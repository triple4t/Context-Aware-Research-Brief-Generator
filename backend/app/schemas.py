"""
Pydantic schemas for structured outputs throughout the research brief generation process.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResearchDepth(str, Enum):
    """Research depth levels."""
    SHALLOW = "shallow"  # 3-5 sources
    MODERATE = "moderate"  # 5-8 sources
    DEEP = "deep"  # 8-12 sources


class ResearchPlan(BaseModel):
    """The structured plan for conducting research."""
    queries: List[str] = Field(
        description="Comprehensive list of search engine queries to answer the user's topic",
        min_length=1
    )
    rationale: str = Field(
        description="Brief explanation of why these queries were chosen and how they address the topic"
    )
    expected_sources: int = Field(
        description="Expected number of sources to gather",
        ge=1,
        le=15
    )
    focus_areas: List[str] = Field(
        description="Key areas to focus on during research"
    )


class SourceSummary(BaseModel):
    """A structured summary of a single data source."""
    url: str = Field(description="URL of the source")
    title: str = Field(description="Title of the source")
    summary: str = Field(
        description="A concise summary of the source content relevant to the main topic"
    )
    relevance_score: float = Field(
        description="A score from 0.0 to 1.0 indicating relevance to the topic",
        ge=0.0,
        le=1.0
    )
    key_points: List[str] = Field(
        description="Key points extracted from this source"
    )
    source_type: str = Field(description="Type of source (article, paper, report, etc.)")
    publication_date: Optional[str] = Field(description="Publication date if available")
    author: Optional[str] = Field(description="Author or organization if available")


class ContextSummary(BaseModel):
    """Summary of prior user interactions for context."""
    previous_topics: List[str] = Field(description="Topics from previous briefs")
    key_findings: List[str] = Field(description="Key findings from previous research")
    user_preferences: Dict[str, Any] = Field(
        description="Inferred user preferences based on history",
        default_factory=dict
    )
    continuity_notes: str = Field(
        description="Notes on how this new research relates to previous work"
    )


class FinalBrief(BaseModel):
    """The final, compiled research brief."""
    topic: str = Field(description="The original research topic")
    executive_summary: str = Field(
        description="A high-level summary of the research findings",
        min_length=50
    )
    synthesis: str = Field(
        description="A detailed synthesis of information from all sources, structured into logical sections"
    )
    key_insights: List[str] = Field(
        description="Key insights and conclusions from the research"
    )
    references: List[SourceSummary] = Field(
        description="A list of all summarized sources"
    )
    context_used: Optional[ContextSummary] = Field(
        default=None,
        description="Summary of prior interactions used for this brief"
    )
    metadata: Dict[str, Any] = Field(
        description="Additional metadata about the brief generation",
        default_factory=dict
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class BriefRequest(BaseModel):
    """Request model for generating a research brief."""
    topic: str = Field(
        description="The research topic",
        min_length=5
    )
    depth: ResearchDepth = Field(
        default=ResearchDepth.MODERATE,
        description="Research depth level"
    )
    follow_up: bool = Field(
        default=False,
        description="Whether this is a follow-up query"
    )
    user_id: str = Field(description="Unique identifier for the user")
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context or specific requirements"
    )


class BriefResponse(BaseModel):
    """Response model for the API."""
    brief: FinalBrief
    trace_url: Optional[str] = Field(
        default=None,
        description="Link to LangSmith trace for this execution"
    )
    execution_time: float = Field(description="Total execution time in seconds")
    token_usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Token usage statistics"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for debugging"
    ) 