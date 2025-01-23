"""Base classes and utilities for content ingestion."""

import abc
from pathlib import Path
from typing import BinaryIO, Optional, Union

import magic
from pydantic import BaseModel, HttpUrl

from ..config import settings
from ..llm.base import Summary

class ContentMetadata(BaseModel):
    """Metadata for ingested content."""
    source_type: str
    source_path: Union[str, HttpUrl]
    mime_type: str
    file_size: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[str] = None
    language: Optional[str] = None

class IngestedContent(BaseModel):
    """Represents processed content with metadata."""
    metadata: ContentMetadata
    raw_text: str
    extracted_text: str
    summary: Optional[Summary] = None

class BaseIngester(abc.ABC):
    """Base class for content ingesters."""
    
    def __init__(self):
        self.supported_mime_types: set[str] = set()
        from ..llm.base import LLMProcessor
        self.llm_processor = LLMProcessor()
    
    @abc.abstractmethod
    async def ingest(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Process and extract text from the content."""
        pass
    
    async def process_with_summary(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Process content and generate summary."""
        # First, perform basic ingestion
        ingested = await self.ingest(content)
        
        # Generate summary using LLM
        summary = await self.llm_processor.chunk_and_summarize(ingested.extracted_text)
        
        # Update ingested content with summary
        ingested.summary = summary
        return ingested
    
    def can_handle(self, mime_type: str) -> bool:
        """Check if this ingester can handle the given mime type."""
        return mime_type in self.supported_mime_types

def detect_mime_type(file_path: Union[Path, BinaryIO]) -> str:
    """Detect MIME type of a file."""
    if isinstance(file_path, Path):
        return magic.from_file(str(file_path), mime=True)
    return magic.from_buffer(file_path.read(2048), mime=True)

def get_file_size(file_path: Union[Path, BinaryIO]) -> int:
    """Get file size in bytes."""
    if isinstance(file_path, Path):
        return file_path.stat().st_size
    file_path.seek(0, 2)  # Seek to end
    size = file_path.tell()
    file_path.seek(0)  # Reset position
    return size

def validate_file_size(size: int) -> bool:
    """Check if file size is within allowed limits."""
    max_size = parse_size(settings.MAX_UPLOAD_SIZE)
    return size <= max_size

def parse_size(size_str: str) -> int:
    """Convert size string (e.g., '100MB') to bytes."""
    units = {'B': 1, 'KB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
    size = size_str.strip().upper()
    number = float(''.join(filter(str.isdigit, size)))
    unit = ''.join(filter(str.isalpha, size))
    return int(number * units[unit]) 