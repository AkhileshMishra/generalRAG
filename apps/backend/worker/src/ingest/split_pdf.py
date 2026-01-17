"""
PDF Splitting Module for Large Documents

Splits 1-2GB PDFs into manageable batches (2-20 pages) for reliable processing.
Uses Unstructured's split_pdf_page and split_pdf_concurrency_level.
"""
import os
import tempfile
from typing import List, Tuple, Generator
from dataclasses import dataclass
import fitz  # PyMuPDF

@dataclass
class PDFBatch:
    batch_id: int
    start_page: int
    end_page: int
    temp_path: str
    page_count: int

class PDFSplitter:
    """Splits large PDFs into batches for parallel processing."""
    
    def __init__(
        self,
        batch_size: int = 10,
        max_batch_size: int = 20,
        min_batch_size: int = 2
    ):
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
    
    def split(self, pdf_path: str, output_dir: str = None) -> List[PDFBatch]:
        """
        Split PDF into batches.
        
        Args:
            pdf_path: Path to source PDF
            output_dir: Directory for batch files (uses temp if None)
            
        Returns:
            List of PDFBatch objects
        """
        output_dir = output_dir or tempfile.mkdtemp(prefix="pdf_batches_")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        batches = []
        
        # Calculate optimal batch size based on total pages
        batch_size = min(
            self.max_batch_size,
            max(self.min_batch_size, total_pages // 10)
        )
        
        for batch_id, start_page in enumerate(range(0, total_pages, batch_size)):
            end_page = min(start_page + batch_size, total_pages)
            
            # Create batch PDF
            batch_doc = fitz.open()
            batch_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
            
            batch_path = os.path.join(output_dir, f"batch_{batch_id:04d}.pdf")
            batch_doc.save(batch_path)
            batch_doc.close()
            
            batches.append(PDFBatch(
                batch_id=batch_id,
                start_page=start_page,
                end_page=end_page,
                temp_path=batch_path,
                page_count=end_page - start_page
            ))
        
        doc.close()
        return batches
    
    def iter_batches(self, pdf_path: str) -> Generator[PDFBatch, None, None]:
        """Iterate over batches without storing all in memory."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        batch_size = min(
            self.max_batch_size,
            max(self.min_batch_size, total_pages // 10)
        )
        
        for batch_id, start_page in enumerate(range(0, total_pages, batch_size)):
            end_page = min(start_page + batch_size, total_pages)
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                batch_doc = fitz.open()
                batch_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
                batch_doc.save(f.name)
                batch_doc.close()
                
                yield PDFBatch(
                    batch_id=batch_id,
                    start_page=start_page,
                    end_page=end_page,
                    temp_path=f.name,
                    page_count=end_page - start_page
                )
        
        doc.close()
    
    def get_page_info(self, pdf_path: str) -> dict:
        """Get PDF metadata and page count."""
        doc = fitz.open(pdf_path)
        info = {
            "total_pages": len(doc),
            "metadata": doc.metadata,
            "file_size_mb": os.path.getsize(pdf_path) / (1024 * 1024)
        }
        doc.close()
        return info
    
    def cleanup_batches(self, batches: List[PDFBatch]):
        """Remove temporary batch files."""
        for batch in batches:
            if os.path.exists(batch.temp_path):
                os.remove(batch.temp_path)
