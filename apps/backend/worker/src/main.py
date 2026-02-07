from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GeneralRAG Worker")

# Lazy load pipelines to avoid import errors blocking startup
admin_pipeline = None
user_pipeline = None

def get_admin_pipeline():
    global admin_pipeline
    if admin_pipeline is None:
        from src.pipelines.admin_ingest import AdminIngestionPipeline
        admin_pipeline = AdminIngestionPipeline()
    return admin_pipeline

def get_user_pipeline():
    global user_pipeline
    if user_pipeline is None:
        from src.pipelines.user_ingest import UserIngestionPipeline
        user_pipeline = UserIngestionPipeline()
    return user_pipeline

class IngestRequest(BaseModel):
    doc_id: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ingest/admin")
async def ingest_admin(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger admin document ingestion."""
    logger.info(f"Received admin ingest request for doc_id={request.doc_id}")
    pipeline = get_admin_pipeline()
    background_tasks.add_task(pipeline.ingest, request.doc_id, request.metadata)
    return {"status": "started", "doc_id": request.doc_id}

@app.post("/ingest/user")
async def ingest_user(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger user document ingestion."""
    logger.info(f"Received user ingest request for doc_id={request.doc_id}")
    pipeline = get_user_pipeline()
    background_tasks.add_task(pipeline.ingest, request.doc_id, request.metadata)
    return {"status": "started", "doc_id": request.doc_id}

@app.post("/ingest/admin/sync")
async def ingest_admin_sync(request: IngestRequest):
    """Synchronous admin ingestion (for testing)."""
    pipeline = get_admin_pipeline()
    result = await pipeline.ingest(request.doc_id, request.metadata)
    return result

@app.post("/ingest/user/sync")
async def ingest_user_sync(request: IngestRequest):
    """Synchronous user ingestion (for testing)."""
    pipeline = get_user_pipeline()
    result = await pipeline.ingest(request.doc_id, request.metadata)
    return result
