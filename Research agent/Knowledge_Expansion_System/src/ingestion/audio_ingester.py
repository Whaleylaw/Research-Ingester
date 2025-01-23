"""Audio content ingestion implementation."""

import io
import tempfile
from pathlib import Path
from typing import BinaryIO, Union

import requests
import speech_recognition as sr
from pydantic import HttpUrl

from .base import BaseIngester, ContentMetadata, IngestedContent, detect_mime_type, get_file_size

class AudioIngester(BaseIngester):
    """Handles ingestion of audio content."""
    
    def __init__(self):
        super().__init__()
        self.supported_mime_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
            'audio/vnd.wave', 'audio/wave', 'audio/x-pn-wav'
        }
        self.recognizer = sr.Recognizer()
    
    async def ingest(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Extract text content from audio files using speech recognition."""
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
            source_path = "uploaded_file.audio"
        
        try:
            mime_type = detect_mime_type(file_obj)
            if mime_type not in self.supported_mime_types:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
            
            file_size = get_file_size(file_obj)
            
            # Create a temporary file for speech recognition
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(file_obj.read())
                temp_path = temp_file.name
            
            try:
                # Process audio file
                with sr.AudioFile(temp_path) as audio_file:
                    # Adjust for ambient noise
                    audio = self.recognizer.record(audio_file)
                    
                    # Perform speech recognition
                    raw_text = self.recognizer.recognize_google(audio)
                    
                    # Create metadata
                    content_metadata = ContentMetadata(
                        source_type="audio",
                        source_path=source_path,
                        mime_type=mime_type,
                        file_size=file_size
                    )
                    
                    return IngestedContent(
                        metadata=content_metadata,
                        raw_text=raw_text,
                        extracted_text=raw_text
                    )
            finally:
                Path(temp_path).unlink()  # Clean up temporary file
                
        finally:
            if isinstance(content, (Path, HttpUrl)):
                file_obj.close() 