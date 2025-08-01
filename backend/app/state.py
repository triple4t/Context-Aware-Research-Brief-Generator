"""
Graph state definition for the research brief generator.
"""

from typing import List, TypedDict, Optional, Dict, Any
from app.schemas import ResearchPlan, SourceSummary, FinalBrief, ContextSummary


class GraphState(TypedDict):
    """
    Represents the state of our research brief generation graph.
    
    This state is passed between nodes and contains all the data
    needed for the research brief generation process.
    """
    # Input parameters
    topic: str
    user_id: str
    depth: str
    is_follow_up: bool
    additional_context: Optional[str]
    
    # User history and context
    history: List[FinalBrief]
    context_summary: Optional[ContextSummary]
    
    # Research planning
    plan: Optional[ResearchPlan]
    
    # Search and content fetching
    search_results: Optional[List[Dict[str, Any]]]
    fetched_content: Optional[List[Dict[str, Any]]]
    
    # Content processing
    summaries: Optional[List[SourceSummary]]
    
    # Final output
    final_brief: Optional[FinalBrief]
    
    # Error handling
    error: Optional[str]
    
    # Metadata for monitoring
    execution_metadata: Dict[str, Any] 