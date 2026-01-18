"""
Centralized Configuration

All tunable parameters for the RAG system.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class IngestionConfig:
    """PDF ingestion settings."""
    # PDF splitting
    batch_size: int = 10
    max_batch_size: int = 20
    min_batch_size: int = 2
    split_concurrency: int = 1  # Reduced for free trial (prevents OOM on 4GB containers)
    
    # Unstructured - use 'fast' for free trial (hi_res requires heavy CPU/GPU)
    unstructured_strategy: str = "fast"
    unstructured_languages: list = field(default_factory=lambda: ["eng"])
    extract_images: bool = True
    infer_table_structure: bool = True
    
    # Retries
    max_retries: int = 3
    retry_min_wait: float = 1.0
    retry_max_wait: float = 30.0
    allow_partial_failure: bool = True
    failure_threshold: float = 0.3  # Max 30% batch failures allowed
    
    # QA gates
    min_text_density: float = 0.0001  # Below = likely scanned
    require_bbox_for_visuals: bool = True
    run_reconciliation: bool = True  # Backstop for missed elements

@dataclass
class GeminiConfig:
    """Gemini API settings."""
    # Models - using Gemini 1.5 Pro (2.5 not yet available)
    vision_model: str = "gemini-1.5-pro"
    generation_model: str = "gemini-1.5-pro"
    embedding_model: str = "text-embedding-004"
    
    # Limits - NEVER upload full PDFs, only page images/crops
    max_image_size_mb: float = 20.0
    max_images_per_request: int = 10
    
    # Generation
    temperature: float = 0.3
    max_output_tokens: int = 8192
    
    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 1000000

@dataclass
class VespaConfig:
    """Vespa retrieval settings."""
    # Hybrid retrieval
    default_hits: int = 20
    target_hits_dense: int = 100
    target_hits_colbert: int = 200
    
    # Reranking
    rerank_count: int = 50
    colbert_rerank_count: int = 100
    
    # Timeouts
    query_timeout_ms: int = 30000
    feed_timeout_ms: int = 10000
    
    # Ranking profiles
    default_profile: str = "rag"
    hybrid_profile: str = "hybrid"

@dataclass
class ChunkingConfig:
    """Chunking settings."""
    child_chunk_size: int = 500
    child_overlap: int = 50
    parent_window_size: int = 2000
    include_headers: bool = True

@dataclass
class CacheConfig:
    """Caching settings."""
    embedding_cache_ttl: int = 3600  # 1 hour
    query_cache_ttl: int = 300  # 5 minutes
    max_cache_size_mb: int = 512

@dataclass
class RateLimitConfig:
    """Rate limiting for 20 concurrent users."""
    max_concurrent_requests: int = 20
    max_requests_per_user_per_minute: int = 30
    gemini_requests_per_minute: int = 60
    vespa_requests_per_minute: int = 200

@dataclass
class Config:
    """Master configuration."""
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    vespa: VespaConfig = field(default_factory=VespaConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "dev")
    project_id: str = os.getenv("PROJECT_ID", "")
    
    # Default tenant (single-tenant today, multi-tenant ready)
    default_tenant_id: str = "default"
    default_workspace_id: str = "default"

# Global config instance
config = Config()

def get_config() -> Config:
    return config
