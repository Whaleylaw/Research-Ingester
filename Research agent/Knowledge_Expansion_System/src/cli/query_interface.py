"""Command-line interface for querying the Zettelkasten database."""

import asyncio
import json
from typing import Dict, List

import click
from rich.console import Console
from rich.table import Table

from ..database.query_parser import QueryExecutor
from ..database.service import ZettelkastenService

console = Console()

def format_table(results: List[Dict]) -> Table:
    """Format results as a rich table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Summary")
    table.add_column("Tags")
    table.add_column("New Info")
    table.add_column("Confidence")
    
    for result in results:
        table.add_row(
            result["id"],
            result["title"],
            result["summary"][:100] + "...",
            ", ".join(result["tags"]),
            "✓" if result["is_new"] else "✗",
            f"{result['confidence']:.2f}"
        )
    
    return table

async def setup_services():
    """Initialize required services."""
    service = ZettelkastenService()
    await service.setup()
    executor = QueryExecutor(service)
    return service, executor

@click.group()
def cli():
    """Zettelkasten Query Interface"""
    pass

@cli.command()
@click.argument('query')
def search(query: str):
    """Execute a natural language search query."""
    async def _search():
        try:
            # Set up services
            service, executor = await setup_services()
            
            try:
                # Execute query
                console.print("[bold blue]Executing query...[/bold blue]")
                results = await executor.execute_query(query)
                
                # Print explanation
                console.print(f"\n[bold green]{results['explanation']}[/bold green]\n")
                
                # Show interpreted query intent
                console.print("[bold yellow]Query Intent:[/bold yellow]")
                console.print(json.dumps(results["query_intent"], indent=2))
                
                # Show results table
                if results["results"]:
                    console.print("\n[bold]Results:[/bold]")
                    table = format_table(results["results"])
                    console.print(table)
                else:
                    console.print("\n[yellow]No results found[/yellow]")
                
            finally:
                await service.close()
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    # Run the async function
    asyncio.run(_search())

@cli.command()
@click.argument('note_id')
def explore(note_id: str):
    """Explore related content for a specific note."""
    async def _explore():
        try:
            # Set up services
            service, executor = await setup_services()
            
            try:
                # Get the note
                note = await service.get_note(note_id)
                if not note:
                    console.print("[bold red]Note not found[/bold red]")
                    return
                
                # Show note details
                console.print("\n[bold blue]Note Details:[/bold blue]")
                console.print(f"Title: {note.title}")
                console.print(f"Source: {note.source_type} ({note.source_path})")
                console.print(f"Tags: {', '.join(note.tags)}")
                console.print(f"Summary: {note.summary}")
                
                # Get related content
                related = await service.get_related(note_id)
                if related:
                    console.print("\n[bold green]Related Notes:[/bold green]")
                    table = format_table([{
                        "id": n.id,
                        "title": n.title,
                        "summary": n.summary,
                        "tags": list(n.tags),
                        "is_new": n.is_new_information,
                        "confidence": n.confidence_score
                    } for n in related])
                    console.print(table)
                else:
                    console.print("\n[yellow]No related content found[/yellow]")
                
                # Get similarity analysis
                novelty = await service.analyze_novelty(note_id)
                console.print("\n[bold magenta]Novelty Analysis:[/bold magenta]")
                console.print(json.dumps(novelty, indent=2))
                
            finally:
                await service.close()
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    # Run the async function
    asyncio.run(_explore())

@cli.command()
def suggest():
    """Get query suggestions and help."""
    console.print("\n[bold blue]Query Examples:[/bold blue]")
    console.print("""
1. Keyword Search:
   - "Find notes about machine learning and neural networks"
   - "Search for content related to climate change"
   - "Show me new information about quantum computing"

2. Tag Search:
   - "Find notes tagged with AI and robotics"
   - "Show content with tags: psychology, cognition"
   - "Get notes tagged as research papers"

3. Related Content:
   - "Find content similar to note <note_id>"
   - "Show me notes related to <note_id>"
   - "Get all content connected to <note_id>"

4. Source Type Filtering:
   - "Find video content about data science"
   - "Show me PDF documents about biology"
   - "Get audio recordings tagged with interviews"

5. Novelty Filtering:
   - "Show only new information about AI"
   - "Find recent unique content about space exploration"
   - "Get notes with high novelty scores"
    """)

if __name__ == "__main__":
    cli() 