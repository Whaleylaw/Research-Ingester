"""Natural language query parser for the Zettelkasten database."""

from typing import Dict, List, Optional, Union

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class QueryIntent(BaseModel):
    """Structured representation of a query intent."""
    
    operation: str = Field(
        description="Type of search operation (keyword_search, tag_search, related_content, similarity_search)"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to search for in content"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags to filter by"
    )
    source_types: Optional[List[str]] = Field(
        default=None,
        description="Types of sources to search (pdf, video, audio, web)"
    )
    node_id: Optional[str] = Field(
        default=None,
        description="ID of a specific node to find related content"
    )
    only_new: Optional[bool] = Field(
        default=None,
        description="Whether to only return new information"
    )
    min_similarity: Optional[float] = Field(
        default=None,
        description="Minimum similarity score for related content"
    )

class NaturalLanguageQueryParser:
    """Parses natural language queries into structured search parameters."""
    
    def __init__(self):
        """Initialize the query parser."""
        from ..config import settings
        
        self.llm = ChatOpenAI(
            model_name=settings.DEFAULT_MODEL,
            temperature=0.1  # Low temperature for consistent parsing
        )
        self.parser = PydanticOutputParser(pydantic_object=QueryIntent)
        
        # Create the prompt template
        self.template = ChatPromptTemplate.from_messages([
            ("system", """You are a query parser for a Zettelkasten knowledge database. 
            Your task is to interpret natural language queries and convert them into structured search parameters.
            
            The database contains notes from various sources (PDFs, videos, audio, websites) with:
            - Tags and topics
            - Keywords and summaries
            - Links between related content
            - Novelty indicators (whether information is new or existing)
            
            Parse the user's query into appropriate search parameters.
            {format_instructions}"""),
            ("user", "{query}")
        ])
    
    async def parse_query(self, query: str) -> QueryIntent:
        """
        Parse a natural language query into structured search parameters.
        
        Args:
            query: Natural language query from user
        
        Returns:
            Structured query intent
        """
        # Format the prompt
        prompt = self.template.format_messages(
            query=query,
            format_instructions=self.parser.get_format_instructions()
        )
        
        # Get LLM response
        response = await self.llm.ainvoke(prompt)
        
        # Parse into structured format
        return self.parser.parse(response.content)

class QueryExecutor:
    """Executes parsed queries against the database."""
    
    def __init__(self, service):
        """
        Initialize the query executor.
        
        Args:
            service: ZettelkastenService instance
        """
        self.service = service
        self.parser = NaturalLanguageQueryParser()
    
    async def execute_query(self, query: str) -> Dict[str, Union[List[str], str]]:
        """
        Execute a natural language query.
        
        Args:
            query: Natural language query from user
        
        Returns:
            Query results with explanations
        """
        # Parse the query
        intent = await self.parser.parse_query(query)
        
        # Execute appropriate search based on intent
        if intent.operation == "keyword_search":
            results = await self.service.search_notes(
                keywords=intent.keywords,
                tags=intent.tags,
                source_types=intent.source_types,
                only_new=intent.only_new
            )
            explanation = f"Found {len(results)} notes matching your keywords"
            
        elif intent.operation == "tag_search":
            results = await self.service.search_notes(
                tags=intent.tags,
                source_types=intent.source_types,
                only_new=intent.only_new
            )
            explanation = f"Found {len(results)} notes with the specified tags"
            
        elif intent.operation == "related_content":
            if not intent.node_id:
                raise ValueError("Node ID required for finding related content")
            results = await self.service.get_related(
                intent.node_id,
                min_strength=intent.min_similarity or 0.5
            )
            explanation = f"Found {len(results)} related notes"
            
        elif intent.operation == "similarity_search":
            if not intent.node_id:
                raise ValueError("Node ID required for similarity search")
            results = await self.service.get_similar_content(
                intent.node_id,
                min_similarity=intent.min_similarity or 0.85
            )
            explanation = f"Found {len(results)} similar notes"
            
        else:
            raise ValueError(f"Unknown operation: {intent.operation}")
        
        # Format results
        formatted_results = []
        for note in results:
            formatted_results.append({
                "id": note.id,
                "title": note.title,
                "summary": note.summary,
                "tags": list(note.tags),
                "is_new": note.is_new_information,
                "confidence": note.confidence_score
            })
        
        return {
            "explanation": explanation,
            "results": formatted_results,
            "query_intent": intent.dict()
        } 