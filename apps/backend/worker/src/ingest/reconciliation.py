"""
Reconciliation Pass

Backstop to catch missed tables/figures after initial ingestion.
Re-scans pages looking for visual elements that weren't extracted.
"""
import fitz
from typing import List, Dict
from dataclasses import dataclass

from src.ingest.gemini_vision import GeminiVision
from shared.clients.vespa_client import VespaClient
from shared.config.settings import get_config

config = get_config()

@dataclass
class MissedElement:
    page_number: int
    bbox: List[float]
    element_type: str  # table, figure


class ReconciliationPass:
    """Finds and processes missed visual elements."""
    
    def __init__(self, vespa: VespaClient, vision: GeminiVision):
        self.vespa = vespa
        self.vision = vision
        self.min_image_area = 10000  # px^2 - ignore tiny images
    
    async def run(self, doc_id: str, pdf_path: str, tenant_id: str) -> Dict:
        """
        Scan PDF for visual elements not in Vespa.
        
        Returns stats on found/processed elements.
        """
        # Get already-indexed elements
        indexed = await self._get_indexed_elements(doc_id, tenant_id)
        indexed_pages = {(e["page_number"], tuple(e["bbox"])) for e in indexed}
        
        # Scan PDF for visual regions
        candidates = self._find_visual_regions(pdf_path)
        
        # Find missed elements
        missed = [
            c for c in candidates
            if (c.page_number, tuple(c.bbox)) not in indexed_pages
        ]
        
        if not missed:
            return {"missed": 0, "processed": 0}
        
        # Process missed elements
        processed = 0
        for elem in missed:
            try:
                crop = self.vision.crop_region(pdf_path, elem.page_number, elem.bbox)
                
                if elem.element_type == "table":
                    result = await self.vision.process_table(crop, f"recon_{elem.page_number}")
                else:
                    result = await self.vision.process_figure(crop, f"recon_{elem.page_number}")
                
                # Feed to Vespa
                await self._index_element(doc_id, elem, result, tenant_id)
                processed += 1
            except Exception:
                continue
        
        return {"missed": len(missed), "processed": processed}
    
    async def _get_indexed_elements(self, doc_id: str, tenant_id: str) -> List[Dict]:
        """Get all indexed elements for doc."""
        yql = f"""
            select element_id, page_number, bbox, element_type 
            from sop_elements 
            where doc_id = '{doc_id}' and tenant_id = '{tenant_id}'
        """
        return await self.vespa.query(yql, {})
    
    def _find_visual_regions(self, pdf_path: str) -> List[MissedElement]:
        """Detect tables/figures via PyMuPDF heuristics."""
        doc = fitz.open(pdf_path)
        candidates = []
        
        for page_num, page in enumerate(doc):
            # Find images
            for img in page.get_images():
                xref = img[0]
                rect = page.get_image_rects(xref)
                if rect:
                    r = rect[0]
                    area = r.width * r.height
                    if area > self.min_image_area:
                        candidates.append(MissedElement(
                            page_number=page_num,
                            bbox=[r.x0, r.y0, r.x1, r.y1],
                            element_type="figure"
                        ))
            
            # Find table-like regions (rectangles with lines)
            drawings = page.get_drawings()
            rects = [d for d in drawings if d["type"] == "re"]
            if len(rects) > 5:  # Multiple rectangles = likely table
                # Get bounding box of all rects
                all_points = []
                for r in rects:
                    all_points.extend(r["rect"])
                if all_points:
                    candidates.append(MissedElement(
                        page_number=page_num,
                        bbox=[min(all_points[::2]), min(all_points[1::2]),
                              max(all_points[::2]), max(all_points[1::2])],
                        element_type="table"
                    ))
        
        doc.close()
        return candidates
    
    async def _index_element(self, doc_id: str, elem: MissedElement, result, tenant_id: str):
        """Index reconciled element to Vespa."""
        from src.ingest.embeddings import EmbeddingGenerator
        
        embedder = EmbeddingGenerator()
        embedding = embedder.embed(result.content)
        
        doc = {
            "doc_id": doc_id,
            "element_id": f"recon_{doc_id}_{elem.page_number}_{elem.element_type}",
            "tenant_id": tenant_id,
            "workspace_id": config.default_workspace_id,
            "access_scope": "global",
            "element_type": elem.element_type,
            "content_text": result.content,
            "page_number": elem.page_number,
            "bbox": elem.bbox,
            "embedding": embedding
        }
        
        await self.vespa.feed(doc)
