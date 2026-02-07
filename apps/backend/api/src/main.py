import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.jwt_middleware import JWTMiddleware
from src.chat.router import router as chat_router
from src.chat.sessions import router as sessions_router
from src.citations.router import router as citations_router
from src.upload.admin_uploads import router as admin_upload_router
from src.upload.user_uploads import router as user_upload_router
from src.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - initialize database tables
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown

app = FastAPI(
    title="GeneralRAG API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTMiddleware)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(citations_router, prefix="/api/citations", tags=["citations"])
app.include_router(admin_upload_router, prefix="/api/admin/upload", tags=["admin"])
app.include_router(user_upload_router, prefix="/api/upload", tags=["upload"])

@app.get("/health")
async def health():
    return {"status": "healthy"}
