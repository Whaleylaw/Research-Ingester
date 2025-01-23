"""Base LLM functionality for text processing."""

from typing import Dict, List, Optional

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Summary(BaseModel):
    """Structured summary of content."""
    main_points: List[str] = Field(description="Key points from the content")
    summary: str = Field(description="Concise summary of the content")
    topics: List[str] = Field(description="Main topics discussed")
    entities: List[str] = Field(description="Important named entities (people, organizations, etc.)")
    key_concepts: Dict[str, str] = Field(description="Key concepts and their brief explanations")

class LLMProcessor:
    """Handles LLM-based text processing operations."""
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """Initialize the LLM processor."""
        from ..config import settings
        
        self.llm = ChatOpenAI(
            model_name=model_name or settings.DEFAULT_MODEL,
            temperature=temperature or settings.TEMPERATURE
        )
        self.summary_parser = PydanticOutputParser(pydantic_object=Summary)
    
    async def summarize(self, text: str, max_length: Optional[int] = None) -> Summary:
        """
        Generate a structured summary of the text.
        
        Args:
            text: Text to summarize
            max_length: Optional maximum length for the summary
        
        Returns:
            Summary object containing structured summary data
        """
        # Create prompt template
        template = ChatPromptTemplate.from_messages([
            ("system", """You are a precise content summarizer. Analyze the following text and create a structured summary. 
            Focus on extracting key information and main concepts. Be concise but comprehensive.
            {format_instructions}"""),
            ("user", "{text}")
        ])
        
        # Format the prompt
        prompt = template.format_messages(
            format_instructions=self.summary_parser.get_format_instructions(),
            text=text[:max_length] if max_length else text
        )
        
        # Get response from LLM
        response = await self.llm.ainvoke(prompt)
        
        # Parse and return structured summary
        return self.summary_parser.parse(response.content)

    async def chunk_and_summarize(self, text: str, chunk_size: int = 4000) -> Summary:
        """
        Split long text into chunks and summarize each chunk before combining.
        
        Args:
            text: Long text to summarize
            chunk_size: Maximum size of each chunk
        
        Returns:
            Combined summary of all chunks
        """
        # Split text into chunks
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            summary = await self.summarize(chunk)
            chunk_summaries.append(summary)
        
        # Combine summaries
        combined_summary = Summary(
            main_points=list({point for summary in chunk_summaries for point in summary.main_points}),
            summary="\n".join(summary.summary for summary in chunk_summaries),
            topics=list({topic for summary in chunk_summaries for topic in summary.topics}),
            entities=list({entity for summary in chunk_summaries for entity in summary.entities}),
            key_concepts={k: v for summary in chunk_summaries for k, v in summary.key_concepts.items()}
        )
        
        # Generate final summary if needed
        if len(chunks) > 1:
            combined_text = "\n".join(summary.summary for summary in chunk_summaries)
            combined_summary = await self.summarize(combined_text)
        
        return combined_summary 