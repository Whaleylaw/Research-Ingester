"""Video content ingestion implementation."""

import io
import tempfile
from pathlib import Path
from typing import BinaryIO, Union

import moviepy.editor as mp
import requests
import speech_recognition as sr
from pydantic import HttpUrl

from .base import BaseIngester, ContentMetadata, IngestedContent, detect_mime_type, get_file_size

class VideoIngester(BaseIngester):
    """Handles ingestion of video content."""
    
    def __init__(self):
        super().__init__()
        self.supported_mime_types = {
            'video/mp4', 'video/mpeg', 'video/x-msvideo', 'video/quicktime',
            'video/x-ms-wmv', 'video/x-flv', 'video/webm'
        }
        self.recognizer = sr.Recognizer()
    
    async def ingest(self, content: Union[Path, HttpUrl, BinaryIO]) -> IngestedContent:
        """Extract text content from video files by processing the audio track."""
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
            source_path = "uploaded_file.video"
        
        try:
            mime_type = detect_mime_type(file_obj)
            if mime_type not in self.supported_mime_types:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
            
            file_size = get_file_size(file_obj)
            
            # Create temporary files for video and audio processing
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file, \
                 tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                
                video_file.write(file_obj.read())
                video_path = video_file.name
                audio_path = audio_file.name
            
            try:
                # Extract audio from video
                video = mp.VideoFileClip(video_path)
                video.audio.write_audiofile(audio_path, codec='pcm_s16le')
                video.close()
                
                # Process audio file
                text_segments = []
                with sr.AudioFile(audio_path) as audio_file:
                    # Process audio in chunks to handle long videos
                    chunk_duration = 30  # seconds
                    audio_duration = video.duration
                    
                    for start_time in range(0, int(audio_duration), chunk_duration):
                        end_time = min(start_time + chunk_duration, audio_duration)
                        audio = self.recognizer.record(audio_file, duration=end_time-start_time)
                        
                        try:
                            text = self.recognizer.recognize_google(audio)
                            text_segments.append(text)
                        except sr.UnknownValueError:
                            # No speech detected in this segment
                            continue
                
                raw_text = ' '.join(text_segments)
                
                # Create metadata
                content_metadata = ContentMetadata(
                    source_type="video",
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
                # Clean up temporary files
                Path(video_path).unlink()
                Path(audio_path).unlink()
                
        finally:
            if isinstance(content, (Path, HttpUrl)):
                file_obj.close() 