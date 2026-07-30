# ThreatLens AI — Deployment Guide

Complete guide to deploy ThreatLens AI anywhere using Docker containers.

---

## Table of Contents

1. [Local Docker Testing](#1-local-docker-testing)
2. [Deploy to AWS (ECS Fargate)](#2-deploy-to-aws-ecs-fargate)
3. [Deploy to Azure (Container Apps)](#3-deploy-to-azure-container-apps)
4. [Environment Variables](#4-environment-variables)
5. [SSL / HTTPS Setup](#5-ssl--https-setup)
6. [Monitoring & Logs](#6-monitoring--logs)

---

## 1. Local Docker Testing

Test the full production stack locally before deploying to the cloud.

### Prerequisites
- Docker Desktop installed
- At least 4GB RAM allocated to Docker

### Steps

```bash
# 1. Configure production environment
cp .env.production .env.production.local

# 2. Edit secrets (change CHANGE_ME values)
#    - SECRET_KEY: run `python -c "import secrets; print(secrets.token_urlsafe(64))"`
#    - POSTGRES_PASSWORD: use a strong password
#    - CORS_ORIGINS: set to http://localhost for local testing
#    - NEXT_PUBLIC_API_URL: set to http://localhost for local testing

# 3. Build all images
docker compose -f docker-compose.prod.yml build

# 4. Start the stack
docker compose -f docker-compose.prod.yml --env-file .env.production.local up -d

# 5. Check all services are healthy
docker compose -f docker-compose.prod.yml ps

# 6. Test
#    Frontend:  http://localhost
#    API Docs:  http://localhost/docs
#    Health:    http://localhost/health
```

### Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Restart a single service
docker compose -f docker-compose.prod.yml restart backend

# Stop everything
docker compose -f docker-compose.prod.yml down

# Stop and remove all data (⚠️ destructive)
docker compose -f docker-compose.prod.yml down -v
```

---

## 2. Deploy to AWS (ECS Fargate)

### Prerequisites
- AWS CLI v2: `aws --version`
- AWS account with admin access
- Docker installed locally

### Quick Start

```bash
# 1. Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Key, Region (ap-south-1), Output (json)

# 2. Run deployment script
chmod +x deploy/aws/deploy.sh
./deploy/aws/deploy.sh
```

### What the Script Does
1. Creates ECR repositories for backend, frontend, and nginx
2. Builds Docker images locally
3. Pushes images to ECR
4. Creates an ECS cluster

### Manual Steps After Script

#### Create Application Load Balancer (ALB)
1. Go to **EC2 → Load Balancers → Create**
2. Choose **Application Load Balancer**
3. Select your VPC and at least 2 public subnets
4. Create a target group pointing to port 80
5. Add HTTPS listener on port 443 (requires ACM certificate)

#### Create ECS Task Definition
1. Go to **ECS → Task Definitions → Create**
2. Choose **Fargate** launch type
3. Add containers for backend (port 8000), frontend (port 3000), nginx (port 80)
4. Set environment variables from `.env.production`
5. Allocate: 2 vCPU, 4GB memory

#### Create ECS Service
1. Go to **ECS → Clusters → your-cluster → Create Service**
2. Select the task definition
3. Set desired count to 2 (for high availability)
4. Attach the ALB target group

#### DNS & SSL
1. **Route53**: Create an A record pointing to the ALB
2. **ACM**: Request a certificate for your domain
3. Add the certificate to the ALB HTTPS listener

### Estimated Cost
| Service | Monthly Cost (approx) |
|---|---|
| ECS Fargate (2 tasks) | $60–80 |
| ALB | $20 |
| RDS PostgreSQL (db.t3.micro) | $15 |
| ElastiCache Redis | $13 |
| **Total** | **~$110–130/month** |

---

## 3. Deploy to Azure (Container Apps)

### Prerequisites
- Azure CLI: `az --version`
- Azure subscription
- Docker installed locally

### Quick Start

```bash
# 1. Login to Azure
az login

# 2. Run deployment script
chmod +x deploy/azure/deploy.sh
./deploy/azure/deploy.sh
```

### What the Script Does
1. Creates a Resource Group
2. Creates Azure Container Registry (ACR)
3. Builds and pushes Docker images
4. Creates Container Apps Environment
5. Deploys backend (internal) and frontend (external)

### Manual Steps After Script

#### Set Up Managed Databases
For production, use Azure managed services instead of containers:

```bash
# PostgreSQL
az postgres flexible-server create \
    --resource-group threatlens-rg \
    --name threatlens-pg \
    --location centralindia \
    --sku-name Standard_B1ms \
    --storage-size 32 \
    --admin-user threatlens \
    --admin-password 'YourStrongPassword!'

# Redis
az redis create \
    --resource-group threatlens-rg \
    --name threatlens-redis \
    --location centralindia \
    --sku Basic \
    --vm-size c0
```

#### Custom Domain
1. Go to **Container Apps → your-frontend → Custom Domains**
2. Add your domain and validate ownership via DNS
3. Azure provides free managed SSL certificates

### Estimated Cost
| Service | Monthly Cost (approx) |
|---|---|
| Container Apps (2 apps) | $30–50 |
| PostgreSQL Flexible (B1ms) | $13 |
| Azure Cache for Redis (C0) | $16 |
| Container Registry (Basic) | $5 |
| **Total** | **~$65–85/month** |

---

## 4. Environment Variables

All services are configured via environment variables. Key ones to set:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing key (64+ char random string) |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `DATABASE_URL` | ✅ | Full PostgreSQL connection string |
| `CORS_ORIGINS` | ✅ | Allowed origins (your domain) |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL (used at frontend build time) |
| `VIRUSTOTAL_API_KEY` | ❌ | For VirusTotal integration |

### Generate a Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 5. SSL / HTTPS Setup

### Option A: Cloud-Managed SSL (Recommended)
- **AWS**: Use ACM (AWS Certificate Manager) — free certificates
- **Azure**: Container Apps provides free managed certificates

### Option B: Self-Managed with Let's Encrypt

```bash
# 1. Install certbot
apt install certbot

# 2. Generate certificates
certbot certonly --standalone -d your-domain.com

# 3. Copy certs to nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 4. Uncomment HTTPS block in nginx/nginx.conf

# 5. Rebuild nginx
docker compose -f docker-compose.prod.yml build nginx
docker compose -f docker-compose.prod.yml up -d nginx
```

---

## 6. Monitoring & Logs

### Docker Compose (Local / VPS)

```bash
# All logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Resource usage
docker stats
```

### AWS
- **CloudWatch Logs**: Logs auto-ship to `/ecs/threatlens`
- **CloudWatch Metrics**: CPU, memory, request count via ALB

### Azure
- **Log Analytics**: Built into Container Apps
- **Application Insights**: Add for detailed tracing

---

## Architecture (Production)

```
Internet
   │
   ▼
┌─────────┐
│  Nginx  │  ← Port 80/443 (reverse proxy)
│  :80    │
└────┬────┘
     │
     ├── /api/*  ──→  Backend (FastAPI :8000)
     │                    ├── PostgreSQL
     │                    ├── MongoDB
     │                    └── Redis
     │
     └── /*      ──→  Frontend (Next.js :3000)
```
