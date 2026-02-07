import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, desc

from src.auth.jwt_middleware import get_current_user_optional
from src.db import get_db, ChatSession, ChatMessage

router = APIRouter()


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionOut(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[list] = None
    created_at: str


@router.post("/", response_model=SessionOut)
async def create_session(
    body: SessionCreate = SessionCreate(),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=current_user["user_id"] if current_user else None,
        tenant_id=current_user.get("tenant_id", "default") if current_user else "default",
        title=body.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionOut(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get("/", response_model=List[SessionOut])
async def list_sessions(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    user_id = current_user["user_id"] if current_user else None
    q = select(ChatSession).order_by(desc(ChatSession.updated_at))
    if user_id:
        q = q.where(ChatSession.user_id == user_id)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        SessionOut(
            id=s.id, title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in rows
    ]


@router.get("/{session_id}/messages", response_model=List[MessageOut])
async def get_messages(session_id: str, db=Depends(get_db)):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    rows = result.scalars().all()
    return [
        MessageOut(
            id=m.id, role=m.role, content=m.content,
            citations=m.citations,
            created_at=m.created_at.isoformat(),
        )
        for m in rows
    ]
