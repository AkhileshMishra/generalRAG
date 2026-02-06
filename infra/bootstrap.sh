#!/bin/bash
set -euo pipefail

# Bootstrap script: creates GCS buckets for Terraform remote state
# Run this ONCE before first terraform init

PROJECT_ID="${1:?Usage: ./bootstrap.sh <project-id>}"

for ENV in dev prod; do
  BUCKET="generalrag-terraform-state-${ENV}"
  echo "Creating state bucket: ${BUCKET}"
  gcloud storage buckets create "gs://${BUCKET}" \
    --project="${PROJECT_ID}" \
    --location=us-central1 \
    --uniform-bucket-level-access \
    2>/dev/null || echo "  Bucket ${BUCKET} already exists"

  gcloud storage buckets update "gs://${BUCKET}" \
    --versioning \
    --project="${PROJECT_ID}"
done

echo "Done. You can now run: cd infra/terraform/envs/dev && terraform init"
