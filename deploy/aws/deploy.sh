#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# ThreatLens AI — AWS ECS Fargate Deployment Script
#
# Prerequisites:
#   - AWS CLI v2 installed and configured (aws configure)
#   - Docker installed locally
#   - An AWS account with appropriate permissions
#
# Usage:
#   chmod +x deploy/aws/deploy.sh
#   ./deploy/aws/deploy.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-ap-south-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="threatlens"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
ECR_BACKEND="${PROJECT_NAME}-backend"
ECR_FRONTEND="${PROJECT_NAME}-frontend"
ECR_NGINX="${PROJECT_NAME}-nginx"

echo "════════════════════════════════════════════════════════════"
echo "  ThreatLens AI — AWS ECS Fargate Deployment"
echo "  Region:  ${AWS_REGION}"
echo "  Account: ${AWS_ACCOUNT_ID}"
echo "════════════════════════════════════════════════════════════"

# ─── Step 1: Create ECR Repositories ─────────────────────────────
echo ""
echo "📦 Step 1: Creating ECR repositories..."

for repo in $ECR_BACKEND $ECR_FRONTEND $ECR_NGINX; do
    aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" 2>/dev/null || \
    aws ecr create-repository \
        --repository-name "$repo" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo "  ✅ $repo"
done

# ─── Step 2: Login to ECR ────────────────────────────────────────
echo ""
echo "🔐 Step 2: Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ─── Step 3: Build & Push Images ─────────────────────────────────
echo ""
echo "🐳 Step 3: Building and pushing Docker images..."

ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Backend
echo "  Building backend..."
docker build -t "${ECR_BASE}/${ECR_BACKEND}:latest" ./backend
docker push "${ECR_BASE}/${ECR_BACKEND}:latest"
echo "  ✅ Backend pushed"

# Frontend
echo "  Building frontend..."
docker build \
    --build-arg NEXT_PUBLIC_API_URL="https://your-domain.com" \
    -t "${ECR_BASE}/${ECR_FRONTEND}:latest" ./frontend
docker push "${ECR_BASE}/${ECR_FRONTEND}:latest"
echo "  ✅ Frontend pushed"

# Nginx
echo "  Building nginx..."
docker build -t "${ECR_BASE}/${ECR_NGINX}:latest" ./nginx
docker push "${ECR_BASE}/${ECR_NGINX}:latest"
echo "  ✅ Nginx pushed"

# ─── Step 4: Create ECS Cluster ──────────────────────────────────
echo ""
echo "🚀 Step 4: Creating ECS cluster..."
aws ecs create-cluster \
    --cluster-name "$CLUSTER_NAME" \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region "$AWS_REGION" 2>/dev/null || echo "  Cluster already exists"
echo "  ✅ Cluster: $CLUSTER_NAME"

# ─── Step 5: Create CloudWatch Log Group ─────────────────────────
echo ""
echo "📊 Step 5: Creating log group..."
aws logs create-log-group \
    --log-group-name "/ecs/${PROJECT_NAME}" \
    --region "$AWS_REGION" 2>/dev/null || echo "  Log group already exists"
echo "  ✅ Log group: /ecs/${PROJECT_NAME}"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅ Images pushed to ECR successfully!"
echo ""
echo "  Next steps (manual — see deploy/README.md):"
echo "  1. Create a VPC with public/private subnets (or use default)"
echo "  2. Create an Application Load Balancer (ALB)"
echo "  3. Create ECS Task Definitions for each service"
echo "  4. Create ECS Services with the ALB"
echo "  5. Set up Route53 + ACM for your domain and HTTPS"
echo ""
echo "  Quick test with docker-compose locally first:"
echo "  docker compose -f docker-compose.prod.yml up -d"
echo "════════════════════════════════════════════════════════════"
