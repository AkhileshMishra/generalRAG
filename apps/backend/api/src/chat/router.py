import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.auth.jwt_middleware import get_current_user, get_current_user_optional
from src.retrieval.vespa_query_builder import VespaQueryBuilder
from src.retrieval.context_packer import ContextPacker
from src.db import get_db, ChatSession, ChatMessage
from shared.clients.vespa_client import VespaClient
from shared.clients.gemini_client import GeminiClient

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_private: bool = True


class Citation(BaseModel):
    doc_id: str
    element_id: str
    page_number: int
    bbox: List[float]
    snippet: str
    crop_uri: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: str


vespa_client = VespaClient(os.getenv("VESPA_ENDPOINT"))
gemini_client = GeminiClient(os.getenv("GEMINI_API_KEY"))
query_builder = VespaQueryBuilder()
context_packer = ContextPacker()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    user_id = current_user["user_id"] if current_user else None
    tenant_id = current_user.get("tenant_id") if current_user else None

    # Ensure session exists
    session_id = request.session_id or str(uuid.uuid4())
    
    # Generate query embedding for vector search
    query_embedding = await gemini_client.embed_text(request.message)
    
    # Build Vespa query with access control
    yql, ranking_features = query_builder.build_rag_query(
        query_text=request.message,
        tenant_id=tenant_id,
        user_id=user_id if request.include_private else None,
        include_global=True
    )
    
    # Add query embedding to ranking features
    ranking_features["input.query(query_embedding)"] = query_embedding
    
    # Execute retrieval
    results = await vespa_client.query(yql, ranking_features)
    
    # Pack context for LLM
    context, image_crops = context_packer.pack(results)
    
    # Generate answer with Gemini
    answer = await gemini_client.generate_with_context(
        query=request.message,
        context=context,
        image_crops=image_crops
    )
    
    # Build citations
    citations = [
        Citation(
            doc_id=r["doc_id"],
            element_id=r["element_id"],
            page_number=r["page_number"],
            bbox=r["bbox"],
            snippet=r["content_text"][:200],
            crop_uri=r.get("crop_uri")
        )
        for r in results[:5]
    ]

    # Persist messages
    try:
        db.add(ChatMessage(id=str(uuid.uuid4()), session_id=session_id, role="user", content=request.message))
        db.add(ChatMessage(id=str(uuid.uuid4()), session_id=session_id, role="assistant", content=answer, citations=[c.dict() for c in citations]))
        await db.commit()
    except Exception:
        await db.rollback()

    return ChatResponse(
        answer=answer,
        citations=citations,
        session_id=session_id
    )


@router.post("/stream")
async def chat_stream(
    req: Request,
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Streaming chat endpoint with SSE for real-time responses."""
    from src.streaming.sse import stream_response
    
    user_id = current_user["user_id"] if current_user else None
    tenant_id = current_user.get("tenant_id") if current_user else None
    
    # Generate query embedding for vector search
    query_embedding = await gemini_client.embed_text(request.message)
    
    yql, ranking_features = query_builder.build_rag_query(
        query_text=request.message,
        tenant_id=tenant_id,
        user_id=user_id if request.include_private else None,
        include_global=True
    )
    
    # Add query embedding to ranking features
    ranking_features["input.query(query_embedding)"] = query_embedding
    
    results = await vespa_client.query(yql, ranking_features)
    context, image_crops = context_packer.pack(results)
    
    citations = [
        {"doc_id": r["doc_id"], "page": r["page_number"], "text": r["content_text"][:200]}
        for r in results[:5]
    ]
    
    async def generate():
        async for chunk in gemini_client.generate_stream(
            query=request.message,
            context=context,
            image_crops=image_crops
        ):
            if await req.is_disconnected():
                break
            yield chunk
    
    return await stream_response(generate(), citations)
