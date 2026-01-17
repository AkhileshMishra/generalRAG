"""
User Ingestion Pipeline

Pipeline for user-uploaded documents (private scope).
Lighter weight than admin pipeline, optimized for smaller files.
"""
import os
import tempfile
from typing import Dict, Any
from google.cloud import storage

from src.ingest.unstructured_runner import UnstructuredRunner
from src.ingest.gemini_vision import GeminiVision
from src.ingest.chunking import ParentChildChunker
from src.ingest.embeddings import EmbeddingGenerator
from src.ingest.vespa_feed import VespaFeeder

class UserIngestionPipeline:
    """Pipeline for user document ingestion."""
    
    def __init__(self):
        self.extractor = UnstructuredRunner(strategy="hi_res")
        self.vision = GeminiVision()
        self.chunker = ParentChildChunker()
        self.embedder = EmbeddingGenerator()
        self.feeder = VespaFeeder()
        
        self.storage_client = storage.Client()
        self.user_bucket = os.getenv("USER_UPLOADS_BUCKET")
        self.crops_bucket = os.getenv("PAGE_CROPS_BUCKET")
    
    async def ingest(self, doc_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run ingestion pipeline for user document.
        
        Args:
            doc_id: Document identifier
            metadata: Document metadata including gcs_uri, owner_user_id
            
        Returns:
            Ingestion stats
        """
        stats = {
            "doc_id": doc_id,
            "owner_user_id": metadata["owner_user_id"],
            "status": "processing",
            "elements_extracted": 0,
            "chunks_indexed": 0
        }
        
        try:
            # Download PDF
            local_path = await self._download_pdf(metadata["gcs_uri"])
            
            # Extract elements (no batching for smaller files)
            elements, page_types = self.extractor.extract(local_path)
            stats["elements_extracted"] = len(elements)
            
            # Process elements
            processed_elements = []
            for elem in elements:
                processed = await self._process_element(elem, doc_id, local_path)
                processed_elements.append(processed)
            
            # Chunk
            chunks = self.chunker.chunk_elements(processed_elements, doc_id)
            
            # Embed
            texts = [c.content_text for c in chunks]
            embeddings, _ = self.embedder.batch_embed(texts, include_colbert=False)
            
            for i, chunk in enumerate(chunks):
                chunk.metadata["embedding"] = embeddings[i]
            
            # Feed to Vespa with private scope
            feed_stats = await self.feeder.feed_chunks(
                chunks,
                access_scope="private",
                owner_user_id=metadata["owner_user_id"]
            )
            
            stats["chunks_indexed"] = feed_stats["success"]
            stats["status"] = "completed"
            
            # Cleanup
            os.remove(local_path)
            
        except Exception as e:
            stats["status"] = "failed"
            stats["error"] = str(e)
        
        return stats
    
    async def _download_pdf(self, gcs_uri: str) -> str:
        """Download PDF from GCS."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            blob.download_to_filename(f.name)
            return f.name
    
    async def _process_element(self, elem, doc_id: str, pdf_path: str) -> dict:
        """Process a single element."""
        result = {
            "element_id": elem.element_id,
            "element_type": elem.element_type,
            "content": elem.content,
            "page_number": elem.page_number,
            "bbox": elem.bbox,
            "metadata": elem.metadata
        }
        
        # Process tables and figures with Gemini
        if elem.element_type == "table" and elem.bbox != [0, 0, 0, 0]:
            try:
                crop_bytes = self.vision.crop_region(
                    pdf_path, elem.page_number - 1, elem.bbox
                )
                vision_result = await self.vision.process_table(crop_bytes, elem.element_id)
                result["metadata"]["html"] = vision_result.content
                
                # Upload crop
                crop_uri = await self._upload_crop(crop_bytes, doc_id, elem.element_id)
                result["metadata"]["crop_uri"] = crop_uri
            except Exception:
                pass  # Fall back to text content
        
        elif elem.element_type == "figure" and elem.bbox != [0, 0, 0, 0]:
            try:
                crop_bytes = self.vision.crop_region(
                    pdf_path, elem.page_number - 1, elem.bbox
                )
                vision_result = await self.vision.process_figure(crop_bytes, elem.element_id)
                result["metadata"]["figure_caption"] = vision_result.content
                
                crop_uri = await self._upload_crop(crop_bytes, doc_id, elem.element_id)
                result["metadata"]["crop_uri"] = crop_uri
            except Exception:
                pass
        
        return result
    
    async def _upload_crop(self, image_bytes: bytes, doc_id: str, element_id: str) -> str:
        """Upload crop to GCS."""
        bucket = self.storage_client.bucket(self.crops_bucket)
        blob_path = f"user_crops/{doc_id}/{element_id}.png"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        return f"gs://{self.crops_bucket}/{blob_path}"
    
    async def delete_user_documents(self, owner_user_id: str) -> int:
        """Delete all documents for a user."""
        return await self.feeder.delete_by_owner(owner_user_id)
