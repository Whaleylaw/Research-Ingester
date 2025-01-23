"""Web content ingestion implementation."""

import io
from pathlib import Path
from typing import BinaryIO, Union
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from .base import BaseIngester, ContentMetadata, IngestedContent, detect_mime_type, get_file_size

class WebIngester(BaseIngester):
    """Handles ingestion of web content."""
    
    def __init__(self):
        super().__init__()
        self.supported_mime_types = {
            'text/html', 'application/xhtml+xml'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def ingest(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Extract text content from web pages."""
        if isinstance(content, HttpUrl):
            response = requests.get(str(content), headers=self.headers)
            response.raise_for_status()
            html_content = response.text
            source_path = str(content)
            mime_type = response.headers.get('content-type', '').split(';')[0]
        else:
            if isinstance(content, Path):
                file_obj = content.open('rb')
                source_path = str(content)
            else:
                file_obj = content
                source_path = "uploaded_file.html"
            
            html_content = file_obj.read().decode('utf-8')
            mime_type = detect_mime_type(file_obj)
        
        try:
            if mime_type not in self.supported_mime_types:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
                element.decompose()
            
            # Extract text content
            raw_text = soup.get_text(separator='\n', strip=True)
            
            # Extract metadata
            title = soup.title.string if soup.title else None
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description['content'] if meta_description else None
            
            # Create metadata
            content_metadata = ContentMetadata(
                source_type="web",
                source_path=source_path,
                mime_type=mime_type,
                title=title,
                file_size=len(html_content.encode('utf-8'))
            )
            
            # Process the extracted text to make it more readable
            lines = (line.strip() for line in raw_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            extracted_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return IngestedContent(
                metadata=content_metadata,
                raw_text=raw_text,
                extracted_text=extracted_text
            )
            
        finally:
            if isinstance(content, (Path, BinaryIO)):
                file_obj.close() 