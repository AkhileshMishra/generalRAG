"""
Unstructured Runner Module

Runs Unstructured partition_pdf with hi_res strategy for layout-aware extraction.
Detects scanned vs digital pages and routes accordingly.

ROUTING LOGIC:
- Digital pages (text_density > 0.001): Use Unstructured text extraction
- Scanned pages (text_density < 0.0001): Flag for Gemini OCR
- Tables/Figures: Always crop and send to Gemini Vision
"""
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import fitz

from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Element, Table, Image, FigureCaption, 
    NarrativeText, Title, ListItem
)

from shared.config.settings import get_config

config = get_config()

class PageType(Enum):
    DIGITAL = "digital"
    SCANNED = "scanned"
    MIXED = "mixed"

@dataclass
class ExtractedElement:
    element_id: str
    element_type: str  # text, table, figure
    content: str
    page_number: int
    bbox: List[float]  # [x0, y0, x1, y1]
    metadata: Dict[str, Any]
    is_scanned: bool = False

class UnstructuredRunner:
    """Runs Unstructured extraction with layout detection."""
    
    def __init__(
        self,
        strategy: str = "hi_res",
        languages: List[str] = None,
        extract_images: bool = True
    ):
        self.strategy = strategy
        self.languages = languages or ["eng"]
        self.extract_images = extract_images
    
    def extract(
        self, 
        pdf_path: str,
        page_offset: int = 0
    ) -> Tuple[List[ExtractedElement], Dict[int, PageType]]:
        """
        Extract elements from PDF using Unstructured.
        
        Args:
            pdf_path: Path to PDF file
            page_offset: Page number offset for batched processing
            
        Returns:
            Tuple of (elements, page_types)
        """
        # Detect page types first
        page_types = self._detect_page_types(pdf_path)
        
        # Run Unstructured partition
        elements = partition_pdf(
            filename=pdf_path,
            strategy=self.strategy,
            languages=self.languages,
            extract_images_in_pdf=self.extract_images,
            infer_table_structure=True,
            include_page_breaks=True
        )
        
        extracted = []
        for i, elem in enumerate(elements):
            page_num = self._get_page_number(elem) + page_offset
            bbox = self._get_bbox(elem)
            is_scanned = page_types.get(page_num - page_offset, PageType.DIGITAL) == PageType.SCANNED
            
            extracted.append(ExtractedElement(
                element_id=f"elem_{page_num}_{i}",
                element_type=self._map_element_type(elem),
                content=str(elem),
                page_number=page_num,
                bbox=bbox,
                metadata=self._extract_metadata(elem),
                is_scanned=is_scanned
            ))
        
        return extracted, page_types
    
    def _detect_page_types(self, pdf_path: str) -> Dict[int, PageType]:
        """
        Detect if each page is scanned or digital.
        
        Uses min_text_density threshold from config:
        - Below threshold (0.0001): SCANNED → route to Gemini OCR
        - Above 0.001: DIGITAL → use Unstructured text
        - Between: MIXED → use both
        """
        doc = fitz.open(pdf_path)
        page_types = {}
        
        min_density = config.ingestion.min_text_density
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            images = page.get_images()
            
            page_area = max(1, page.rect.width * page.rect.height)
            text_density = len(text.strip()) / page_area
            
            if text_density < min_density and images:
                # Very little text but has images = scanned
                # Will be routed to process_scanned_page() in pipeline
                page_types[page_num] = PageType.SCANNED
            elif text_density > 0.001:
                # Good text density = digital
                page_types[page_num] = PageType.DIGITAL
            else:
                # Mixed or unclear - process both ways
                page_types[page_num] = PageType.MIXED
        
        doc.close()
        return page_types
    
    def _get_page_number(self, elem: Element) -> int:
        """Extract page number from element metadata."""
        if hasattr(elem, 'metadata') and hasattr(elem.metadata, 'page_number'):
            return elem.metadata.page_number or 1
        return 1
    
    def _get_bbox(self, elem: Element) -> List[float]:
        """Extract bounding box from element."""
        if hasattr(elem, 'metadata') and hasattr(elem.metadata, 'coordinates'):
            coords = elem.metadata.coordinates
            if coords and hasattr(coords, 'points'):
                points = coords.points
                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    return [min(xs), min(ys), max(xs), max(ys)]
        return [0, 0, 0, 0]
    
    def _map_element_type(self, elem: Element) -> str:
        """Map Unstructured element type to our schema."""
        if isinstance(elem, Table):
            return "table"
        elif isinstance(elem, (Image, FigureCaption)):
            return "figure"
        else:
            return "text"
    
    def _extract_metadata(self, elem: Element) -> Dict[str, Any]:
        """Extract additional metadata from element."""
        meta = {}
        if hasattr(elem, 'metadata'):
            if hasattr(elem.metadata, 'text_as_html'):
                meta['html'] = elem.metadata.text_as_html
            if hasattr(elem.metadata, 'image_path'):
                meta['image_path'] = elem.metadata.image_path
            if hasattr(elem.metadata, 'parent_id'):
                meta['parent_id'] = elem.metadata.parent_id
        return meta
