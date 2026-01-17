"""
Embeddings Module

Generates dense embeddings using CPU-friendly models.
Supports both dense vectors and ColBERT-style token embeddings.
"""
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Generates embeddings for retrieval."""
    
    def __init__(
        self,
        dense_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        colbert_model: str = "colbert-ir/colbertv2.0"
    ):
        self.dense_model = SentenceTransformer(dense_model)
        self.dense_dim = self.dense_model.get_sentence_embedding_dimension()
        
        # ColBERT model (optional, heavier)
        self._colbert_model = None
        self._colbert_model_name = colbert_model
    
    @property
    def colbert_model(self):
        """Lazy load ColBERT model."""
        if self._colbert_model is None:
            self._colbert_model = SentenceTransformer(self._colbert_model_name)
        return self._colbert_model
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate dense embeddings for texts."""
        return self.dense_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 10
        )
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query."""
        return self.dense_model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    
    def embed_colbert(self, text: str, max_tokens: int = 32) -> np.ndarray:
        """
        Generate ColBERT-style token embeddings.
        
        Returns tensor of shape (num_tokens, embedding_dim)
        """
        # Tokenize and get token embeddings
        encoded = self.colbert_model.tokenize([text])
        
        with self.colbert_model._target_device:
            features = self.colbert_model.forward(encoded)
            token_embeddings = features['token_embeddings'][0].cpu().numpy()
        
        # Truncate/pad to max_tokens
        if len(token_embeddings) > max_tokens:
            token_embeddings = token_embeddings[:max_tokens]
        elif len(token_embeddings) < max_tokens:
            padding = np.zeros((max_tokens - len(token_embeddings), token_embeddings.shape[1]))
            token_embeddings = np.vstack([token_embeddings, padding])
        
        # Normalize
        norms = np.linalg.norm(token_embeddings, axis=1, keepdims=True)
        token_embeddings = token_embeddings / np.maximum(norms, 1e-8)
        
        return token_embeddings
    
    def batch_embed(
        self,
        texts: List[str],
        batch_size: int = 32,
        include_colbert: bool = False
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Batch embed texts with optional ColBERT embeddings.
        
        Returns:
            - dense_embeddings: (N, dense_dim) array
            - colbert_embeddings: List of (tokens, colbert_dim) arrays (if include_colbert)
        """
        # Dense embeddings
        dense_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embed_texts(batch)
            dense_embeddings.append(embeddings)
        
        dense_embeddings = np.vstack(dense_embeddings)
        
        # ColBERT embeddings (optional)
        colbert_embeddings = []
        if include_colbert:
            for text in texts:
                colbert_embeddings.append(self.embed_colbert(text))
        
        return dense_embeddings, colbert_embeddings
