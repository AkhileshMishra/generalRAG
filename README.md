# GeneralRAG - Production RAG System for Large Document Processing

A production-ready Retrieval-Augmented Generation system optimized for large (1-2GB) mixed scanned/digital PDFs with multimodal support.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Admin Portal  │     │   User Chatbot  │     │   User Uploads  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Cloud Run API                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   Auth   │  │   Chat   │  │ Retrieval│  │  Upload Handler  │ │
│  │  (OIDC)  │  │ Endpoint │  │  Engine  │  │ (Admin/Private)  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Cloud Tasks    │     │     Vespa       │     │      GCS        │
│  (Ingestion)    │     │  (Hybrid Search)│     │  (Raw + Crops)  │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │                       ▲
         ▼                       │
┌─────────────────────────────────────────────────────────────────┐
│                      Ingestion Worker                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ PDF Split│  │Unstructured│ │  Gemini  │  │  Vespa Feeder   │ │
│  │ (Batches)│  │  (Layout) │  │ (Vision) │  │  (Index)        │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Large PDF Support**: Splits 1-2GB PDFs into batches for reliable processing
- **Mixed Document Handling**: Routes scanned vs digital pages automatically
- **Multimodal RAG**: Tables→HTML, Figures→Dense captions via Gemini Vision
- **Hybrid Retrieval**: BM25 + Dense + ColBERT reranking in Vespa
- **Parent-Child Chunking**: Preserves section context for accurate answers
- **Access Control**: Global (admin) + Private (per-user) document scopes
- **Precise Citations**: Page + bounding box level references

## Quick Start

```bash
# 0. Bootstrap Terraform state buckets (one-time)
./infra/bootstrap.sh YOUR_PROJECT_ID

# 1. Setup infrastructure
cd infra/terraform/envs/dev
terraform init && terraform apply -var="project_id=YOUR_PROJECT" -var="db_password=YOUR_PASSWORD"

# 2. Deploy Vespa schema
cd ../../../../vespa/app
vespa deploy --target <vespa-endpoint>

# 3. Deploy backend
cd ../../apps/backend
gcloud run deploy api --source api/
gcloud run deploy worker --source worker/

# 4. Deploy frontend
cd ../frontend/web
npm install && npm run build
gcloud run deploy user-chat --source .
```

## Project Structure

```
repo/
├── infra/terraform/          # GCP infrastructure as code
├── apps/
│   ├── backend/
│   │   ├── api/              # FastAPI service (auth, chat, retrieval)
│   │   ├── worker/           # Ingestion pipeline
│   │   └── shared/           # Common schemas and clients
│   └── frontend/
│       └── web/              # Next.js app (user chat + admin)
└── vespa/app/                # Vespa application package
```

## Requirements

- GCP Project with Cloud Run, GCS, Cloud SQL, Secret Manager
- Vespa instance (single VM or Vespa Cloud)
- Gemini API access
- Python 3.11+, Node.js 20+

## Configuration

Set these secrets in Secret Manager:
- `gemini-api-key`
- `vespa-endpoint`
- `db-connection-string`
- `jwt-secret`

## License

MIT
