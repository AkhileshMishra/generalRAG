"""
Tabular Data Extractor

Extracts and chunks CSV/Excel files for RAG indexing.
No vision processing needed - direct structure preservation.
"""
import os
import hashlib
from typing import List, Dict, Any, Generator
from dataclasses import dataclass
import pandas as pd

from shared.config.settings import get_config

config = get_config()

@dataclass
class TabularChunk:
    chunk_id: str
    content_text: str
    sheet_name: str
    row_start: int
    row_end: int
    columns: List[str]
    metadata: Dict[str, Any]


class TabularExtractor:
    """Extract and chunk CSV/Excel files."""
    
    def __init__(self, rows_per_chunk: int = 50):
        self.rows_per_chunk = rows_per_chunk
    
    def extract(self, file_path: str, doc_id: str) -> List[TabularChunk]:
        """Extract chunks from CSV or Excel file."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            return self._extract_csv(file_path, doc_id)
        elif ext in ('.xlsx', '.xls'):
            return self._extract_excel(file_path, doc_id)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _extract_csv(self, file_path: str, doc_id: str) -> List[TabularChunk]:
        """Extract from CSV file."""
        df = pd.read_csv(file_path)
        return self._chunk_dataframe(df, doc_id, "sheet1")
    
    def _extract_excel(self, file_path: str, doc_id: str) -> List[TabularChunk]:
        """Extract from Excel file (all sheets)."""
        chunks = []
        xlsx = pd.ExcelFile(file_path)
        
        for sheet_name in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=sheet_name)
            chunks.extend(self._chunk_dataframe(df, doc_id, sheet_name))
        
        return chunks
    
    def _chunk_dataframe(
        self, 
        df: pd.DataFrame, 
        doc_id: str, 
        sheet_name: str
    ) -> List[TabularChunk]:
        """Chunk dataframe into row groups with column headers as context."""
        chunks = []
        columns = df.columns.tolist()
        header_text = " | ".join(str(c) for c in columns)
        
        for i in range(0, len(df), self.rows_per_chunk):
            batch = df.iloc[i:i + self.rows_per_chunk]
            
            # Serialize rows with headers for each row (better retrieval)
            rows_text = []
            for _, row in batch.iterrows():
                row_parts = [f"{col}: {row[col]}" for col in columns]
                rows_text.append(" | ".join(row_parts))
            
            content = f"Columns: {header_text}\n\n" + "\n".join(rows_text)
            
            chunk_id = hashlib.sha256(
                f"{doc_id}_{sheet_name}_{i}".encode()
            ).hexdigest()[:12]
            
            chunks.append(TabularChunk(
                chunk_id=f"{doc_id}_{chunk_id}",
                content_text=content,
                sheet_name=sheet_name,
                row_start=i,
                row_end=min(i + self.rows_per_chunk, len(df)),
                columns=columns,
                metadata={
                    "total_rows": len(df),
                    "file_type": "tabular"
                }
            ))
        
        return chunks
    
    def to_vespa_docs(
        self,
        chunks: List[TabularChunk],
        doc_id: str,
        access_scope: str,
        owner_user_id: str = None,
        tenant_id: str = None,
        workspace_id: str = None
    ) -> List[Dict]:
        """Convert chunks to Vespa document format."""
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        
        docs = []
        for chunk in chunks:
            docs.append({
                "doc_id": doc_id,
                "element_id": chunk.chunk_id,
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
                "access_scope": access_scope,
                "owner_user_id": owner_user_id,
                "element_type": "table",
                "content_text": chunk.content_text,
                "parent_context": f"Sheet: {chunk.sheet_name}, Rows {chunk.row_start}-{chunk.row_end}",
                "page_number": chunk.row_start // self.rows_per_chunk,
                "bbox": [0, 0, 0, 0],
                "metadata": chunk.metadata
            })
        
        return docs
