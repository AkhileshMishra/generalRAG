"""
Embeddings Module

Generates dense embeddings using Gemini text-embedding-004 (768 dimensions).
Consistent with Vespa schema and API query embeddings.
"""
import asyncio
from typing import List, Tuple
import numpy as np

from shared.clients.gemini_client import GeminiClient


class EmbeddingGenerator:
    """
    Generates embeddings using Gemini API.
    
    Uses text-embedding-004 which outputs 768-dimensional vectors,
    matching the Vespa schema tensor<float>(x[768]).
    """
    
    EMBEDDING_DIM = 768  # text-embedding-004 output dimension
    
    def __init__(self):
        self.client = GeminiClient()
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text (sync wrapper)."""
        return asyncio.run(self.client.embed_text(text))
    
    async def embed_async(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return await self.client.embed_text(text)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate dense embeddings for texts (sync wrapper)."""
        embeddings = asyncio.run(self.client.batch_embed(texts))
        return np.array(embeddings, dtype=np.float32)
    
    async def embed_texts_async(self, texts: List[str]) -> np.ndarray:
        """Generate dense embeddings for texts."""
        embeddings = await self.client.batch_embed(texts)
        return np.array(embeddings, dtype=np.float32)
    
    def batch_embed(
        self,
        texts: List[str],
        batch_size: int = 100,
        include_colbert: bool = False
    ) -> Tuple[np.ndarray, List]:
        """
        Batch embed texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Texts per API call (Gemini limit ~100)
            include_colbert: Ignored (ColBERT not supported with Gemini)
            
        Returns:
            - dense_embeddings: (N, 768) array
            - colbert_embeddings: Empty list (not supported)
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = asyncio.run(self.client.batch_embed(batch))
            all_embeddings.extend(embeddings)
        
        return np.array(all_embeddings, dtype=np.float32), []
    
    async def batch_embed_async(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> np.ndarray:
        """Async batch embed."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.client.batch_embed(batch)
            all_embeddings.extend(embeddings)
        
        return np.array(all_embeddings, dtype=np.float32)
