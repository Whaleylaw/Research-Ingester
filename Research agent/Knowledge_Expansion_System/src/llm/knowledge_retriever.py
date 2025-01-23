"""Knowledge retrieval and augmentation for LLM responses."""

from typing import Dict, List, Optional, Union

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from pydantic import BaseModel

from ..database.service import ZettelkastenService
from ..database.models import ZettelNode

class RelevantKnowledge(BaseModel):
    """Container for knowledge relevant to a query."""
    
    summaries: List[str]
    main_points: List[str]
    key_concepts: Dict[str, str]
    source_references: List[str]
    confidence: float

class KnowledgeEnhancedLLM:
    """LLM enhanced with Zettelkasten knowledge."""
    
    def __init__(self, service: ZettelkastenService):
        """
        Initialize the enhanced LLM.
        
        Args:
            service: ZettelkastenService instance
        """
        from ..config import settings
        
        self.service = service
        self.llm = ChatOpenAI(
            model_name=settings.DEFAULT_MODEL,
            temperature=settings.TEMPERATURE
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    async def _retrieve_relevant_knowledge(
        self,
        query: str,
        max_results: int = 5
    ) -> RelevantKnowledge:
        """
        Retrieve knowledge relevant to the query.
        
        Args:
            query: User's query
            max_results: Maximum number of relevant notes to retrieve
        
        Returns:
            Relevant knowledge from the database
        """
        # Search for relevant notes
        notes = await self.service.search_notes(
            keywords=query.split(),
            min_confidence=0.5
        )
        
        # Sort by confidence and take top results
        notes.sort(key=lambda x: x.confidence_score, reverse=True)
        top_notes = notes[:max_results]
        
        if not top_notes:
            return RelevantKnowledge(
                summaries=[],
                main_points=[],
                key_concepts={},
                source_references=[],
                confidence=0.0
            )
        
        # Combine knowledge from top notes
        combined_knowledge = RelevantKnowledge(
            summaries=[note.summary for note in top_notes],
            main_points=[
                point
                for note in top_notes
                for point in note.main_points
            ],
            key_concepts={
                k: v
                for note in top_notes
                for k, v in note.key_concepts.items()
            },
            source_references=[
                f"{note.title} ({note.source_type}): {note.source_path}"
                for note in top_notes
            ],
            confidence=sum(n.confidence_score for n in top_notes) / len(top_notes)
        )
        
        return combined_knowledge
    
    def _format_knowledge_context(self, knowledge: RelevantKnowledge) -> str:
        """Format retrieved knowledge into context for the LLM."""
        if not knowledge.summaries:
            return "No relevant knowledge found in the database."
        
        context = ["Here's relevant information from the knowledge base:"]
        
        # Add summaries
        context.append("\nSummaries:")
        for i, summary in enumerate(knowledge.summaries, 1):
            context.append(f"{i}. {summary}")
        
        # Add main points
        if knowledge.main_points:
            context.append("\nKey Points:")
            for point in knowledge.main_points:
                context.append(f"• {point}")
        
        # Add key concepts
        if knowledge.key_concepts:
            context.append("\nRelevant Concepts:")
            for concept, explanation in knowledge.key_concepts.items():
                context.append(f"• {concept}: {explanation}")
        
        # Add sources
        context.append("\nSources:")
        for source in knowledge.source_references:
            context.append(f"• {source}")
        
        return "\n".join(context)
    
    async def generate_response(
        self,
        query: str,
        include_sources: bool = True
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Generate a response enhanced with knowledge from the database.
        
        Args:
            query: User's query
            include_sources: Whether to include source references
        
        Returns:
            Enhanced response with sources
        """
        # Retrieve relevant knowledge
        knowledge = await self._retrieve_relevant_knowledge(query)
        context = self._format_knowledge_context(knowledge)
        
        # Create prompt template
        template = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable assistant with access to a Zettelkasten knowledge base.
            Use the provided information to give accurate and comprehensive answers.
            Always synthesize information from multiple sources when available.
            
            Knowledge Context:
            {context}
            
            Chat History:
            {chat_history}
            """),
            ("user", "{query}")
        ])
        
        # Format prompt
        prompt = template.format_messages(
            context=context,
            chat_history=self.memory.chat_memory.messages,
            query=query
        )
        
        # Get response from LLM
        response = await self.llm.ainvoke(prompt)
        
        # Update conversation memory
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(response.content)
        
        # Format response
        result = {
            "response": response.content,
            "confidence": knowledge.confidence
        }
        
        if include_sources and knowledge.source_references:
            result["sources"] = knowledge.source_references
        
        return result
    
    async def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear() 