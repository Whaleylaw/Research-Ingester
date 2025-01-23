"""Database models for the Zettelkasten system."""

from datetime import datetime
from typing import Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, HttpUrl

class ZettelNode(BaseModel):
    """Represents a note in the Zettelkasten system."""
    
    id: str = Field(description="Unique identifier for the note")
    title: str = Field(description="Title of the note")
    source_type: str = Field(description="Type of source (pdf, video, audio, web)")
    source_path: Union[str, HttpUrl] = Field(description="Original source path or URL")
    content_hash: str = Field(description="Hash of the content for duplicate detection")
    
    # Summary data
    summary: str = Field(description="Concise summary of the content")
    main_points: List[str] = Field(description="Key points from the content")
    key_concepts: Dict[str, str] = Field(description="Important concepts and their explanations")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    is_new_information: bool = Field(description="Whether this represents new knowledge")
    confidence_score: float = Field(description="Confidence in the novelty assessment (0-1)")
    
    # Relationships
    tags: Set[str] = Field(default_factory=set, description="Topics and themes")
    entities: Set[str] = Field(default_factory=set, description="Named entities mentioned")
    related_nodes: Set[str] = Field(default_factory=set, description="IDs of related notes")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v)
        }

class ZettelLink(BaseModel):
    """Represents a relationship between two notes."""
    
    source_id: str = Field(description="ID of the source note")
    target_id: str = Field(description="ID of the target note")
    relationship_type: str = Field(description="Type of relationship")
    strength: float = Field(description="Strength of the relationship (0-1)")
    shared_tags: List[str] = Field(description="Tags shared between the nodes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SearchQuery(BaseModel):
    """Model for searching the Zettelkasten."""
    
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    source_types: Optional[List[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    only_new_information: Optional[bool] = None
    min_confidence: Optional[float] = None 