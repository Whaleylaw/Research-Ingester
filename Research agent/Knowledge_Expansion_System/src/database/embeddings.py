"""Embeddings and semantic similarity functionality."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from langchain.embeddings import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingProcessor:
    """Handles text embedding and similarity computations."""
    
    def __init__(self):
        """Initialize the embedding processor."""
        from ..config import settings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            Array of embeddings
        """
        # Get embeddings using OpenAI
        embeddings = await self.embeddings.aembed_documents(texts)
        return np.array(embeddings)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score between 0 and 1
        """
        # Reshape embeddings for sklearn
        e1 = embedding1.reshape(1, -1)
        e2 = embedding2.reshape(1, -1)
        return float(cosine_similarity(e1, e2)[0, 0])
    
    async def find_similar_segments(
        self,
        text: str,
        existing_texts: List[str],
        threshold: float = 0.85
    ) -> List[Tuple[int, float]]:
        """
        Find similar segments in existing texts.
        
        Args:
            text: New text to compare
            existing_texts: List of existing texts to compare against
            threshold: Minimum similarity score to consider (default: 0.85)
        
        Returns:
            List of tuples (index, similarity_score) for similar segments
        """
        # Get embeddings
        new_embedding = await self.get_embeddings([text])
        existing_embeddings = await self.get_embeddings(existing_texts)
        
        # Compute similarities
        similarities = [
            self.compute_similarity(new_embedding[0], existing_embedding)
            for existing_embedding in existing_embeddings
        ]
        
        # Return indices and scores of similar segments
        return [
            (idx, score)
            for idx, score in enumerate(similarities)
            if score >= threshold
        ]
    
    def combine_similarity_scores(self, scores: List[float]) -> float:
        """
        Combine multiple similarity scores into a single novelty score.
        
        Args:
            scores: List of similarity scores
        
        Returns:
            Combined novelty score between 0 and 1
        """
        if not scores:
            return 1.0  # Completely new
        
        # Use the maximum similarity as the base
        max_similarity = max(scores)
        
        # Adjust based on number of similar segments
        coverage_factor = min(len(scores) / 5, 1.0)  # Cap at 5 similar segments
        
        # Combine scores: more similar segments reduce novelty
        return 1.0 - (max_similarity * (1 + coverage_factor)) / 2 