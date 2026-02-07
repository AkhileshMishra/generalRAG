"""
Gemini Client

Client for Gemini API for generation and vision tasks.
"""
import os
import base64
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx

class GeminiClient:
    """Async client for Gemini API."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    async def generate_with_context(
        self,
        query: str,
        context: str,
        image_crops: List[Dict] = None,
        model: str = "gemini-2.0-flash"
    ) -> str:
        """
        Generate answer with RAG context and optional images.
        
        Args:
            query: User question
            context: Retrieved context text
            image_crops: List of {uri, base64, type} for multimodal
            model: Gemini model to use
            
        Returns:
            Generated answer
        """
        system_prompt = """You are a helpful assistant answering questions about documents.

Use the provided context to answer questions accurately. When referencing information:
- Cite sources using [N] notation matching the context references
- For tables, verify data against both the HTML and image if provided
- For figures/diagrams, describe what you see and reference the caption
- If information is not in the context, say so clearly

Be precise and factual."""

        # Build content parts
        parts = [
            {"text": f"{system_prompt}\n\n## Context:\n{context}\n\n## Question:\n{query}"}
        ]
        
        # Add images if provided
        if image_crops:
            for crop in image_crops[:10]:  # Limit to 10 images
                if crop.get("base64"):
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": crop["base64"]
                        }
                    })
        
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
                "topP": 0.8
            }
        }
        
        url = f"{self.BASE_URL}/{model}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    async def generate_stream(
        self,
        query: str,
        context: str,
        image_crops: List[Dict] = None,
        model: str = "gemini-2.0-flash"
    ) -> AsyncGenerator[str, None]:
        """Stream generation for real-time responses."""
        system_prompt = """You are a helpful assistant. Use the context to answer accurately. Cite sources with [N]."""
        
        parts = [{"text": f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}"}]
        
        if image_crops:
            for crop in image_crops[:5]:
                if crop.get("base64"):
                    parts.append({
                        "inline_data": {"mime_type": "image/png", "data": crop["base64"]}
                    })
        
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}
        }
        
        url = f"{self.BASE_URL}/{model}:streamGenerateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        if "candidates" in data:
                            text = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if text:
                                yield text
    
    EMBEDDING_DIM = 768

    async def embed_text(self, text: str, model: str = "gemini-embedding-001") -> List[float]:
        """Generate embedding for text."""
        url = f"{self.BASE_URL}/{model}:embedContent?key={self.api_key}"
        
        payload = {
            "model": f"models/{model}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.EMBEDDING_DIM
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["embedding"]["values"]
    
    async def batch_embed(
        self,
        texts: List[str],
        model: str = "gemini-embedding-001"
    ) -> List[List[float]]:
        """Batch embed multiple texts."""
        url = f"{self.BASE_URL}/{model}:batchEmbedContents?key={self.api_key}"
        
        requests = [
            {"model": f"models/{model}", "content": {"parts": [{"text": t}]}, "outputDimensionality": self.EMBEDDING_DIM}
            for t in texts
        ]
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json={"requests": requests})
            response.raise_for_status()
            
            data = response.json()
            return [e["values"] for e in data["embeddings"]]
