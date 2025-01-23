"""PDF content ingestion implementation."""

import io
from pathlib import Path
from typing import BinaryIO, Union

import PyPDF2
import requests
from pydantic import HttpUrl

from .base import BaseIngester, ContentMetadata, IngestedContent, detect_mime_type, get_file_size

class PDFIngester(BaseIngester):
    """Handles ingestion of PDF documents."""
    
    def __init__(self):
        super().__init__()
        self.supported_mime_types = {'application/pdf'}
    
    async def ingest(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Extract text content from PDF files."""
        if isinstance(content, HttpUrl):
            response = requests.get(str(content))
            response.raise_for_status()
            file_obj = io.BytesIO(response.content)
            source_path = str(content)
        elif isinstance(content, Path):
            file_obj = content.open('rb')
            source_path = str(content)
        else:
            file_obj = content
            source_path = "uploaded_file.pdf"
        
        try:
            mime_type = detect_mime_type(file_obj)
            if mime_type not in self.supported_mime_types:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
            
            file_size = get_file_size(file_obj)
            
            # Extract text from PDF
            reader = PyPDF2.PdfReader(file_obj)
            text_content = []
            metadata = reader.metadata or {}
            
            for page in reader.pages:
                text_content.append(page.extract_text())
            
            raw_text = '\n'.join(text_content)
            
            # Create metadata
            content_metadata = ContentMetadata(
                source_type="pdf",
                source_path=source_path,
                mime_type=mime_type,
                file_size=file_size,
                title=metadata.get('/Title', None),
                author=metadata.get('/Author', None),
                created_date=metadata.get('/CreationDate', None)
            )
            
            return IngestedContent(
                metadata=content_metadata,
                raw_text=raw_text,
                extracted_text=raw_text  # For PDFs, extracted text is same as raw text
            )
            
        finally:
            if isinstance(content, (Path, HttpUrl)):
                file_obj.close() 