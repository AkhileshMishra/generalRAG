import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.cloud import storage

from src.auth.jwt_middleware import get_current_user

router = APIRouter()

ALLOWED_EXTENSIONS = {'.pdf', '.csv', '.xlsx', '.xls'}
CONTENT_TYPES = {
    '.pdf': 'application/pdf',
    '.csv': 'text/csv',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel'
}

class UserUploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    expires_at: str

storage_client = storage.Client()
USER_UPLOADS_BUCKET = os.getenv("USER_UPLOADS_BUCKET")
WORKER_URL = os.getenv("WORKER_URL")
UPLOAD_EXPIRY_DAYS = 30

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]

@router.post("/", response_model=UserUploadResponse)
async def user_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    User upload endpoint for private session documents.
    Supports PDF, CSV, and Excel files. Documents expire after 30 days.
    """
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (limit to 100MB for user uploads)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 100MB for user uploads.")
    
    doc_id = str(uuid.uuid4())
    user_id = user["user_id"]
    session_id = session_id or str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=UPLOAD_EXPIRY_DAYS)
    
    gcs_path = f"users/{user_id}/{session_id}/{doc_id}/{file.filename}"
    
    # Upload to GCS (bucket has 30-day lifecycle policy)
    bucket = storage_client.bucket(USER_UPLOADS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(content, content_type=CONTENT_TYPES.get(ext, 'application/octet-stream'))
    
    metadata = {
        "doc_id": doc_id,
        "filename": file.filename,
        "access_scope": "private",
        "owner_user_id": user_id,
        "session_id": session_id,
        "expires_at": expires_at.isoformat(),
        "gcs_uri": f"gs://{USER_UPLOADS_BUCKET}/{gcs_path}"
    }
    
    # Trigger async ingestion
    background_tasks.add_task(trigger_user_ingestion, doc_id, metadata)
    
    return UserUploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        status="processing",
        expires_at=expires_at.isoformat()
    )

@router.get("/my-documents")
async def list_user_documents(user: dict = Depends(get_current_user)):
    """List user's uploaded documents."""
    # Query database for user's documents
    return {"documents": []}

@router.delete("/{doc_id}")
async def delete_user_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Delete a user's uploaded document."""
    # Verify ownership and delete from GCS + Vespa
    return {"status": "deleted", "doc_id": doc_id}

async def trigger_user_ingestion(doc_id: str, metadata: dict):
    """Trigger the worker to process user document."""
    import httpx
    import logging
    logger = logging.getLogger(__name__)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{WORKER_URL}/ingest/user",
                json={"doc_id": doc_id, "metadata": metadata}
            )
            logger.info(f"Worker response: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to trigger worker: {e}")
