"""Interactive chat interface for the knowledge-enhanced LLM."""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ..database.service import ZettelkastenService
from ..llm.knowledge_retriever import KnowledgeEnhancedLLM

console = Console()

class ChatInterface:
    """Interactive chat interface."""
    
    def __init__(self):
        """Initialize the chat interface."""
        self.service = None
        self.llm = None
    
    async def setup(self):
        """Set up required services."""
        self.service = ZettelkastenService()
        await self.service.setup()
        self.llm = KnowledgeEnhancedLLM(self.service)
    
    async def cleanup(self):
        """Clean up resources."""
        if self.service:
            await self.service.close()
    
    def display_welcome(self):
        """Display welcome message."""
        console.print(Panel(
            "[bold blue]Knowledge-Enhanced Chat Interface[/bold blue]\n\n"
            "Ask questions or have a conversation. The system will enhance its "
            "responses with knowledge from the Zettelkasten database.\n\n"
            "Commands:\n"
            "- /help: Show this help message\n"
            "- /clear: Clear conversation history\n"
            "- /quit: Exit the chat\n"
            "- /sources on|off: Toggle source references",
            title="Welcome",
            border_style="blue"
        ))
    
    def display_help(self):
        """Display help information."""
        console.print(Panel(
            "Example queries:\n\n"
            "1. Questions about stored knowledge:\n"
            "   - What do we know about machine learning?\n"
            "   - Summarize our knowledge about climate change\n"
            "   - What are the key concepts in quantum computing?\n\n"
            "2. Analysis and synthesis:\n"
            "   - Compare different approaches to neural networks\n"
            "   - What are the main challenges in renewable energy?\n"
            "   - How has AI evolved according to our sources?\n\n"
            "3. Source-specific queries:\n"
            "   - What have we learned from research papers about X?\n"
            "   - What do video tutorials say about Python?\n"
            "   - Compare academic and practical sources on Y\n\n"
            "Commands:\n"
            "- /help: Show this help\n"
            "- /clear: Clear chat history\n"
            "- /quit: Exit chat\n"
            "- /sources on|off: Toggle source display",
            title="Help",
            border_style="green"
        ))
    
    async def handle_command(self, command: str, show_sources: bool) -> Optional[bool]:
        """
        Handle special commands.
        
        Returns:
            New show_sources value or None if not a command
        """
        if command == "/help":
            self.display_help()
            return show_sources
        elif command == "/clear":
            await self.llm.clear_memory()
            console.print("[yellow]Conversation history cleared[/yellow]")
            return show_sources
        elif command == "/quit":
            return None
        elif command.startswith("/sources"):
            parts = command.split()
            if len(parts) == 2 and parts[1] in ("on", "off"):
                show_sources = parts[1] == "on"
                console.print(f"[yellow]Source display turned {parts[1]}[/yellow]")
                return show_sources
        return show_sources
    
    def format_response(self, response: dict, show_sources: bool):
        """Format and display the response."""
        # Display the main response
        console.print("\n[bold green]Assistant:[/bold green]")
        console.print(Markdown(response["response"]))
        
        # Display confidence
        confidence = response.get("confidence", 0)
        color = "green" if confidence > 0.8 else "yellow" if confidence > 0.5 else "red"
        console.print(f"\n[{color}]Confidence: {confidence:.2f}[/{color}]")
        
        # Display sources if enabled
        if show_sources and "sources" in response:
            console.print("\n[bold blue]Sources:[/bold blue]")
            for source in response["sources"]:
                console.print(f"• {source}")
    
    async def chat_loop(self):
        """Main chat loop."""
        show_sources = True
        
        self.display_welcome()
        console.print()
        
        while True:
            # Get user input
            query = Prompt.ask("[bold blue]You[/bold blue]")
            
            # Handle commands
            result = await self.handle_command(query, show_sources)
            if result is None:
                break
            elif result is not show_sources:
                show_sources = result
                continue
            
            try:
                # Generate and display response
                response = await self.llm.generate_response(
                    query,
                    include_sources=show_sources
                )
                self.format_response(response, show_sources)
                
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            
            console.print()

@click.command()
def chat():
    """Start the interactive chat interface."""
    interface = ChatInterface()
    
    async def run():
        try:
            await interface.setup()
            await interface.chat_loop()
        finally:
            await interface.cleanup()
    
    asyncio.run(run())

if __name__ == "__main__":
    chat() 