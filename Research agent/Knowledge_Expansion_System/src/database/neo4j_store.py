"""Neo4j implementation of the Zettelkasten database."""

import hashlib
import json
from datetime import datetime
from typing import List, Optional, Set, Tuple, Union

from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ConstraintError
from pydantic import HttpUrl

from ..config import settings
from .embeddings import EmbeddingProcessor
from .models import SearchQuery, ZettelLink, ZettelNode

class Neo4jZettelkasten:
    """Neo4j-based Zettelkasten implementation."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.embedding_processor = EmbeddingProcessor()
    
    async def setup(self):
        """Set up database constraints and indexes."""
        async with self.driver.session() as session:
            # Create constraints
            await session.run("""
                CREATE CONSTRAINT unique_node_id IF NOT EXISTS
                FOR (n:Note) REQUIRE n.id IS UNIQUE
            """)
            await session.run("""
                CREATE CONSTRAINT unique_content_hash IF NOT EXISTS
                FOR (n:Note) REQUIRE n.content_hash IS UNIQUE
            """)
            
            # Create indexes
            await session.run("CREATE INDEX note_tags IF NOT EXISTS FOR (n:Note) ON n.tags")
            await session.run("CREATE INDEX note_entities IF NOT EXISTS FOR (n:Note) ON n.entities")
    
    async def close(self):
        """Close the database connection."""
        await self.driver.close()
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute a hash of the content for duplicate detection."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def add_note(self, node: ZettelNode) -> ZettelNode:
        """
        Add a new note to the database.
        
        Args:
            node: The note to add
        
        Returns:
            The added note with updated relationships
        """
        async with self.driver.session() as session:
            # Find similar content using embeddings
            similar_nodes = await self._find_similar_nodes(session, node)
            
            # Analyze similarity and novelty
            similarity_scores = [score for _, score in similar_nodes]
            novelty_score = self.embedding_processor.combine_similarity_scores(similarity_scores)
            
            # Update node metadata
            node.is_new_information = novelty_score > 0.3  # Threshold for considering information new
            node.confidence_score = novelty_score
            
            # Create the note
            create_query = """
            CREATE (n:Note)
            SET n = $properties
            RETURN n
            """
            properties = json.loads(node.json())
            try:
                result = await session.run(create_query, properties=properties)
                record = await result.single()
                
                # Create relationships with similar nodes
                for similar_node, similarity_score in similar_nodes:
                    link = ZettelLink(
                        source_id=node.id,
                        target_id=similar_node.id,
                        relationship_type="semantic_similarity",
                        strength=similarity_score,
                        shared_tags=list(set(node.tags) & set(similar_node.tags))
                    )
                    await self.add_link(link)
                
                return node
            except ConstraintError:
                raise ValueError("A note with this content already exists")
    
    async def add_link(self, link: ZettelLink):
        """Add a relationship between two notes."""
        async with self.driver.session() as session:
            query = """
            MATCH (source:Note {id: $source_id})
            MATCH (target:Note {id: $target_id})
            CREATE (source)-[r:RELATED {
                type: $rel_type,
                strength: $strength,
                shared_tags: $shared_tags,
                created_at: $created_at
            }]->(target)
            """
            await session.run(
                query,
                source_id=link.source_id,
                target_id=link.target_id,
                rel_type=link.relationship_type,
                strength=link.strength,
                shared_tags=link.shared_tags,
                created_at=link.created_at.isoformat()
            )
    
    async def get_note(self, note_id: str) -> Optional[ZettelNode]:
        """Retrieve a note by its ID."""
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (n:Note {id: $id}) RETURN n",
                id=note_id
            )
            record = await result.single()
            return ZettelNode(**record["n"]) if record else None
    
    async def search(self, query: SearchQuery) -> List[ZettelNode]:
        """
        Search for notes based on various criteria.
        
        Args:
            query: Search parameters
        
        Returns:
            List of matching notes
        """
        conditions = []
        params = {}
        
        if query.keywords:
            conditions.append("ANY(keyword IN $keywords WHERE n.summary CONTAINS keyword)")
            params["keywords"] = query.keywords
        
        if query.tags:
            conditions.append("ANY(tag IN n.tags WHERE tag IN $tags)")
            params["tags"] = query.tags
        
        if query.entities:
            conditions.append("ANY(entity IN n.entities WHERE entity IN $entities)")
            params["entities"] = query.entities
        
        if query.source_types:
            conditions.append("n.source_type IN $source_types")
            params["source_types"] = query.source_types
        
        if query.only_new_information is not None:
            conditions.append("n.is_new_information = $is_new")
            params["is_new"] = query.only_new_information
        
        if query.min_confidence is not None:
            conditions.append("n.confidence_score >= $min_confidence")
            params["min_confidence"] = query.min_confidence
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        cypher_query = f"""
        MATCH (n:Note)
        WHERE {where_clause}
        RETURN n
        ORDER BY n.created_at DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher_query, **params)
            return [ZettelNode(**record["n"]) async for record in result]
    
    async def get_related_notes(self, note_id: str, min_strength: float = 0.5) -> List[ZettelNode]:
        """Get notes related to the given note."""
        async with self.driver.session() as session:
            query = """
            MATCH (n:Note {id: $id})-[r:RELATED]->(related:Note)
            WHERE r.strength >= $min_strength
            RETURN related
            ORDER BY r.strength DESC
            """
            result = await session.run(query, id=note_id, min_strength=min_strength)
            return [ZettelNode(**record["related"]) async for record in result]
    
    async def _find_similar_nodes(self, session: AsyncSession, node: ZettelNode) -> List[Tuple[ZettelNode, float]]:
        """Find nodes with similar content using embeddings."""
        # Get all existing notes
        query = """
        MATCH (n:Note)
        RETURN n
        """
        result = await session.run(query)
        existing_nodes = [ZettelNode(**record["n"]) async for record in result]
        
        if not existing_nodes:
            return []
        
        # Compare embeddings
        similar_pairs = await self.embedding_processor.find_similar_segments(
            node.summary,
            [n.summary for n in existing_nodes]
        )
        
        # Return nodes with their similarity scores
        return [(existing_nodes[idx], score) for idx, score in similar_pairs] 