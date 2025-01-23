"""Content ingestion package."""

from pathlib import Path
from typing import BinaryIO, Dict, Type, Union

from pydantic import HttpUrl

from .audio_ingester import AudioIngester
from .base import BaseIngester, IngestedContent
from .pdf_ingester import PDFIngester
from .video_ingester import VideoIngester
from .web_ingester import WebIngester

class IngesterFactory:
    """Factory for creating appropriate content ingesters."""
    
    def __init__(self):
        self._ingesters: Dict[str, BaseIngester] = {}
        self._register_ingesters()
    
    def _register_ingesters(self):
        """Register all available ingesters."""
        ingesters = [
            PDFIngester(),
            AudioIngester(),
            VideoIngester(),
            WebIngester()
        ]
        
        for ingester in ingesters:
            for mime_type in ingester.supported_mime_types:
                self._ingesters[mime_type] = ingester
    
    def get_ingester(self, mime_type: str) -> BaseIngester:
        """Get appropriate ingester for the given MIME type."""
        ingester = self._ingesters.get(mime_type)
        if not ingester:
            raise ValueError(f"No ingester available for MIME type: {mime_type}")
        return ingester

class ContentIngestionManager:
    """Manages the content ingestion process."""
    
    def __init__(self):
        self.factory = IngesterFactory()
    
    async def ingest_content(
        self,
        content: Union[Path, HttpUrl, BinaryIO],
        mime_type: str = None,
        generate_summary: bool = True
    ) -> IngestedContent:
        """
        Ingest content and extract text.
        
        Args:
            content: The content to ingest (file path, URL, or file-like object)
            mime_type: Optional MIME type (if known)
            generate_summary: Whether to generate a summary using LLM
        
        Returns:
            IngestedContent object containing extracted text, metadata, and optional summary
        """
        # If mime_type is not provided, detect it
        if not mime_type and not isinstance(content, HttpUrl):
            from .base import detect_mime_type
            mime_type = detect_mime_type(content)
        
        # Get appropriate ingester
        ingester = self.factory.get_ingester(mime_type)
        
        # Process the content with or without summary
        if generate_summary:
            return await ingester.process_with_summary(content)
        else:
            return await ingester.ingest(content) 