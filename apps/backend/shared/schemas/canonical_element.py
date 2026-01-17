"""
Canonical Element Schema

Defines the standard element model used across the pipeline.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class ElementType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    HEADER = "header"
    LIST = "list"

class AccessScope(str, Enum):
    GLOBAL = "global"
    PRIVATE = "private"

@dataclass
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float
    
    def to_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1]
    
    @classmethod
    def from_list(cls, coords: List[float]) -> "BoundingBox":
        return cls(x0=coords[0], y0=coords[1], x1=coords[2], y1=coords[3])

@dataclass
class CanonicalElement:
    """
    Standard element model for the RAG pipeline.
    
    Used for:
    - Extraction output
    - Chunking input/output
    - Vespa document format
    """
    # Identifiers
    doc_id: str
    element_id: str
    
    # Type and content
    element_type: ElementType
    content_text: str
    parent_context: str = ""
    
    # Location
    page_number: int = 1
    bbox: BoundingBox = field(default_factory=lambda: BoundingBox(0, 0, 0, 0))
    
    # Type-specific content
    table_html: Optional[str] = None
    figure_caption: Optional[str] = None
    crop_uri: Optional[str] = None
    
    # Access control
    access_scope: AccessScope = AccessScope.GLOBAL
    owner_user_id: Optional[str] = None
    
    # Embeddings (populated during indexing)
    embedding: Optional[List[float]] = None
    colbert_tokens: Optional[List[List[float]]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[int] = None
    
    def to_vespa_doc(self) -> Dict[str, Any]:
        """Convert to Vespa document format."""
        doc = {
            "fields": {
                "doc_id": self.doc_id,
                "element_id": self.element_id,
                "element_type": self.element_type.value,
                "content_text": self.content_text,
                "parent_context": self.parent_context,
                "page_number": self.page_number,
                "bbox": self.bbox.to_list(),
                "access_scope": self.access_scope.value,
                "owner_user_id": self.owner_user_id or "",
            }
        }
        
        if self.table_html:
            doc["fields"]["table_html"] = self.table_html
        if self.figure_caption:
            doc["fields"]["figure_caption"] = self.figure_caption
        if self.crop_uri:
            doc["fields"]["crop_uri"] = self.crop_uri
        if self.embedding:
            doc["fields"]["embedding"] = {"values": self.embedding}
        if self.created_at:
            doc["fields"]["created_at"] = self.created_at
            
        return doc
    
    @classmethod
    def from_vespa_hit(cls, hit: Dict[str, Any]) -> "CanonicalElement":
        """Create from Vespa search hit."""
        fields = hit.get("fields", hit)
        
        return cls(
            doc_id=fields["doc_id"],
            element_id=fields["element_id"],
            element_type=ElementType(fields["element_type"]),
            content_text=fields["content_text"],
            parent_context=fields.get("parent_context", ""),
            page_number=fields.get("page_number", 1),
            bbox=BoundingBox.from_list(fields.get("bbox", [0, 0, 0, 0])),
            table_html=fields.get("table_html"),
            figure_caption=fields.get("figure_caption"),
            crop_uri=fields.get("crop_uri"),
            access_scope=AccessScope(fields.get("access_scope", "global")),
            owner_user_id=fields.get("owner_user_id"),
        )
