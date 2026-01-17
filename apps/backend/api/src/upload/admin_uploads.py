import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.cloud import storage

from src.auth.jwt_middleware import require_admin

router = APIRouter()

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    message: str

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

storage_client = storage.Client()
RAW_PDFS_BUCKET = os.getenv("RAW_PDFS_BUCKET")
WORKER_URL = os.getenv("WORKER_URL")

@router.post("/", response_model=UploadResponse)
async def admin_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    admin: dict = Depends(require_admin)
):
    """
    Admin upload endpoint for global knowledge base documents.
    Triggers async ingestion pipeline.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    doc_id = str(uuid.uuid4())
    gcs_path = f"admin/{doc_id}/{file.filename}"
    
    # Upload to GCS
    bucket = storage_client.bucket(RAW_PDFS_BUCKET)
    blob = bucket.blob(gcs_path)
    
    content = await file.read()
    blob.upload_from_string(content, content_type="application/pdf")
    
    # Store metadata
    metadata = {
        "doc_id": doc_id,
        "filename": file.filename,
        "title": title or file.filename,
        "tags": tags.split(",") if tags else [],
        "description": description,
        "access_scope": "global",
        "uploaded_by": admin["user_id"],
        "gcs_uri": f"gs://{RAW_PDFS_BUCKET}/{gcs_path}"
    }
    
    # Trigger async ingestion
    background_tasks.add_task(trigger_ingestion, doc_id, metadata)
    
    return UploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        status="processing",
        message="Document uploaded. Ingestion started."
    )

@router.get("/status/{doc_id}")
async def get_upload_status(doc_id: str, admin: dict = Depends(require_admin)):
    """Check ingestion status for a document."""
    # Query database for status
    # For now, return placeholder
    return {"doc_id": doc_id, "status": "processing", "progress": 50}

async def trigger_ingestion(doc_id: str, metadata: dict):
    """Trigger the worker to process the document."""
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"{WORKER_URL}/ingest/admin",
            json={"doc_id": doc_id, "metadata": metadata}
        )
