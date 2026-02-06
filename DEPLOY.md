# GeneralRAG Deployment Guide

## Prerequisites

```bash
# Bootstrap Terraform state buckets (one-time)
./infra/bootstrap.sh YOUR_PROJECT_ID
```

## Infrastructure

```bash
cd infra/terraform/envs/dev
terraform init
terraform plan -var="project_id=YOUR_PROJECT" -var="db_password=YOUR_PASSWORD"
terraform apply -var="project_id=YOUR_PROJECT" -var="db_password=YOUR_PASSWORD"
```

## Vespa

```bash
cd vespa/app
vespa deploy --target http://VESPA_IP:19071
```

## Backend

```bash
cd apps/backend

# API
docker build -f api/Dockerfile -t gcr.io/PROJECT/generalrag-api .
docker push gcr.io/PROJECT/generalrag-api

# Worker
docker build -f worker/Dockerfile -t gcr.io/PROJECT/generalrag-worker .
docker push gcr.io/PROJECT/generalrag-worker
```

## Frontend

```bash
cd apps/frontend/web
npm install && npm run build
```
