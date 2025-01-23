"""Service layer for the Zettelkasten database."""

import uuid
from typing import Dict, List, Optional, Tuple

from ..ingestion import IngestedContent
from .embeddings import EmbeddingProcessor
from .models import SearchQuery, ZettelNode
from .neo4j_store import Neo4jZettelkasten

class ZettelkastenService:
    """Service for managing the Zettelkasten database."""
    
    def __init__(self):
        """Initialize the service."""
        self.db = Neo4jZettelkasten()
        self.embedding_processor = EmbeddingProcessor()
    
    async def setup(self):
        """Set up the database."""
        await self.db.setup()
    
    async def close(self):
        """Close database connections."""
        await self.db.close()
    
    async def process_ingested_content(
        self,
        content: IngestedContent,
        similarity_threshold: float = 0.85
    ) -> Tuple[ZettelNode, List[ZettelNode]]:
        """
        Process ingested content and add it to the Zettelkasten.
        
        Args:
            content: The ingested content to process
            similarity_threshold: Threshold for considering content similar
        
        Returns:
            Tuple of (created node, list of similar nodes)
        """
        # Create a new node
        node = ZettelNode(
            id=str(uuid.uuid4()),
            title=content.metadata.title or "Untitled",
            source_type=content.metadata.source_type,
            source_path=content.metadata.source_path,
            content_hash=self.db._compute_content_hash(content.extracted_text),
            
            # Summary data from LLM
            summary=content.summary.summary,
            main_points=content.summary.main_points,
            key_concepts=content.summary.key_concepts,
            
            # Tags and entities from LLM analysis
            tags=set(content.summary.topics),
            entities=set(content.summary.entities)
        )
        
        # Add to database and get similar nodes
        created_node = await self.db.add_note(node)
        similar_nodes = await self.get_similar_content(created_node.id, similarity_threshold)
        
        return created_node, similar_nodes
    
    async def search_notes(
        self,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source_types: Optional[List[str]] = None,
        only_new: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[ZettelNode]:
        """
        Search for notes in the Zettelkasten.
        
        Args:
            keywords: Optional keywords to search for
            tags: Optional tags to filter by
            source_types: Optional source types to filter by
            only_new: Whether to only return new information
            min_confidence: Minimum confidence score for novelty
        
        Returns:
            List of matching notes
        """
        query = SearchQuery(
            keywords=keywords,
            tags=tags,
            source_types=source_types,
            only_new_information=only_new,
            min_confidence=min_confidence
        )
        return await self.db.search(query)
    
    async def get_note(self, note_id: str) -> Optional[ZettelNode]:
        """Get a note by its ID."""
        return await self.db.get_note(note_id)
    
    async def get_related(
        self,
        note_id: str,
        min_strength: float = 0.5
    ) -> List[ZettelNode]:
        """Get notes related to the given note."""
        return await self.db.get_related_notes(note_id, min_strength)
    
    async def get_similar_content(
        self,
        note_id: str,
        min_similarity: float = 0.85
    ) -> List[ZettelNode]:
        """
        Find content similar to the given note.
        
        Args:
            note_id: ID of the note to compare
            min_similarity: Minimum similarity score (0-1)
        
        Returns:
            List of similar notes
        """
        note = await self.get_note(note_id)
        if not note:
            raise ValueError("Note not found")
        
        # Get all notes
        all_notes = await self.search_notes()
        if not all_notes:
            return []
        
        # Find similar content using embeddings
        similar_pairs = await self.embedding_processor.find_similar_segments(
            note.summary,
            [n.summary for n in all_notes if n.id != note_id],
            min_similarity
        )
        
        # Return similar notes
        return [all_notes[idx] for idx, _ in similar_pairs]
    
    async def analyze_novelty(self, note_id: str) -> Dict[str, float]:
        """
        Analyze how novel the information in a note is.
        
        Args:
            note_id: ID of the note to analyze
        
        Returns:
            Dictionary with novelty metrics
        """
        note = await self.get_note(note_id)
        if not note:
            raise ValueError("Note not found")
        
        # Get related and similar content
        related = await self.get_related(note_id)
        similar = await self.get_similar_content(note_id)
        
        # Calculate different novelty metrics
        tag_overlap = sum(len(set(note.tags) & set(r.tags)) for r in related)
        concept_overlap = sum(
            len(set(note.key_concepts.keys()) & set(r.key_concepts.keys()))
            for r in related
        )
        
        # Normalize scores
        max_tag_overlap = len(note.tags) * len(related) if related else 1
        max_concept_overlap = len(note.key_concepts) * len(related) if related else 1
        
        tag_novelty = 1 - (tag_overlap / max_tag_overlap)
        concept_novelty = 1 - (concept_overlap / max_concept_overlap)
        semantic_novelty = 1 - (len(similar) / 10)  # Cap at 10 similar documents
        
        # Combine scores
        overall_novelty = (tag_novelty + concept_novelty + semantic_novelty) / 3
        
        return {
            "overall_novelty": overall_novelty,
            "tag_novelty": tag_novelty,
            "concept_novelty": concept_novelty,
            "semantic_novelty": semantic_novelty,
            "similar_documents": len(similar),
            "confidence": note.confidence_score
        } 