# GeneralRAG Monorepo

## Quick Verification

```bash
# Check structure
find . -type f -name "*.py" | head -20
find . -type f -name "*.tf" | head -20
find . -type f -name "*.tsx" | head -10
```

## Deploy Commands

### Infrastructure
```bash
cd infra/terraform/envs/dev
terraform init
terraform plan -var="project_id=YOUR_PROJECT" -var="db_password=YOUR_PASSWORD"
terraform apply
```

### Vespa
```bash
cd vespa/app
# Deploy to Vespa Cloud or self-hosted
vespa deploy --target http://VESPA_IP:19071
```

### Backend
```bash
# Build and push images
cd apps/backend/api
docker build -t gcr.io/PROJECT/generalrag-api .
docker push gcr.io/PROJECT/generalrag-api

cd ../worker
docker build -t gcr.io/PROJECT/generalrag-worker .
docker push gcr.io/PROJECT/generalrag-worker
```

### Frontend
```bash
cd apps/frontend/user_chat
npm install && npm run build

cd ../admin_portal
npm install && npm run build
```
