"""
Gemini Vision Module

Handles vision-to-text conversion for tables and figures using Gemini API.

CRITICAL: Never upload full PDFs to Gemini. Always:
1. Split PDF into pages
2. Render pages as images
3. Crop regions (tables/figures)
4. Send individual images to Gemini

Gemini PDF limits: 50MB / 1000 pages - our corpus is 1-2GB per file.
"""
import os
import io
import base64
from typing import List, Optional
from dataclasses import dataclass
import httpx
from PIL import Image
import fitz

from shared.config.settings import get_config

config = get_config()

@dataclass
class VisionResult:
    element_id: str
    content_type: str  # table_html, figure_caption, ocr_text
    content: str
    confidence: float

class GeminiVision:
    """
    Gemini Vision API client for document understanding.
    
    IMPORTANT: This class ONLY accepts image bytes, never PDFs.
    The ingestion pipeline must:
    1. split_pdf() -> page batches
    2. render_page() -> PNG bytes
    3. crop_region() -> PNG bytes for tables/figures
    4. Call this class with image bytes only
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = config.gemini.vision_model
        self.max_image_size = config.gemini.max_image_size_mb * 1024 * 1024
    
    async def process_table(
        self, 
        image_bytes: bytes,
        element_id: str
    ) -> VisionResult:
        """
        Convert table image to HTML/Markdown.
        
        Args:
            image_bytes: PNG/JPEG bytes of cropped table region
            element_id: Element identifier
        """
        self._validate_image_size(image_bytes)
        
        prompt = """Analyze this table image and convert it to HTML format.
        
Requirements:
- Preserve all cell spans (rowspan, colspan)
- Keep headers in <thead> and data in <tbody>
- Maintain alignment and structure
- Include all text exactly as shown

Output only the HTML table, no explanation."""

        response = await self._call_gemini(image_bytes, prompt)
        
        return VisionResult(
            element_id=element_id,
            content_type="table_html",
            content=response,
            confidence=0.9
        )
    
    async def process_figure(
        self,
        image_bytes: bytes,
        element_id: str
    ) -> VisionResult:
        """
        Generate dense caption for figure/flowchart.
        
        Args:
            image_bytes: PNG/JPEG bytes of cropped figure region
            element_id: Element identifier
        """
        self._validate_image_size(image_bytes)
        
        prompt = """Describe this figure/diagram in detail.

Requirements:
- If it's a flowchart: describe each step, decision node, and flow direction
- If it's a diagram: describe all components, labels, and relationships
- If it's a chart: describe the data, axes, trends, and key values
- Include ALL text labels visible in the image
- Be specific about positions (top, bottom, left, right)

Provide a comprehensive description that would allow someone to understand the figure without seeing it."""

        response = await self._call_gemini(image_bytes, prompt)
        
        return VisionResult(
            element_id=element_id,
            content_type="figure_caption",
            content=response,
            confidence=0.85
        )
    
    async def process_scanned_page(
        self,
        image_bytes: bytes,
        element_id: str
    ) -> VisionResult:
        """
        OCR scanned page using Gemini.
        
        Args:
            image_bytes: PNG bytes of rendered page (NOT PDF)
            element_id: Element identifier
        """
        self._validate_image_size(image_bytes)
        
        prompt = """Extract all text from this scanned document page.

Requirements:
- Preserve paragraph structure
- Maintain headers and subheaders
- Keep bullet points and numbered lists
- Preserve table structure if present (as markdown)
- Include all visible text

Output the extracted text with proper formatting."""

        response = await self._call_gemini(image_bytes, prompt)
        
        return VisionResult(
            element_id=element_id,
            content_type="ocr_text",
            content=response,
            confidence=0.8
        )
    
    def _validate_image_size(self, image_bytes: bytes):
        """Ensure image is within Gemini limits."""
        if len(image_bytes) > self.max_image_size:
            raise ValueError(
                f"Image too large: {len(image_bytes) / 1024 / 1024:.1f}MB > "
                f"{config.gemini.max_image_size_mb}MB limit"
            )
    
    async def _call_gemini(self, image_bytes: bytes, prompt: str) -> str:
        """Make API call to Gemini with image bytes (never PDF)."""
        image_b64 = base64.b64encode(image_bytes).decode()
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }
        
        url = f"{self.GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    def crop_region(
        self,
        pdf_path: str,
        page_number: int,
        bbox: List[float],
        dpi: int = 150
    ) -> bytes:
        """
        Crop a region from PDF page and return as PNG bytes.
        
        This renders the page first, then crops - never sends PDF to Gemini.
        """
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        
        rect = fitz.Rect(bbox)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        
        pix = page.get_pixmap(matrix=mat, clip=rect)
        img_bytes = pix.tobytes("png")
        
        doc.close()
        
        self._validate_image_size(img_bytes)
        return img_bytes
    
    def render_page(self, pdf_path: str, page_number: int, dpi: int = 150) -> bytes:
        """
        Render full page as PNG bytes.
        
        Use this for scanned page OCR - sends image to Gemini, not PDF.
        """
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        doc.close()
        
        self._validate_image_size(img_bytes)
        return img_bytes
