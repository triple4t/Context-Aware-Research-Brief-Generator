"""
Command-line interface for the research brief generator using Azure OpenAI.
"""

import asyncio
import json
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from app.schemas import BriefRequest, ResearchDepth
from app.graph import research_graph
from app.storage import storage
from app.config import settings

# Create Typer app
cli_app = typer.Typer(
    name="research-brief",
    help="Context-Aware Research Brief Generator CLI (Azure OpenAI)",
    add_completion=False
)

# Rich console for better output
console = Console()


@cli_app.command()
def generate(
    topic: str = typer.Option(..., "--topic", "-t", help="The research topic"),
    user_id: str = typer.Option("cli-user", "--user", "-u", help="User ID for context"),
    depth: ResearchDepth = typer.Option(
        ResearchDepth.MODERATE, 
        "--depth", 
        "-d", 
        help="Research depth level"
    ),
    follow_up: bool = typer.Option(
        False, 
        "--follow-up", 
        help="Flag for follow-up query"
    ),
    additional_context: Optional[str] = typer.Option(
        None, 
        "--context", 
        "-c", 
        help="Additional context or requirements"
    ),
    output_file: Optional[str] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="Output file path (JSON format)"
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v", 
        help="Verbose output"
    )
):
    """
    Generate a research brief from the command line using Azure OpenAI.
    
    This command orchestrates the entire research brief generation process
    using the LangGraph workflow with context-aware processing.
    """
    try:
        # Validate environment
        if not all([settings.AZURE_OPENAI_API_KEY, settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_LLM_DEPLOYMENT_NAME, settings.TAVILY_API_KEY]):
            console.print(
                "[red]Error: Missing required API keys. Please check your .env file.[/red]"
            )
            console.print("Required keys: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_LLM_DEPLOYMENT_NAME, TAVILY_API_KEY")
            sys.exit(1)
        
        # Display startup information
        console.print(Panel.fit(
            f"[bold blue]Research Brief Generator (Azure OpenAI)[/bold blue]\n"
            f"Topic: [yellow]{topic}[/yellow]\n"
            f"User: [cyan]{user_id}[/cyan]\n"
            f"Depth: [green]{depth.value}[/green]\n"
            f"Follow-up: [{'green' if follow_up else 'red'}]{follow_up}[/]\n"
            f"LLM Provider: [blue]Azure OpenAI[/blue]\n"
            f"Storage: [cyan]SQLite[/cyan]",
            title="Configuration"
        ))
        
        # Create request
        request = BriefRequest(
            topic=topic,
            depth=depth,
            follow_up=follow_up,
            user_id=user_id,
            additional_context=additional_context
        )
        
        # Get user history
        history = storage.get_user_history(user_id, limit=5)
        if history and verbose:
            console.print(f"[dim]Found {len(history)} previous briefs for context[/dim]")
        
        # Prepare initial state
        initial_state = {
            "topic": topic,
            "user_id": user_id,
            "depth": depth.value,
            "is_follow_up": follow_up,
            "additional_context": additional_context,
            "history": history,
            "context_summary": None,
            "plan": None,
            "search_results": None,
            "fetched_content": None,
            "summaries": None,
            "final_brief": None,
            "error": None,
            "execution_metadata": {}
        }
        
        # Execute with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Generating research brief...", total=None)
            
            final_brief = None
            node_progress = {}
            
            async def execute_graph():
                nonlocal final_brief, node_progress
                
                # Add required configuration for LangGraph checkpointer
                config = {"configurable": {"thread_id": f"cli-{user_id}-{int(asyncio.get_event_loop().time())}"}}
                
                async for event in research_graph.astream(initial_state, config=config):
                    for node_name, node_output in event.items():
                        if node_name != "__end__":
                            if verbose:
                                progress.update(
                                    task, 
                                    description=f"Completed: {node_name}"
                                )
                            
                            node_progress[node_name] = "completed"
                            
                            # Check for final brief
                            if "final_brief" in node_output:
                                final_brief = node_output["final_brief"]
            
            # Run the graph
            asyncio.run(execute_graph())
        
        if not final_brief:
            console.print("[red]Error: Failed to generate research brief[/red]")
            sys.exit(1)
        
        # Display results
        console.print("\n[bold green]✅ Research Brief Generated Successfully![/bold green]\n")
        
        # Create summary table
        table = Table(title="Research Brief Summary")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Topic", final_brief.topic)
        table.add_row("Sources", str(len(final_brief.references)))
        table.add_row("Executive Summary", final_brief.executive_summary[:100] + "...")
        table.add_row("Key Insights", str(len(final_brief.key_insights)))
        table.add_row("Generated At", final_brief.generated_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("LLM Provider", "Azure OpenAI")
        table.add_row("Storage", "SQLite")
        
        console.print(table)
        
        # Display executive summary
        console.print("\n[bold]Executive Summary:[/bold]")
        console.print(Panel(final_brief.executive_summary, title="Summary"))
        
        # Display key insights
        console.print("\n[bold]Key Insights:[/bold]")
        for i, insight in enumerate(final_brief.key_insights, 1):
            console.print(f"{i}. {insight}")
        
        # Display sources
        console.print(f"\n[bold]Sources ({len(final_brief.references)}):[/bold]")
        for i, source in enumerate(final_brief.references, 1):
            console.print(f"{i}. [link={source.url}]{source.title}[/link]")
            console.print(f"   Relevance: {source.relevance_score:.2f}")
            console.print(f"   Summary: {source.summary[:100]}...")
            console.print()
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(final_brief.model_dump(), f, indent=2, default=str)
            
            console.print(f"[green]Brief saved to: {output_path}[/green]")
        
        # Save to storage
        storage.save_brief(user_id, request, final_brief)
        console.print("[dim]Brief saved to user history[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli_app.command()
def history(
    user_id: str = typer.Option("cli-user", "--user", "-u", help="User ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of briefs to show")
):
    """
    Show research history for a user.
    """
    try:
        history = storage.get_user_history(user_id, limit=limit)
        
        if not history:
            console.print(f"[yellow]No research history found for user {user_id}[/yellow]")
            return
        
        console.print(f"[bold]Research History for {user_id}[/bold]\n")
        
        table = Table()
        table.add_column("Date", style="cyan")
        table.add_column("Topic", style="white")
        table.add_column("Sources", style="green")
        table.add_column("Key Insights", style="yellow")
        
        for brief in history:
            table.add_row(
                brief.generated_at.strftime("%Y-%m-%d"),
                brief.topic,
                str(len(brief.references)),
                str(len(brief.key_insights))
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli_app.command()
def stats(
    user_id: str = typer.Option("cli-user", "--user", "-u", help="User ID")
):
    """
    Show statistics for a user.
    """
    try:
        stats = storage.get_user_stats(user_id)
        
        console.print(f"[bold]Statistics for {user_id}[/bold]\n")
        
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Briefs", str(stats["total_briefs"]))
        table.add_row("Recent Briefs (7 days)", str(stats["recent_briefs"]))
        if stats.get("user_created"):
            table.add_row("User Created", stats["user_created"])
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli_app.command()
def config():
    """
    Show current configuration.
    """
    console.print("[bold]Current Configuration[/bold]\n")
    
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Environment", settings.ENVIRONMENT)
    table.add_row("LLM Provider", "Azure OpenAI")
    table.add_row("Primary Model", settings.PRIMARY_MODEL)
    table.add_row("Secondary Model", settings.SECONDARY_MODEL)
    table.add_row("Azure OpenAI API Key", "Set" if settings.AZURE_OPENAI_API_KEY else "Not set")
    table.add_row("Storage", "SQLite")
    table.add_row("Database URL", settings.DATABASE_URL)
    table.add_row("LangSmith Tracing", str(settings.LANGCHAIN_TRACING_V2))
    table.add_row("LangSmith API Key", "Set" if (settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY) else "Not set")
    table.add_row("LangSmith Project", settings.LANGCHAIN_PROJECT)
    table.add_row("Max Sources per Query", str(settings.MAX_SOURCES_PER_QUERY))
    table.add_row("Max Content Length", str(settings.MAX_CONTENT_LENGTH))
    table.add_row("Request Timeout", str(settings.REQUEST_TIMEOUT))
    
    console.print(table)


@cli_app.command()
def monitoring():
    """
    Show monitoring and observability status.
    """
    from app.monitoring import metrics_collector
    
    console.print("[bold]Monitoring Status[/bold]\n")
    
    # LangSmith status
    langsmith_status = "✅ Enabled" if metrics_collector.langsmith_manager.is_enabled else "❌ Disabled"
    tracing_status = "✅ Enabled" if settings.langsmith_tracing_enabled else "❌ Disabled"
    
    # Check which API key is being used
    if settings.LANGSMITH_API_KEY:
        api_key_status = "✅ Set (LANGSMITH_API_KEY)"
        api_key_source = "LANGSMITH_API_KEY"
    elif settings.LANGCHAIN_API_KEY:
        api_key_status = "✅ Set (LANGCHAIN_API_KEY)"
        api_key_source = "LANGCHAIN_API_KEY"
    else:
        api_key_status = "❌ Not set"
        api_key_source = "None"
    
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="yellow")
    
    table.add_row("LangSmith Integration", langsmith_status, "")
    table.add_row("Tracing", tracing_status, "")
    table.add_row("API Key", api_key_status, api_key_source)
    table.add_row("Project", settings.langsmith_project, "")
    table.add_row("Endpoint", settings.langsmith_endpoint, "")
    table.add_row("Trace URLs", "✅ Available" if metrics_collector.langsmith_manager.is_enabled else "❌ Not available", "")
    table.add_row("Token Tracking", "✅ Available", "Real-time token usage tracking")
    table.add_row("Cost Estimation", "✅ Available", "Azure OpenAI pricing estimates")
    table.add_row("Execution Metrics", "✅ Available", "Node execution times and performance")
    
    console.print(table)
    
    # Show detailed configuration info
    console.print("\n[bold]Configuration Details:[/bold]")
    console.print(f"   LANGCHAIN_TRACING_V2: {settings.LANGCHAIN_TRACING_V2}")
    console.print(f"   LANGSMITH_API_KEY: {'Set' if settings.LANGSMITH_API_KEY else 'Not set'}")
    console.print(f"   LANGCHAIN_API_KEY: {'Set' if settings.LANGCHAIN_API_KEY else 'Not set'}")
    console.print(f"   LANGCHAIN_PROJECT: {settings.LANGCHAIN_PROJECT}")
    console.print(f"   LANGCHAIN_ENDPOINT: {settings.LANGCHAIN_ENDPOINT}")
    
    if not metrics_collector.langsmith_manager.is_enabled:
        console.print("\n[yellow]⚠️  LangSmith is not enabled. To enable monitoring:[/yellow]")
        console.print("1. Set LANGSMITH_API_KEY in your .env file")
        console.print("2. Set LANGCHAIN_TRACING_V2=true")
        console.print("3. Restart the application")
    else:
        console.print("\n[green]✅ LangSmith monitoring is properly configured![/green]")
        console.print("You can now generate research briefs and get trace URLs with token usage data.")


@cli_app.command()
def test():
    """
    Run a quick test to verify the system is working.
    """
    console.print("[bold]Testing Research Brief Generator (Azure OpenAI)[/bold]\n")
    
    # Test configuration
    console.print("1. Testing configuration...")
    try:
        settings.validate()
        console.print("   ✅ Configuration valid")
    except Exception as e:
        console.print(f"   ❌ Configuration error: {e}")
        return
    
    # Test LLM setup
    console.print("2. Testing Azure OpenAI setup...")
    try:
        from app.llm_setup import get_primary_llm, get_secondary_llm
        primary_llm = get_primary_llm()
        secondary_llm = get_secondary_llm()
        console.print("   ✅ Azure OpenAI setup successful")
    except Exception as e:
        console.print(f"   ❌ Azure OpenAI setup error: {e}")
        return
    
    # Test search tool
    console.print("3. Testing search tool...")
    try:
        from app.tools import search_tool
        console.print("   ✅ Search tool initialized")
    except Exception as e:
        console.print(f"   ❌ Search tool error: {e}")
        return
    
    # Test graph
    console.print("4. Testing graph setup...")
    try:
        from app.graph import research_graph
        console.print("   ✅ Research graph compiled")
    except Exception as e:
        console.print(f"   ❌ Graph error: {e}")
        return
    
    # Test storage
    console.print("5. Testing storage setup...")
    try:
        from app.storage import storage
        console.print("   ✅ SQLite storage initialized")
    except Exception as e:
        console.print(f"   ❌ Storage error: {e}")
        return
    
    console.print("\n[green]✅ All tests passed! System is ready.[/green]")


@cli_app.command()
def chat(
    user_id: str = typer.Option("chat-user", "--user", "-u", help="User ID for chat"),
    topic: str = typer.Option(None, "--topic", "-t", help="Initial topic to discuss"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Interactive chat mode for research discussions.
    
    This allows continuous conversation while maintaining research context.
    """
    console.print(Panel.fit(
        "[bold blue]Research Chat Mode[/bold blue]\n"
        f"User: [cyan]{user_id}[/cyan]\n"
        "Choose your research mode:",
        title="Chat Configuration"
    ))
    
    try:
        # Get user history
        history = storage.get_user_history(user_id, limit=5)
        if history:
            console.print(f"[dim]Found {len(history)} previous research briefs[/dim]")
        
        # Get conversation history for context
        conversations = storage.get_conversation_history(user_id, limit=10)
        if conversations:
            console.print(f"[dim]Found {len(conversations)} previous conversations[/dim]")
        
        # Show initial options
        console.print(f"\n[bold cyan]Available Options:[/bold cyan]")
        console.print(f"1. [green]Type 'brief'[/green] - Generate detailed context-aware research brief")
        console.print(f"2. [yellow]Ask any question[/yellow] - Get quick research responses")
        console.print(f"3. [blue]Type 'history'[/blue] - View your research history")
        console.print(f"4. [red]Type 'quit'[/red] - Exit chat mode")
        console.print(f"5. [purple]Type 'help'[/purple] - Show this menu")
        console.print(f"6. [orange]Type 'show [number]'[/orange] - Show full content of brief #")
        console.print(f"\n[dim]💡 Tip: For complex topics, use 'brief' for comprehensive research[/dim]")
        
        # Start chat loop
        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if user_input.lower() == 'history':
                    console.print("\n[bold]Research History:[/bold]")
                    for i, brief in enumerate(history, 1):
                        console.print(f"{i}. {brief.topic} ({len(brief.references)} sources)")
                    
                    # Also show recent conversation history
                    conversations = storage.get_conversation_history(user_id, limit=5)
                    if conversations:
                        console.print(f"\n[bold]Recent Conversations:[/bold]")
                        for i, conv in enumerate(conversations, 1):
                            console.print(f"{i}. Q: {conv['user_input'][:50]}...")
                            console.print(f"   A: {conv['bot_response'][:50]}...")
                            console.print(f"   Type: {conv['interaction_type']} | {conv['created_at']}")
                            console.print()
                    continue
                
                if user_input.lower() == 'help':
                    console.print(f"\n[bold cyan]Available Options:[/bold cyan]")
                    console.print(f"1. [green]Type 'brief'[/green] - Generate detailed context-aware research brief")
                    console.print(f"2. [yellow]Ask any question[/yellow] - Get quick research responses")
                    console.print(f"3. [blue]Type 'history'[/blue] - View your research history")
                    console.print(f"4. [red]Type 'quit'[/red] - Exit chat mode")
                    console.print(f"5. [purple]Type 'help'[/purple] - Show this menu")
                    console.print(f"6. [orange]Type 'show [number]'[/orange] - Show full content of brief #")
                    continue
                
                if user_input.lower().startswith('show '):
                    try:
                        brief_num = int(user_input.split()[1]) - 1
                        if 0 <= brief_num < len(history):
                            brief = history[brief_num]
                            console.print(f"\n[bold]Full Brief: {brief.topic}[/bold]")
                            console.print(f"[bold]Generated:[/bold] {brief.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                            console.print(f"[bold]Sources:[/bold] {len(brief.references)}")
                            
                            console.print(f"\n[bold]Executive Summary:[/bold]")
                            console.print(Panel(brief.executive_summary, title="Summary"))
                            
                            console.print(f"\n[bold]Key Insights:[/bold]")
                            for i, insight in enumerate(brief.key_insights, 1):
                                console.print(f"{i}. {insight}")
                            
                            console.print(f"\n[bold]Detailed Analysis:[/bold]")
                            console.print(Panel(brief.synthesis, title="Synthesis"))
                            
                            console.print(f"\n[bold]Sources:[/bold]")
                            for i, source in enumerate(brief.references, 1):
                                console.print(f"{i}. {source.title}")
                                console.print(f"   URL: {source.url}")
                                console.print(f"   Relevance: {source.relevance_score:.2f}")
                                console.print(f"   Summary: {source.summary[:100]}...")
                                console.print()
                        else:
                            console.print(f"[red]Brief #{brief_num + 1} not found. You have {len(history)} briefs.[/red]")
                    except (ValueError, IndexError):
                        console.print("[red]Usage: 'show [number]' (e.g., 'show 1')[/red]")
                    continue
                
                if user_input.lower() == 'brief':
                    topic_input = console.input("[bold green]Enter topic for full brief:[/bold green] ")
                    if topic_input.strip():
                        console.print(f"[dim]Generating full research brief for: {topic_input}[/dim]")
                        try:
                            # Create request for full brief generation
                            request = BriefRequest(
                                topic=topic_input,
                                depth=ResearchDepth.MODERATE,
                                follow_up=False,
                                user_id=user_id
                            )
                            
                            # Prepare initial state
                            initial_state = {
                                "topic": topic_input,
                                "user_id": user_id,
                                "depth": "moderate",
                                "is_follow_up": False,
                                "additional_context": None,
                                "history": history,
                                "context_summary": None,
                                "plan": None,
                                "search_results": None,
                                "fetched_content": None,
                                "summaries": None,
                                "final_brief": None,
                                "error": None,
                                "execution_metadata": {}
                            }
                            
                            # Execute the research graph
                            console.print("[dim]Executing research graph...[/dim]")
                            final_brief = None
                            
                            async def execute_brief():
                                nonlocal final_brief
                                async for event in research_graph.astream(initial_state):
                                    for node_name, node_output in event.items():
                                        if node_name != "__end__":
                                            if "final_brief" in node_output:
                                                final_brief = node_output["final_brief"]
                            
                            # Run the brief generation
                            asyncio.run(execute_brief())
                            
                            if final_brief:
                                console.print(f"[green]✅ Brief generated successfully![/green]")
                                console.print(f"[bold]Topic:[/bold] {final_brief.topic}")
                                console.print(f"[bold]Sources:[/bold] {len(final_brief.references)}")
                                console.print(f"[bold]Key Insights:[/bold] {len(final_brief.key_insights)}")
                                
                                # Display full executive summary
                                console.print(f"\n[bold]Executive Summary:[/bold]")
                                console.print(Panel(final_brief.executive_summary, title="Summary"))
                                
                                # Display key insights
                                console.print(f"\n[bold]Key Insights:[/bold]")
                                for i, insight in enumerate(final_brief.key_insights, 1):
                                    console.print(f"{i}. {insight}")
                                
                                # Display synthesis (main content)
                                console.print(f"\n[bold]Detailed Analysis:[/bold]")
                                console.print(Panel(final_brief.synthesis, title="Synthesis"))
                                
                                # Display sources
                                console.print(f"\n[bold]Sources ({len(final_brief.references)}):[/bold]")
                                for i, source in enumerate(final_brief.references, 1):
                                    console.print(f"{i}. [link={source.url}]{source.title}[/link]")
                                    console.print(f"   Relevance: {source.relevance_score:.2f}")
                                    console.print(f"   Summary: {source.summary[:100]}...")
                                    console.print()
                                
                                # Save to storage
                                storage.save_brief(user_id, request, final_brief)
                                console.print("[dim]Brief saved to history[/dim]")
                                
                                # Update history
                                history = storage.get_user_history(user_id, limit=5)
                            else:
                                console.print("[red]Failed to generate brief[/red]")
                                
                        except Exception as e:
                            console.print(f"[red]Error generating brief: {str(e)}[/red]")
                    continue
                
                if not user_input:
                    continue
                
                # Process as a quick research query
                console.print(f"\n[dim]Quick research on: {user_input}[/dim]")
                
                try:
                    # Handle special cases like date/time questions
                    if any(word in user_input.lower() for word in ['date', 'time', 'today', 'now', 'tomorrow', 'yesterday']):
                        from datetime import datetime, timedelta
                        current_time = datetime.now()
                        
                        # Handle different time references
                        if 'tomorrow' in user_input.lower():
                            tomorrow = current_time + timedelta(days=1)
                            response = f"Tomorrow will be {tomorrow.strftime('%B %d, %Y')} ({tomorrow.strftime('%A')})."
                        elif 'yesterday' in user_input.lower():
                            yesterday = current_time - timedelta(days=1)
                            response = f"Yesterday was {yesterday.strftime('%B %d, %Y')} ({yesterday.strftime('%A')})."
                        else:
                            response = f"Today's date is {current_time.strftime('%B %d, %Y')} ({current_time.strftime('%A')}) and the current time is {current_time.strftime('%I:%M %p')}."
                        
                        console.print(f"[bold green]Bot:[/bold green] {response}")
                        
                        # Show options
                        console.print(f"\n[bold cyan]Options:[/bold cyan]")
                        console.print(f"1. [yellow]Ask another question[/yellow] for quick responses")
                        console.print(f"2. [blue]Type 'history'[/blue] to see your research history")
                        console.print(f"3. [green]Type 'brief'[/green] to generate a research brief")
                        
                        # Save this interaction to conversation history
                        storage.save_conversation(user_id, user_input, response, "date_time")
                        
                        # Refresh conversation context for next interaction
                        conversations = storage.get_conversation_history(user_id, limit=10)
                        continue
                    
                    # Use LLM for quick response based on context
                    from app.llm_setup import get_secondary_llm
                    llm = get_secondary_llm()
                    
                    # Prepare context from history
                    context_text = ""
                    if history:
                        context_text = "\n\nPrevious research context:\n"
                        for brief in history[-3:]:  # Last 3 briefs for better context
                            context_text += f"- {brief.topic}: {brief.executive_summary[:200]}...\n"
                            context_text += f"  Key insights: {', '.join(brief.key_insights[:3])}\n"
                    
                    # Prepare conversation context
                    conversation_context = ""
                    if conversations:
                        conversation_context = "\n\nRecent conversation context:\n"
                        for conv in conversations[-5:]:  # Last 5 conversations
                            conversation_context += f"User: {conv['user_input']}\n"
                            conversation_context += f"Bot: {conv['bot_response'][:100]}...\n\n"
                    
                    # Check if question relates to previous research
                    research_keywords = ['research', 'study', 'analysis', 'trends', 'applications', 'technology', 'ai', 'ml', 'machine learning', 'artificial intelligence']
                    is_research_related = any(keyword in user_input.lower() for keyword in research_keywords)
                    
                    if is_research_related and history:
                        context_text += f"\nNote: The user's question appears related to previous research topics. Use this context to provide a more informed response."
                    
                    # Create prompt for quick response
                    prompt = f"""You are a helpful research assistant in an ongoing conversation. Provide a concise, informative response to the user's question.

{context_text}
{conversation_context}

User question: {user_input}

Instructions:
1. Answer the question accurately and concisely
2. If the question relates to previous research topics, reference that context
3. If the question refers to previous conversation, acknowledge that context
4. If the question is about current date/time, provide the correct current information
5. If this topic would benefit from a full research brief, mention that
6. Keep responses focused and relevant to the ongoing conversation"""
                    
                    # Get quick response
                    response = llm.invoke(prompt)
                    
                    # Extract only the content, not metadata
                    if hasattr(response, 'content'):
                        response_text = response.content
                    else:
                        response_text = str(response)
                    
                    console.print(f"[bold green]Bot:[/bold green] {response_text}")
                    
                    # Save this interaction to conversation history
                    storage.save_conversation(user_id, user_input, response_text, "chat")
                    
                    # Refresh conversation context for next interaction
                    conversations = storage.get_conversation_history(user_id, limit=10)
                    
                    # Always show options for full brief
                    console.print(f"\n[bold cyan]Options:[/bold cyan]")
                    console.print(f"1. [green]Type 'brief'[/green] to generate a comprehensive research brief on '{user_input}'")
                    console.print(f"2. [yellow]Ask another question[/yellow] for quick responses")
                    console.print(f"3. [blue]Type 'history'[/blue] to see your research history")
                    
                except Exception as e:
                    console.print(f"[red]Error in quick research: {str(e)}[/red]")
                    console.print(f"[bold green]Bot:[/bold green] I understand you're asking about '{user_input}'. "
                                f"Type 'brief' to generate a full research brief on this topic.")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Chat interrupted. Type 'quit' to exit.[/yellow]")
                continue
                
    except Exception as e:
        console.print(f"[red]Error in chat: {str(e)}[/red]")
        if verbose:
            console.print_exception()


@cli_app.command()
def quick_response(
    question: str = typer.Option(..., "--question", "-q", help="Quick research question"),
    user_id: str = typer.Option("test-user", "--user", "-u", help="User ID for context")
):
    """
    Get a quick response to a research question.
    """
    try:
        # Handle special cases like date/time questions
        if any(word in question.lower() for word in ['date', 'time', 'today', 'now']):
            from datetime import datetime
            current_time = datetime.now()
            console.print(f"[bold green]Quick Response:[/bold green] Today's date is {current_time.strftime('%B %d, %Y')} and the current time is {current_time.strftime('%I:%M %p')}.")
            
            # Show options
            console.print(f"\n[bold cyan]Options:[/bold cyan]")
            console.print(f"1. [yellow]Ask another question[/yellow] for quick responses")
            console.print(f"2. [green]Generate full brief[/green] on '{question}'")
            return
        
        # Get user history for context
        history = storage.get_user_history(user_id, limit=3)
        
        # Use LLM for quick response
        from app.llm_setup import get_secondary_llm
        llm = get_secondary_llm()
        
        # Prepare context from history
        context_text = ""
        if history:
            context_text = "\n\nPrevious research context:\n"
            for brief in history[-2:]:
                context_text += f"- {brief.topic}: {brief.executive_summary[:100]}...\n"
        
        # Create prompt
        prompt = f"""You are a helpful research assistant. Provide a concise, informative response to the user's question.

{context_text}

User question: {question}

Provide a helpful response based on your knowledge."""
        
        # Get response
        response = llm.invoke(prompt)
        
        # Extract only content
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        console.print(f"[bold green]Quick Response:[/bold green] {response_text}")
        
        # Show options
        console.print(f"\n[bold cyan]Options:[/bold cyan]")
        console.print(f"1. [green]Generate full brief[/green] on '{question}'")
        console.print(f"2. [yellow]Ask another question[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    cli_app() 