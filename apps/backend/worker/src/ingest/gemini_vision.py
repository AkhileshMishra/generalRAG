"""
Gemini Vision Module

Handles vision-to-text conversion for tables and figures using Gemini API.
Crops regions from PDF pages and sends to Gemini for:
- Table → HTML/Markdown transcription
- Figure/Flowchart → Dense step-by-step caption
- Scanned page → OCR text
"""
import os
import io
import base64
from typing import List, Optional
from dataclasses import dataclass
import httpx
from PIL import Image
import fitz

@dataclass
class VisionResult:
    element_id: str
    content_type: str  # table_html, figure_caption, ocr_text
    content: str
    confidence: float

class GeminiVision:
    """Gemini Vision API client for document understanding."""
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    async def process_table(
        self, 
        image_bytes: bytes,
        element_id: str
    ) -> VisionResult:
        """Convert table image to HTML/Markdown."""
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
        """Generate dense caption for figure/flowchart."""
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
        """OCR scanned page using Gemini."""
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
    
    async def _call_gemini(self, image_bytes: bytes, prompt: str) -> str:
        """Make API call to Gemini."""
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
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.GEMINI_API_URL}?key={self.api_key}",
                json=payload
            )
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
        """Crop a region from PDF page and return as PNG bytes."""
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        
        # Convert bbox to fitz.Rect
        rect = fitz.Rect(bbox)
        
        # Render at higher DPI for better quality
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        clip = rect
        
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img_bytes = pix.tobytes("png")
        
        doc.close()
        return img_bytes
    
    def render_page(self, pdf_path: str, page_number: int, dpi: int = 150) -> bytes:
        """Render full page as PNG."""
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        doc.close()
        return img_bytes
