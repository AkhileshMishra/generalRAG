"""
Vespa Client

Client for Vespa search and document operations.
"""
import os
from typing import List, Dict, Any, Optional
import httpx

class VespaClient:
    """Async client for Vespa operations."""
    
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.getenv("VESPA_ENDPOINT", "http://localhost:8080")
        self.search_url = f"{self.endpoint}/search/"
        self.document_url = f"{self.endpoint}/document/v1"
    
    async def query(
        self,
        yql: str,
        ranking_features: Dict[str, Any] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Execute Vespa query.
        
        Args:
            yql: YQL query string
            ranking_features: Query parameters including ranking profile
            timeout: Request timeout in seconds
            
        Returns:
            List of hit documents
        """
        params = {
            "yql": yql,
            "format": "json",
            **(ranking_features or {})
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(self.search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            hits = data.get("root", {}).get("children", [])
            
            return [hit.get("fields", {}) for hit in hits]
    
    async def query_with_embedding(
        self,
        yql: str,
        query_embedding: List[float],
        ranking_profile: str = "hybrid",
        hits: int = 20
    ) -> List[Dict[str, Any]]:
        """Query with dense embedding."""
        params = {
            "yql": yql,
            "ranking.profile": ranking_profile,
            "hits": hits,
            "input.query(query_embedding)": str(query_embedding)
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(self.search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return [hit.get("fields", {}) for hit in data.get("root", {}).get("children", [])]
    
    async def feed_document(
        self,
        schema: str,
        doc_id: str,
        fields: Dict[str, Any]
    ) -> bool:
        """Feed a single document."""
        url = f"{self.document_url}/{schema}/docid/{doc_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json={"fields": fields})
            return response.status_code in (200, 201)
    
    async def get_document(
        self,
        schema: str,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        url = f"{self.document_url}/{schema}/docid/{doc_id}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json().get("fields")
            return None
    
    async def delete_document(
        self,
        schema: str,
        doc_id: str
    ) -> bool:
        """Delete a document."""
        url = f"{self.document_url}/{schema}/docid/{doc_id}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(url)
            return response.status_code == 200
    
    async def batch_feed(
        self,
        schema: str,
        documents: List[Dict[str, Any]],
        id_field: str = "element_id"
    ) -> Dict[str, int]:
        """Batch feed documents."""
        stats = {"success": 0, "failed": 0}
        
        async with httpx.AsyncClient(timeout=60) as client:
            for doc in documents:
                doc_id = doc.get(id_field)
                url = f"{self.document_url}/{schema}/docid/{doc_id}"
                
                try:
                    response = await client.post(url, json={"fields": doc})
                    if response.status_code in (200, 201):
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                except Exception:
                    stats["failed"] += 1
        
        return stats
