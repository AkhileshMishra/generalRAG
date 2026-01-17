"""
Server-Sent Events (SSE) Streaming Module

Provides streaming responses for long-running chat queries.
Streams tokens as they're generated, with citation events.
"""
import json
import asyncio
from typing import AsyncGenerator, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import Request
from fastapi.responses import StreamingResponse


class SSEEventType(str, Enum):
    TOKEN = "token"
    CITATION = "citation"
    DONE = "done"
    ERROR = "error"


@dataclass
class SSEEvent:
    event: SSEEventType
    data: dict

    def encode(self) -> str:
        return f"event: {self.event.value}\ndata: {json.dumps(self.data)}\n\n"


async def stream_response(
    generator: AsyncGenerator[str, None],
    citations: Optional[list] = None
) -> StreamingResponse:
    """
    Create SSE streaming response from async generator.
    
    Args:
        generator: Async generator yielding text tokens
        citations: Optional list of citations to send at end
    """
    async def event_stream():
        try:
            async for token in generator:
                yield SSEEvent(
                    event=SSEEventType.TOKEN,
                    data={"text": token}
                ).encode()
            
            if citations:
                yield SSEEvent(
                    event=SSEEventType.CITATION,
                    data={"citations": citations}
                ).encode()
            
            yield SSEEvent(
                event=SSEEventType.DONE,
                data={}
            ).encode()
            
        except Exception as e:
            yield SSEEvent(
                event=SSEEventType.ERROR,
                data={"error": str(e)}
            ).encode()
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


class StreamingChat:
    """Handles streaming chat responses with Gemini."""
    
    def __init__(self, gemini_client):
        self.gemini = gemini_client
    
    async def stream_answer(
        self,
        query: str,
        context_chunks: list,
        request: Request
    ) -> StreamingResponse:
        """
        Stream answer generation with client disconnect handling.
        """
        async def generate():
            prompt = self._build_prompt(query, context_chunks)
            
            async for token in self.gemini.stream_generate(prompt):
                if await request.is_disconnected():
                    break
                yield token
        
        citations = [
            {"doc_id": c["doc_id"], "page": c["page"], "text": c["text"][:200]}
            for c in context_chunks
        ]
        
        return await stream_response(generate(), citations)
    
    def _build_prompt(self, query: str, chunks: list) -> str:
        context = "\n\n---\n\n".join(
            f"[Source: {c['doc_id']}, Page {c['page']}]\n{c['text']}"
            for c in chunks
        )
        
        return f"""Answer the question based on the provided context.

Context:
{context}

Question: {query}

Answer:"""
