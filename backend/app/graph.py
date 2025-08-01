"""
Main LangGraph assembly for the research brief generator.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import GraphState
from app.nodes import (
    context_summarizer,
    planner,
    search_and_fetch,
    per_source_summarizer,
    synthesizer,
    error_handler
)

logger = logging.getLogger(__name__)


def should_summarize_context(state: GraphState) -> str:
    """
    Determine whether to summarize context or go directly to planning.
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    if state.get("is_follow_up") and state.get("history"):
        logger.info("Follow-up query with history detected, summarizing context")
        return "context_summarizer"
    else:
        logger.info("New query or no history, proceeding to planning")
        return "planner"


def should_continue_after_error(state: GraphState) -> str:
    """
    Determine whether to continue execution after an error.
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    if state.get("error"):
        logger.warning(f"Error detected: {state['error']}, handling error")
        return "error_handler"
    else:
        return "synthesizer"


def build_research_graph() -> StateGraph:
    """
    Build the research brief generation graph.
    
    Returns:
        Compiled LangGraph instance
    """
    logger.info("Building research brief generation graph")
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("context_summarizer", context_summarizer)
    workflow.add_node("planner", planner)
    workflow.add_node("search_and_fetch", search_and_fetch)
    workflow.add_node("per_source_summarizer", per_source_summarizer)
    workflow.add_node("synthesizer", synthesizer)
    workflow.add_node("error_handler", error_handler)
    
    # Add conditional edges from start
    workflow.add_conditional_edges(
        "__start__",
        should_summarize_context,
        {
            "context_summarizer": "context_summarizer",
            "planner": "planner"
        }
    )
    
    # Add edges from context summarizer to planner
    workflow.add_edge("context_summarizer", "planner")
    
    # Add edges for main workflow
    workflow.add_edge("planner", "search_and_fetch")
    workflow.add_edge("search_and_fetch", "per_source_summarizer")
    
    # Add conditional edge after summarization
    workflow.add_conditional_edges(
        "per_source_summarizer",
        should_continue_after_error,
        {
            "error_handler": "error_handler",
            "synthesizer": "synthesizer"
        }
    )
    
    # Add edges to end
    workflow.add_edge("synthesizer", END)
    workflow.add_edge("error_handler", END)
    
    logger.info("Research graph built successfully")
    return workflow


def create_graph_with_checkpointing() -> StateGraph:
    """
    Create the graph with checkpointing for resumable execution.
    
    Returns:
        Compiled graph with checkpointing
    """
    # Build the graph
    workflow = build_research_graph()
    
    # Compile the graph without checkpointing for now
    app = workflow.compile()
    
    logger.info("Research graph compiled without checkpointing")
    return app


# Global graph instance
research_graph = create_graph_with_checkpointing()


def get_graph_state_summary(state: GraphState) -> Dict[str, Any]:
    """
    Get a summary of the current graph state for monitoring.
    
    Args:
        state: Current graph state
        
    Returns:
        Summary dictionary
    """
    return {
        "topic": state.get("topic"),
        "user_id": state.get("user_id"),
        "is_follow_up": state.get("is_follow_up"),
        "has_plan": state.get("plan") is not None,
        "has_content": state.get("fetched_content") is not None,
        "content_count": len(state.get("fetched_content", [])),
        "has_summaries": state.get("summaries") is not None,
        "summary_count": len(state.get("summaries", [])),
        "has_final_brief": state.get("final_brief") is not None,
        "has_error": state.get("error") is not None,
        "error": state.get("error")
    } 