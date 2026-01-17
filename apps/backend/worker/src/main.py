from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

from src.pipelines.admin_ingest import AdminIngestionPipeline
from src.pipelines.user_ingest import UserIngestionPipeline

app = FastAPI(title="GeneralRAG Worker")

admin_pipeline = AdminIngestionPipeline()
user_pipeline = UserIngestionPipeline()

class IngestRequest(BaseModel):
    doc_id: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ingest/admin")
async def ingest_admin(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger admin document ingestion."""
    background_tasks.add_task(
        admin_pipeline.ingest,
        request.doc_id,
        request.metadata
    )
    return {"status": "started", "doc_id": request.doc_id}

@app.post("/ingest/user")
async def ingest_user(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger user document ingestion."""
    background_tasks.add_task(
        user_pipeline.ingest,
        request.doc_id,
        request.metadata
    )
    return {"status": "started", "doc_id": request.doc_id}

@app.post("/ingest/admin/sync")
async def ingest_admin_sync(request: IngestRequest):
    """Synchronous admin ingestion (for testing)."""
    result = await admin_pipeline.ingest(request.doc_id, request.metadata)
    return result

@app.post("/ingest/user/sync")
async def ingest_user_sync(request: IngestRequest):
    """Synchronous user ingestion (for testing)."""
    result = await user_pipeline.ingest(request.doc_id, request.metadata)
    return result
