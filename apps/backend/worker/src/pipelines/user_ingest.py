"""
User Ingestion Pipeline

Pipeline for user-uploaded documents (private scope).
Supports PDF, CSV, and Excel files.
"""
import os
import tempfile
from typing import Dict, Any
from google.cloud import storage

from src.ingest.file_router import FileRouter, FileType
from src.ingest.tabular_extractor import TabularExtractor
from src.ingest.unstructured_runner import UnstructuredRunner
from src.ingest.gemini_vision import GeminiVision
from src.ingest.chunking import ParentChildChunker
from src.ingest.embeddings import EmbeddingGenerator
from src.ingest.vespa_feed import VespaFeeder
from shared.config.settings import get_config

config = get_config()

class UserIngestionPipeline:
    """Pipeline for user document ingestion (PDF, CSV, Excel)."""
    
    def __init__(self):
        self.extractor = UnstructuredRunner(strategy="hi_res")
        self.tabular = TabularExtractor()
        self.vision = GeminiVision()
        self.chunker = ParentChildChunker()
        self.embedder = EmbeddingGenerator()
        self.feeder = VespaFeeder()
        
        self.storage_client = storage.Client()
        self.user_bucket = os.getenv("USER_UPLOADS_BUCKET")
        self.crops_bucket = os.getenv("PAGE_CROPS_BUCKET")
    
    async def ingest(self, doc_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Run ingestion for user document (any supported type)."""
        stats = {
            "doc_id": doc_id,
            "owner_user_id": metadata["owner_user_id"],
            "status": "processing",
            "chunks_indexed": 0
        }
        
        try:
            local_path = await self._download_file(metadata["gcs_uri"])
            file_type = FileRouter.detect_type(local_path)
            stats["file_type"] = file_type.value
            
            if file_type == FileType.PDF:
                stats = await self._ingest_pdf(local_path, doc_id, metadata, stats)
            elif file_type in (FileType.CSV, FileType.EXCEL):
                stats = await self._ingest_tabular(local_path, doc_id, metadata, stats)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            os.remove(local_path)
            
        except Exception as e:
            stats["status"] = "failed"
            stats["error"] = str(e)
        
        return stats
    
    async def _ingest_tabular(
        self, 
        file_path: str, 
        doc_id: str, 
        metadata: Dict, 
        stats: Dict
    ) -> Dict:
        """Ingest CSV/Excel file - fast path, no vision needed."""
        chunks = self.tabular.extract(file_path, doc_id)
        stats["chunks_extracted"] = len(chunks)
        
        # Convert to Vespa docs
        vespa_docs = self.tabular.to_vespa_docs(
            chunks, doc_id,
            access_scope="private",
            owner_user_id=metadata["owner_user_id"]
        )
        
        # Generate embeddings
        texts = [d["content_text"] for d in vespa_docs]
        embeddings, _ = self.embedder.batch_embed(texts, include_colbert=False)
        
        for i, doc in enumerate(vespa_docs):
            doc["embedding"] = embeddings[i]
        
        # Feed to Vespa
        feed_stats = await self.feeder.feed_docs(vespa_docs)
        stats["chunks_indexed"] = feed_stats["success"]
        stats["status"] = "completed"
        
        return stats
    
    async def _ingest_pdf(
        self, 
        file_path: str, 
        doc_id: str, 
        metadata: Dict, 
        stats: Dict
    ) -> Dict:
        """Ingest PDF file with vision processing."""
        elements, page_types = self.extractor.extract(file_path)
        stats["elements_extracted"] = len(elements)
        
        processed = []
        for elem in elements:
            p = await self._process_element(elem, doc_id, file_path)
            processed.append(p)
        
        chunks = self.chunker.chunk_elements(processed, doc_id)
        texts = [c.content_text for c in chunks]
        embeddings, _ = self.embedder.batch_embed(texts, include_colbert=False)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata["embedding"] = embeddings[i]
        
        feed_stats = await self.feeder.feed_chunks(
            chunks, access_scope="private", owner_user_id=metadata["owner_user_id"]
        )
        
        stats["chunks_indexed"] = feed_stats["success"]
        stats["status"] = "completed"
        return stats
    
    async def _download_file(self, gcs_uri: str) -> str:
        """Download file from GCS preserving extension."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])
        ext = os.path.splitext(blob_path)[1]
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            blob.download_to_filename(f.name)
            return f.name
    
    async def _process_element(self, elem, doc_id: str, pdf_path: str) -> dict:
        """Process PDF element with optional vision."""
        result = {
            "element_id": elem.element_id,
            "element_type": elem.element_type,
            "content": elem.content,
            "page_number": elem.page_number,
            "bbox": elem.bbox,
            "metadata": elem.metadata
        }
        
        if elem.element_type == "table" and elem.bbox != [0, 0, 0, 0]:
            try:
                crop = self.vision.crop_region(pdf_path, elem.page_number - 1, elem.bbox)
                vr = await self.vision.process_table(crop, elem.element_id)
                result["metadata"]["html"] = vr.content
            except Exception as e:
                import logging
                logging.warning(f"Table processing failed for {elem.element_id}: {e}")
        
        elif elem.element_type == "figure" and elem.bbox != [0, 0, 0, 0]:
            try:
                crop = self.vision.crop_region(pdf_path, elem.page_number - 1, elem.bbox)
                vr = await self.vision.process_figure(crop, elem.element_id)
                result["metadata"]["figure_caption"] = vr.content
            except Exception as e:
                import logging
                logging.warning(f"Figure processing failed for {elem.element_id}: {e}")
        
        return result
    
    async def delete_user_documents(self, owner_user_id: str) -> int:
        """Delete all documents for a user."""
        return await self.feeder.delete_by_owner(owner_user_id)
