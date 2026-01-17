"""
Chunking Module

Implements parent-child chunking to preserve section context.
Child chunks are indexed for retrieval precision.
Parent context is stored for LLM reading.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    element_id: str
    element_type: str
    content_text: str
    parent_context: str
    page_number: int
    bbox: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

class ParentChildChunker:
    """
    Implements parent-child chunking strategy.
    
    - Child chunks: Small, precise units for retrieval
    - Parent context: Larger window including headers/sections for LLM
    """
    
    def __init__(
        self,
        child_chunk_size: int = 500,
        child_overlap: int = 50,
        parent_window_size: int = 2000,
        include_headers: bool = True
    ):
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap
        self.parent_window_size = parent_window_size
        self.include_headers = include_headers
    
    def chunk_elements(
        self,
        elements: List[Dict[str, Any]],
        doc_id: str
    ) -> List[Chunk]:
        """
        Chunk extracted elements with parent context.
        
        Args:
            elements: List of extracted elements from Unstructured
            doc_id: Document identifier
            
        Returns:
            List of Chunk objects ready for indexing
        """
        chunks = []
        
        # Build section hierarchy for context
        sections = self._build_section_hierarchy(elements)
        
        for i, elem in enumerate(elements):
            elem_type = elem.get("element_type", "text")
            content = elem.get("content", "")
            
            if elem_type == "table":
                # Tables are kept as single chunks
                chunks.append(self._create_chunk(
                    doc_id=doc_id,
                    element=elem,
                    content=content,
                    parent_context=self._get_parent_context(elements, i, sections),
                    chunk_index=0
                ))
            elif elem_type == "figure":
                # Figures are kept as single chunks
                chunks.append(self._create_chunk(
                    doc_id=doc_id,
                    element=elem,
                    content=elem.get("figure_caption", content),
                    parent_context=self._get_parent_context(elements, i, sections),
                    chunk_index=0
                ))
            else:
                # Text elements are chunked
                text_chunks = self._split_text(content)
                for j, text_chunk in enumerate(text_chunks):
                    chunks.append(self._create_chunk(
                        doc_id=doc_id,
                        element=elem,
                        content=text_chunk,
                        parent_context=self._get_parent_context(elements, i, sections),
                        chunk_index=j
                    ))
        
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.child_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.child_chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for sep in ['. ', '.\n', '? ', '! ']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + self.child_chunk_size // 2:
                        end = last_sep + len(sep)
                        break
            
            chunks.append(text[start:end].strip())
            start = end - self.child_overlap
        
        return chunks
    
    def _build_section_hierarchy(self, elements: List[Dict]) -> Dict[int, str]:
        """Build mapping of element index to section header."""
        sections = {}
        current_header = ""
        
        for i, elem in enumerate(elements):
            content = elem.get("content", "")
            
            # Detect headers (simple heuristic)
            if self._is_header(content, elem):
                current_header = content.strip()
            
            sections[i] = current_header
        
        return sections
    
    def _is_header(self, content: str, elem: Dict) -> bool:
        """Detect if element is a header."""
        # Check metadata
        if elem.get("metadata", {}).get("is_header"):
            return True
        
        # Heuristics
        content = content.strip()
        if len(content) < 100 and content.isupper():
            return True
        if re.match(r'^[\d.]+\s+[A-Z]', content):
            return True
        if content.endswith(':') and len(content) < 80:
            return True
        
        return False
    
    def _get_parent_context(
        self,
        elements: List[Dict],
        current_index: int,
        sections: Dict[int, str]
    ) -> str:
        """Build parent context window around current element."""
        context_parts = []
        
        # Add section header
        if self.include_headers and sections.get(current_index):
            context_parts.append(f"## {sections[current_index]}\n")
        
        # Gather surrounding elements
        char_count = 0
        
        # Look backward
        for i in range(current_index - 1, -1, -1):
            content = elements[i].get("content", "")
            if char_count + len(content) > self.parent_window_size // 2:
                break
            context_parts.insert(1, content)
            char_count += len(content)
        
        # Add current element
        context_parts.append(elements[current_index].get("content", ""))
        char_count = len(elements[current_index].get("content", ""))
        
        # Look forward
        for i in range(current_index + 1, len(elements)):
            content = elements[i].get("content", "")
            if char_count + len(content) > self.parent_window_size // 2:
                break
            context_parts.append(content)
            char_count += len(content)
        
        return "\n\n".join(context_parts)
    
    def _create_chunk(
        self,
        doc_id: str,
        element: Dict,
        content: str,
        parent_context: str,
        chunk_index: int
    ) -> Chunk:
        """Create a Chunk object."""
        elem_id = element.get("element_id", "unknown")
        
        return Chunk(
            chunk_id=f"{doc_id}_{elem_id}_{chunk_index}",
            doc_id=doc_id,
            element_id=elem_id,
            element_type=element.get("element_type", "text"),
            content_text=content,
            parent_context=parent_context,
            page_number=element.get("page_number", 1),
            bbox=element.get("bbox", [0, 0, 0, 0]),
            metadata=element.get("metadata", {})
        )
