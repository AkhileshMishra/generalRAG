"""
File Router

Routes incoming files to appropriate extraction pipeline based on type.
"""
import os
from typing import Dict, Any
from enum import Enum


class FileType(Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"


class FileRouter:
    """Route files to appropriate extractor."""
    
    EXTENSIONS = {
        '.pdf': FileType.PDF,
        '.csv': FileType.CSV,
        '.xlsx': FileType.EXCEL,
        '.xls': FileType.EXCEL,
    }
    
    @classmethod
    def detect_type(cls, file_path: str) -> FileType:
        """Detect file type from extension."""
        ext = os.path.splitext(file_path)[1].lower()
        return cls.EXTENSIONS.get(ext, FileType.UNKNOWN)
    
    @classmethod
    def get_accepted_extensions(cls) -> list:
        """Return list of accepted file extensions."""
        return list(cls.EXTENSIONS.keys())
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if file type is supported."""
        return cls.detect_type(file_path) != FileType.UNKNOWN
