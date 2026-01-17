"""
Admin Ingestion Pipeline

Full pipeline for admin-uploaded documents (global scope).
Handles large PDFs with batching, vision processing, and indexing.
"""
import os
import tempfile
from typing import Dict, Any
from google.cloud import storage

from src.ingest.split_pdf import PDFSplitter
from src.ingest.unstructured_runner import UnstructuredRunner, PageType
from src.ingest.gemini_vision import GeminiVision
from src.ingest.chunking import ParentChildChunker
from src.ingest.embeddings import EmbeddingGenerator
from src.ingest.vespa_feed import VespaFeeder
from src.retries_qos import with_retry, IngestionError

class AdminIngestionPipeline:
    """Pipeline for admin document ingestion."""
    
    def __init__(self):
        self.splitter = PDFSplitter(batch_size=10)
        self.extractor = UnstructuredRunner(strategy="hi_res")
        self.vision = GeminiVision()
        self.chunker = ParentChildChunker()
        self.embedder = EmbeddingGenerator()
        self.feeder = VespaFeeder()
        
        self.storage_client = storage.Client()
        self.raw_bucket = os.getenv("RAW_PDFS_BUCKET")
        self.crops_bucket = os.getenv("PAGE_CROPS_BUCKET")
    
    async def ingest(self, doc_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full ingestion pipeline for admin document.
        
        Args:
            doc_id: Document identifier
            metadata: Document metadata including gcs_uri
            
        Returns:
            Ingestion stats
        """
        stats = {
            "doc_id": doc_id,
            "status": "processing",
            "batches_processed": 0,
            "elements_extracted": 0,
            "chunks_indexed": 0,
            "errors": []
        }
        
        try:
            # Download PDF from GCS
            local_path = await self._download_pdf(metadata["gcs_uri"])
            
            # Get PDF info
            pdf_info = self.splitter.get_page_info(local_path)
            stats["total_pages"] = pdf_info["total_pages"]
            stats["file_size_mb"] = pdf_info["file_size_mb"]
            
            all_elements = []
            
            # Process in batches
            for batch in self.splitter.iter_batches(local_path):
                try:
                    batch_elements = await self._process_batch(
                        batch, doc_id, metadata
                    )
                    all_elements.extend(batch_elements)
                    stats["batches_processed"] += 1
                except Exception as e:
                    stats["errors"].append({
                        "batch_id": batch.batch_id,
                        "error": str(e)
                    })
                finally:
                    # Cleanup batch file
                    if os.path.exists(batch.temp_path):
                        os.remove(batch.temp_path)
            
            stats["elements_extracted"] = len(all_elements)
            
            # Chunk elements
            chunks = self.chunker.chunk_elements(all_elements, doc_id)
            
            # Generate embeddings
            texts = [c.content_text for c in chunks]
            embeddings, colbert_embeddings = self.embedder.batch_embed(
                texts, include_colbert=True
            )
            
            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata["embedding"] = embeddings[i]
                if colbert_embeddings:
                    chunk.metadata["colbert_tokens"] = colbert_embeddings[i]
            
            # Feed to Vespa
            feed_stats = await self.feeder.feed_chunks(
                chunks,
                access_scope="global",
                owner_user_id=None
            )
            
            stats["chunks_indexed"] = feed_stats["success"]
            stats["index_failures"] = feed_stats["failed"]
            stats["status"] = "completed"
            
            # Cleanup
            os.remove(local_path)
            
        except Exception as e:
            stats["status"] = "failed"
            stats["errors"].append({"stage": "pipeline", "error": str(e)})
        
        return stats
    
    async def _download_pdf(self, gcs_uri: str) -> str:
        """Download PDF from GCS to local temp file."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            blob.download_to_filename(f.name)
            return f.name
    
    async def _process_batch(
        self,
        batch,
        doc_id: str,
        metadata: Dict
    ) -> list:
        """Process a single batch of pages."""
        # Extract elements
        elements, page_types = self.extractor.extract(
            batch.temp_path,
            page_offset=batch.start_page
        )
        
        processed_elements = []
        
        for elem in elements:
            # Route based on element type and page type
            if elem.element_type == "table":
                # Process table with Gemini
                crop_bytes = self.vision.crop_region(
                    batch.temp_path,
                    elem.page_number - batch.start_page,
                    elem.bbox
                )
                result = await self.vision.process_table(crop_bytes, elem.element_id)
                
                # Upload crop to GCS
                crop_uri = await self._upload_crop(
                    crop_bytes, doc_id, elem.element_id
                )
                
                elem.metadata["html"] = result.content
                elem.metadata["crop_uri"] = crop_uri
                
            elif elem.element_type == "figure":
                # Process figure with Gemini
                crop_bytes = self.vision.crop_region(
                    batch.temp_path,
                    elem.page_number - batch.start_page,
                    elem.bbox
                )
                result = await self.vision.process_figure(crop_bytes, elem.element_id)
                
                crop_uri = await self._upload_crop(
                    crop_bytes, doc_id, elem.element_id
                )
                
                elem.metadata["figure_caption"] = result.content
                elem.metadata["crop_uri"] = crop_uri
                
            elif elem.is_scanned:
                # OCR scanned page with Gemini
                page_bytes = self.vision.render_page(
                    batch.temp_path,
                    elem.page_number - batch.start_page
                )
                result = await self.vision.process_scanned_page(
                    page_bytes, elem.element_id
                )
                elem.content = result.content
            
            processed_elements.append({
                "element_id": elem.element_id,
                "element_type": elem.element_type,
                "content": elem.content,
                "page_number": elem.page_number,
                "bbox": elem.bbox,
                "metadata": elem.metadata
            })
        
        return processed_elements
    
    async def _upload_crop(
        self,
        image_bytes: bytes,
        doc_id: str,
        element_id: str
    ) -> str:
        """Upload crop image to GCS."""
        bucket = self.storage_client.bucket(self.crops_bucket)
        blob_path = f"{doc_id}/{element_id}.png"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_string(image_bytes, content_type="image/png")
        
        return f"gs://{self.crops_bucket}/{blob_path}"
