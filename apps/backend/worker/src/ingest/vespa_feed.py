"""
Vespa Feed Module

Feeds processed documents to Vespa for indexing.
"""
import os
from typing import List, Dict, Any
import httpx
from dataclasses import asdict

from src.ingest.chunking import Chunk

class VespaFeeder:
    """Feeds documents to Vespa."""
    
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.getenv("VESPA_ENDPOINT")
        self.document_api = f"{self.endpoint}/document/v1"
    
    async def feed_chunks(
        self,
        chunks: List[Chunk],
        access_scope: str,
        owner_user_id: str = None,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Feed chunks to Vespa.
        
        Args:
            chunks: List of Chunk objects
            access_scope: 'global' or 'private'
            owner_user_id: User ID for private docs
            batch_size: Number of docs per batch
            
        Returns:
            Stats dict with success/failure counts
        """
        stats = {"success": 0, "failed": 0}
        
        async with httpx.AsyncClient(timeout=30) as client:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                for chunk in batch:
                    doc = self._chunk_to_vespa_doc(chunk, access_scope, owner_user_id)
                    
                    try:
                        response = await client.post(
                            f"{self.document_api}/sop_elements/docid/{chunk.chunk_id}",
                            json=doc
                        )
                        
                        if response.status_code in (200, 201):
                            stats["success"] += 1
                        else:
                            stats["failed"] += 1
                    except Exception as e:
                        stats["failed"] += 1
        
        return stats
    
    def _chunk_to_vespa_doc(
        self,
        chunk: Chunk,
        access_scope: str,
        owner_user_id: str = None
    ) -> Dict[str, Any]:
        """Convert Chunk to Vespa document format."""
        doc = {
            "fields": {
                "doc_id": chunk.doc_id,
                "element_id": chunk.element_id,
                "element_type": chunk.element_type,
                "content_text": chunk.content_text,
                "parent_context": chunk.parent_context,
                "page_number": chunk.page_number,
                "bbox": chunk.bbox,
                "access_scope": access_scope,
                "owner_user_id": owner_user_id or "",
                "created_at": int(os.time() * 1000) if hasattr(os, 'time') else 0
            }
        }
        
        # Add optional fields from metadata
        if chunk.metadata.get("html"):
            doc["fields"]["table_html"] = chunk.metadata["html"]
        if chunk.metadata.get("figure_caption"):
            doc["fields"]["figure_caption"] = chunk.metadata["figure_caption"]
        if chunk.metadata.get("crop_uri"):
            doc["fields"]["crop_uri"] = chunk.metadata["crop_uri"]
        if chunk.metadata.get("embedding"):
            doc["fields"]["embedding"] = {"values": chunk.metadata["embedding"].tolist()}
        if chunk.metadata.get("colbert_tokens"):
            doc["fields"]["colbert_tokens"] = self._format_colbert(chunk.metadata["colbert_tokens"])
        
        return doc
    
    def _format_colbert(self, tokens: Any) -> Dict:
        """Format ColBERT tokens for Vespa tensor format."""
        # Convert to Vespa mapped tensor format
        cells = []
        for i, token_vec in enumerate(tokens):
            for j, val in enumerate(token_vec):
                cells.append({
                    "address": {"token": str(i), "x": str(j)},
                    "value": float(val)
                })
        return {"cells": cells}
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from Vespa."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(
                f"{self.document_api}/sop_elements/docid/{doc_id}"
            )
            return response.status_code == 200
    
    async def delete_by_owner(self, owner_user_id: str) -> int:
        """Delete all documents owned by a user."""
        # Use Vespa's visit API with selection
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.delete(
                f"{self.document_api}/sop_elements/docid/",
                params={
                    "selection": f"sop_elements.owner_user_id == '{owner_user_id}'",
                    "cluster": "sop_content"
                }
            )
            return response.json().get("documentCount", 0)
