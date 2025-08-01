"""
LLM setup and configuration for the research brief generator using Google Generative AI.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import Type, TypeVar, Any
from pydantic import BaseModel
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)

# Validate settings on import
settings.validate()


def get_primary_llm() -> ChatGoogleGenerativeAI:
    """Get the primary LLM for complex reasoning tasks."""
    return ChatGoogleGenerativeAI(
        model=settings.PRIMARY_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        max_output_tokens=4000
    )


def get_secondary_llm() -> ChatGoogleGenerativeAI:
    """Get the secondary LLM for faster, simpler tasks."""
    return ChatGoogleGenerativeAI(
        model=settings.SECONDARY_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        max_output_tokens=2000
    )


T = TypeVar('T', bound=BaseModel)


def create_structured_llm(
    model_type: str,
    pydantic_class: Type[T],
    system_prompt: str = None
) -> Any:
    """
    Creates a LangChain runnable that will return a structured Pydantic object.

    Args:
        model_type: 'primary' or 'secondary'.
        pydantic_class: The Pydantic class for the output.
        system_prompt: The system prompt to guide the LLM.

    Returns:
        A LangChain runnable object.
    """
    if model_type == "primary":
        llm = get_primary_llm()
    else:
        llm = get_secondary_llm()

    # Use the structured output method for Google Generative AI
    structured_llm = llm.with_structured_output(pydantic_class)

    # Create a default system prompt if none provided
    if system_prompt is None:
        system_prompt = f"""You are an expert research assistant. Your task is to analyze the given input and provide a structured response in the format specified by the {pydantic_class.__name__} schema.

Please ensure your response is accurate, comprehensive, and follows the required structure."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    return prompt | structured_llm


def create_context_summarizer_prompt(context: str, topic: str) -> list:
    """Create a prompt for context summarization."""
    return [
        SystemMessage(content="""You are an expert research assistant. Your task is to summarize 
        previous research interactions to provide context for new research requests.
        
        Focus on:
        1. Key topics and findings from previous research
        2. User preferences and patterns
        3. How new research might build on previous work
        
        Be concise but comprehensive."""),
        HumanMessage(content=f"""
        Previous research context: {context}
        
        New research topic: {topic}
        
        Please provide a structured summary of the previous research context that would be 
        relevant for this new research topic.
        """)
    ]


def create_planning_prompt(topic: str, depth: str, context_summary: str = None) -> list:
    """Create a prompt for research planning."""
    context_part = f"\nPrevious research context: {context_summary}" if context_summary else ""
    
    return [
        SystemMessage(content="""You are an expert research planner. Your task is to create a 
        comprehensive research plan for a given topic.
        
        Consider:
        1. Multiple search angles and perspectives
        2. Different types of sources (academic, news, reports)
        3. Recent vs. historical information
        4. Specific focus areas within the topic
        
        Generate search queries that will yield diverse, high-quality sources."""),
        HumanMessage(content=f"""
        Research topic: {topic}
        Research depth: {depth}
        {context_part}
        
        Create a comprehensive research plan with search queries and rationale.
        """)
    ]


def create_summarization_prompt(topic: str, content: str, url: str) -> list:
    """Create a prompt for source summarization."""
    return [
        SystemMessage(content="""You are an expert research analyst. Your task is to summarize 
        web content in relation to a specific research topic.
        
        For each source:
        1. Extract the title and key information
        2. Summarize relevant content
        3. Assess relevance to the topic (0.0-1.0)
        4. Identify key points
        5. Note source type and metadata
        
        Be objective and focus on factual information."""),
        HumanMessage(content=f"""
        Research topic: {topic}
        Source URL: {url}
        
        Content to summarize:
        {content[:3000]}  # Limit content length
        
        Please provide a structured summary of this source.
        """)
    ]


def create_synthesis_prompt(topic: str, summaries: list, context_summary: str = None) -> list:
    """Create a prompt for final synthesis."""
    context_part = f"\nPrevious research context: {context_summary}" if context_summary else ""
    
    summaries_text = "\n\n".join([
        f"Source {i+1}: {summary.title}\nURL: {summary.url}\nSummary: {summary.summary}\n"
        f"Relevance: {summary.relevance_score}\nKey Points: {', '.join(summary.key_points)}"
        for i, summary in enumerate(summaries)
    ])
    
    return [
        SystemMessage(content="""You are an expert research analyst. Your task is to synthesize 
        multiple sources into a comprehensive research brief.
        
        Structure your response with:
        1. Executive Summary: High-level overview of findings
        2. Detailed Synthesis: Organized analysis of the research
        3. Key Insights: Main conclusions and implications
        4. References: All sources used
        
        Be thorough, objective, and well-organized."""),
        HumanMessage(content=f"""
        Research topic: {topic}
        {context_part}
        
        Source summaries:
        {summaries_text}
        
        Please create a comprehensive research brief synthesizing all sources.
        """)
    ] 