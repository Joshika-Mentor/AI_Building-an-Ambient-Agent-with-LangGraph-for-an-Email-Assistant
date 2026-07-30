#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# ThreatLens AI — Azure Container Apps Deployment Script
#
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Docker installed locally
#   - An Azure subscription
#
# Usage:
#   chmod +x deploy/azure/deploy.sh
#   ./deploy/azure/deploy.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-threatlens-rg}"
LOCATION="${AZURE_LOCATION:-centralindia}"
ACR_NAME="${AZURE_ACR_NAME:-threatlensacr}"
ENVIRONMENT_NAME="threatlens-env"
PROJECT_NAME="threatlens"

echo "════════════════════════════════════════════════════════════"
echo "  ThreatLens AI — Azure Container Apps Deployment"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location:       ${LOCATION}"
echo "  Registry:       ${ACR_NAME}"
echo "════════════════════════════════════════════════════════════"

# ─── Step 1: Create Resource Group ───────────────────────────────
echo ""
echo "📁 Step 1: Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
echo "  ✅ Resource group: $RESOURCE_GROUP"

# ─── Step 2: Create Azure Container Registry ────────────────────
echo ""
echo "📦 Step 2: Creating container registry..."
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none
echo "  ✅ Registry: ${ACR_NAME}.azurecr.io"

# ─── Step 3: Login to ACR ────────────────────────────────────────
echo ""
echo "🔐 Step 3: Logging into ACR..."
az acr login --name "$ACR_NAME"

# ─── Step 4: Build & Push Images ─────────────────────────────────
echo ""
echo "🐳 Step 4: Building and pushing Docker images..."

ACR_URL="${ACR_NAME}.azurecr.io"

# Backend
echo "  Building backend..."
docker build -t "${ACR_URL}/${PROJECT_NAME}-backend:latest" ./backend
docker push "${ACR_URL}/${PROJECT_NAME}-backend:latest"
echo "  ✅ Backend pushed"

# Frontend
echo "  Building frontend..."
docker build \
    --build-arg NEXT_PUBLIC_API_URL="https://your-domain.com" \
    -t "${ACR_URL}/${PROJECT_NAME}-frontend:latest" ./frontend
docker push "${ACR_URL}/${PROJECT_NAME}-frontend:latest"
echo "  ✅ Frontend pushed"

# Nginx
echo "  Building nginx..."
docker build -t "${ACR_URL}/${PROJECT_NAME}-nginx:latest" ./nginx
docker push "${ACR_URL}/${PROJECT_NAME}-nginx:latest"
echo "  ✅ Nginx pushed"

# ─── Step 5: Create Container Apps Environment ──────────────────
echo ""
echo "🌐 Step 5: Creating Container Apps environment..."
az containerapp env create \
    --name "$ENVIRONMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none 2>/dev/null || echo "  Environment already exists"
echo "  ✅ Environment: $ENVIRONMENT_NAME"

# ─── Step 6: Deploy Backend ─────────────────────────────────────
echo ""
echo "🚀 Step 6: Deploying backend..."

ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" --output tsv)

az containerapp create \
    --name "${PROJECT_NAME}-backend" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENVIRONMENT_NAME" \
    --image "${ACR_URL}/${PROJECT_NAME}-backend:latest" \
    --registry-server "$ACR_URL" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8000 \
    --ingress internal \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --env-vars \
        "DEBUG=false" \
        "SECRET_KEY=CHANGE_ME_generate_a_secret" \
        "DATABASE_URL=postgresql+asyncpg://threatlens:CHANGE_ME@postgres:5432/threatlens_db" \
        "MONGODB_URL=mongodb://mongodb:27017" \
        "REDIS_URL=redis://redis:6379/0" \
    --output none
echo "  ✅ Backend deployed"

# ─── Step 7: Deploy Frontend ────────────────────────────────────
echo ""
echo "🚀 Step 7: Deploying frontend..."
az containerapp create \
    --name "${PROJECT_NAME}-frontend" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENVIRONMENT_NAME" \
    --image "${ACR_URL}/${PROJECT_NAME}-frontend:latest" \
    --registry-server "$ACR_URL" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 3000 \
    --ingress external \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --output none
echo "  ✅ Frontend deployed"

# ─── Get URLs ────────────────────────────────────────────────────
echo ""
FRONTEND_URL=$(az containerapp show \
    --name "${PROJECT_NAME}-frontend" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo "════════════════════════════════════════════════════════════"
echo "  ✅ Deployment complete!"
echo ""
echo "  🌐 Frontend URL: https://${FRONTEND_URL}"
echo ""
echo "  Next steps:"
echo "  1. Set up Azure Database for PostgreSQL (managed)"
echo "  2. Set up Azure Cosmos DB for MongoDB API (managed)"
echo "  3. Set up Azure Cache for Redis (managed)"
echo "  4. Update backend env vars with managed DB connection strings"
echo "  5. Add custom domain + SSL in Container Apps settings"
echo ""
echo "  See deploy/README.md for detailed instructions."
echo "════════════════════════════════════════════════════════════"
