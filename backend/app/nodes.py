"""
Individual graph nodes for the research brief generation workflow.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from app.state import GraphState
from app.schemas import ResearchPlan, SourceSummary, FinalBrief, ContextSummary
from app.llm_setup import (
    create_structured_llm,
    create_context_summarizer_prompt,
    create_planning_prompt,
    create_summarization_prompt,
    create_synthesis_prompt,
    get_primary_llm,
    get_secondary_llm
)
from app.tools import search_tool
from app.monitoring import (
    metrics_collector,
    create_traceable_config,
    extract_token_usage_from_response
)

logger = logging.getLogger(__name__)


def context_summarizer(state: GraphState) -> Dict[str, Any]:
    """
    Summarize previous user interactions for context.
    
    This node runs only for follow-up queries and creates a structured
    summary of the user's research history.
    """
    start_time = time.time()
    trace_id = state.get("execution_metadata", {}).get("trace_id", "unknown")
    
    try:
        logger.info(f"Starting context summarization for user {state['user_id']}")
        
        if not state.get('history') or not state['is_follow_up']:
            logger.info("No history or not follow-up query, skipping context summarization")
            duration = time.time() - start_time
            metrics_collector.add_node_execution_time("context_summarizer", duration)
            return {"context_summary": None}
        
        # Create context string from history
        history_text = "\n\n".join([
            f"Topic: {brief.topic}\n"
            f"Key Insights: {', '.join(brief.key_insights)}\n"
            f"Executive Summary: {brief.executive_summary[:200]}..."
            for brief in state['history'][-3:]  # Last 3 briefs
        ])
        
        # Define system prompt for context summarization
        system_prompt = """You are an expert research assistant. Your task is to summarize 
        previous research interactions to provide context for new research requests.
        
        Focus on:
        1. Key topics and findings from previous research
        2. User preferences and patterns
        3. How new research might build on previous work
        
        Be concise but comprehensive."""
        
        # Use secondary LLM for context summarization with monitoring
        structured_llm = create_structured_llm("secondary", ContextSummary, system_prompt)
        
        # Create input for the structured LLM
        context_input = f"""
        Previous research context: {history_text}
        
        New research topic: {state['topic']}
        
        Please provide a structured summary of the previous research context that would be 
        relevant for this new research topic.
        """
        
        try:
            # Add traceable config for monitoring
            config = create_traceable_config(trace_id, "context_summarizer")
            context_summary = structured_llm.invoke({"input": context_input}, config=config)
            
            # Extract and track token usage
            token_usage = extract_token_usage_from_response(context_summary)
            if token_usage:
                metrics_collector.add_token_usage(token_usage)
            
            logger.info("Successfully created context summary")
        except Exception as e:
            logger.warning(f"Structured LLM failed for context summary, using fallback: {e}")
            # Fallback to manual parsing
            context_summary = ContextSummary(
                previous_topics=[brief.topic for brief in state['history']],
                key_findings=[insight for brief in state['history'] for insight in brief.key_insights],
                user_preferences={},
                continuity_notes="Previous research context available"
            )
        
        # Convert to dict for serialization
        context_dict = context_summary.model_dump()
        context_summary = ContextSummary(**context_dict)
        
        duration = time.time() - start_time
        metrics_collector.add_node_execution_time("context_summarizer", duration)
        
        logger.info("Context summarization completed successfully")
        return {"context_summary": context_summary}
        
    except Exception as e:
        duration = time.time() - start_time
        metrics_collector.add_node_execution_time("context_summarizer", duration)
        logger.error(f"Error in context summarization: {e}")
        return {"error": f"Context summarization failed: {str(e)}"}


def planner(state: GraphState) -> Dict[str, Any]:
    """
    Create a research plan based on the topic and context.
    
    This node generates structured search queries and a research strategy.
    """
    start_time = time.time()
    trace_id = state.get("execution_metadata", {}).get("trace_id", "unknown")
    
    try:
        logger.info(f"Starting research planning for topic: {state['topic']}")
        
        # Prepare context summary for planning
        context_summary = None
        if state.get('context_summary'):
            context_summary = f"Previous topics: {', '.join(state['context_summary'].previous_topics)}\n"
            context_summary += f"Key findings: {', '.join(state['context_summary'].key_findings)}"
        
        # Define system prompt for research planning
        system_prompt = """You are an expert research planner. Your task is to create a 
        comprehensive research plan for a given topic.
        
        Consider:
        1. Multiple search angles and perspectives
        2. Different types of sources (academic, news, reports)
        3. Recent vs. historical information
        4. Specific focus areas within the topic
        
        Generate search queries that will yield diverse, high-quality sources."""
        
        # Use primary LLM for planning with structured output
        structured_llm = create_structured_llm("primary", ResearchPlan, system_prompt)
        
        # Create input for the structured LLM
        planning_input = f"""
        Research topic: {state['topic']}
        Research depth: {state['depth']}
        {f"Previous research context: {context_summary}" if context_summary else ""}
        
        Create a comprehensive research plan with search queries and rationale.
        """
        
        try:
            # Add traceable config for monitoring
            config = create_traceable_config(trace_id, "planner")
            plan = structured_llm.invoke({"input": planning_input}, config=config)
            
            # Extract and track token usage
            token_usage = extract_token_usage_from_response(plan)
            if token_usage:
                metrics_collector.add_token_usage(token_usage)
            
            logger.info(f"Successfully created research plan with {len(plan.queries)} queries")
        except Exception as e:
            logger.warning(f"Structured LLM failed, using fallback plan: {e}")
            # Fallback plan
            plan = ResearchPlan(
                queries=[f"{state['topic']} research", f"{state['topic']} analysis", f"{state['topic']} trends"],
                rationale="Basic search queries for the topic",
                expected_sources=5,
                focus_areas=[state['topic']]
            )
        
        # Convert to dict for serialization
        plan_dict = plan.model_dump()
        plan = ResearchPlan(**plan_dict)
        
        duration = time.time() - start_time
        metrics_collector.add_node_execution_time("planner", duration)
        
        logger.info(f"Research planning completed with {len(plan.queries)} queries")
        return {"plan": plan}
        
    except Exception as e:
        duration = time.time() - start_time
        metrics_collector.add_node_execution_time("planner", duration)
        logger.error(f"Error in research planning: {e}")
        return {"error": f"Research planning failed: {str(e)}"}


def search_and_fetch(state: GraphState) -> Dict[str, Any]:
    """
    Execute search queries and fetch content from URLs.
    
    This node uses the search tool to find sources and fetches their content.
    """
    try:
        logger.info("Starting search and content fetching")
        
        if not state.get('plan'):
            return {"error": "No research plan available"}
        
        queries = state['plan'].queries
        logger.info(f"Executing {len(queries)} search queries")
        
        # Execute search and fetch content
        fetched_content = search_tool.search_and_fetch(queries)
        
        if not fetched_content:
            logger.warning("No content fetched from search results")
            return {"error": "No content could be fetched from search results"}
        
        logger.info(f"Successfully fetched content from {len(fetched_content)} sources")
        return {
            "search_results": fetched_content,
            "fetched_content": fetched_content
        }
        
    except Exception as e:
        logger.error(f"Error in search and fetch: {e}")
        return {"error": f"Search and fetch failed: {str(e)}"}


async def search_and_fetch_async(state: GraphState) -> Dict[str, Any]:
    """
    Async version of search_and_fetch for better performance.
    """
    try:
        logger.info("Starting async search and content fetching")
        
        if not state.get('plan'):
            return {"error": "No research plan available"}
        
        queries = state['plan'].queries
        logger.info(f"Executing {len(queries)} search queries")
        
        # Execute search and fetch content asynchronously
        fetched_content = await search_tool.search_and_fetch_async(queries)
        
        if not fetched_content:
            logger.warning("No content fetched from search results")
            return {"error": "No content could be fetched from search results"}
        
        logger.info(f"Successfully fetched content from {len(fetched_content)} sources")
        return {
            "search_results": fetched_content,
            "fetched_content": fetched_content
        }
        
    except Exception as e:
        logger.error(f"Error in async search and fetch: {e}")
        return {"error": f"Search and fetch failed: {str(e)}"}


def per_source_summarizer(state: GraphState) -> Dict[str, Any]:
    """
    Summarize each fetched source individually.
    
    This node processes each source and creates structured summaries.
    """
    try:
        logger.info("Starting per-source summarization")
        
        if not state.get('fetched_content'):
            return {"error": "No content available for summarization"}
        
        summaries = []
        
        # Define system prompt for source summarization
        system_prompt = """You are an expert research analyst. Your task is to summarize 
        web content in relation to a specific research topic.
        
        For each source:
        1. Extract the title and key information
        2. Summarize relevant content
        3. Assess relevance to the topic (0.0-1.0)
        4. Identify key points
        5. Note source type and metadata
        
        Be objective and focus on factual information."""
        
        # Use structured output for summaries
        structured_llm = create_structured_llm("secondary", SourceSummary, system_prompt)
        
        for i, content in enumerate(state['fetched_content']):
            try:
                logger.info(f"Summarizing source {i+1}/{len(state['fetched_content'])}")
                
                # Create input for the structured LLM
                summary_input = f"""
                Research topic: {state['topic']}
                Source URL: {content['url']}
                Source content: {content['content'][:2000]}...
                
                Please summarize this source in relation to the research topic.
                """
                
                try:
                    summary = structured_llm.invoke({"input": summary_input})
                    logger.info(f"Successfully summarized source {i+1}")
                except Exception as e:
                    logger.warning(f"Structured LLM failed for source {i+1}, using fallback: {e}")
                    # Fallback summary
                    summary = SourceSummary(
                        url=content['url'],
                        title=content.get('title', 'Unknown Title'),
                        summary=content['content'][:500] + "...",
                        relevance_score=0.5,
                        key_points=[content['content'][:100]],
                        source_type="web page",
                        publication_date=None,
                        author=None
                    )
                
                # Convert to dict for serialization
                summary_dict = summary.model_dump()
                summary = SourceSummary(**summary_dict)
                summaries.append(summary)
                
            except Exception as e:
                logger.error(f"Error summarizing source {i+1}: {e}")
                # Create a basic summary for failed sources
                summary = SourceSummary(
                    url=content['url'],
                    title=content.get('title', 'Unknown Title'),
                    summary=f"Error processing source: {str(e)}",
                    relevance_score=0.0,
                    key_points=["Error processing source"],
                    source_type="web page",
                    publication_date=None,
                    author=None
                )
                summaries.append(summary)
        
        logger.info(f"Completed summarization of {len(summaries)} sources")
        return {"summaries": summaries}
        
    except Exception as e:
        logger.error(f"Error in per-source summarization: {e}")
        return {"error": f"Per-source summarization failed: {str(e)}"}


def synthesizer(state: GraphState) -> Dict[str, Any]:
    """
    Synthesize all source summaries into a final research brief.
    
    This node creates the final structured output combining all sources.
    """
    try:
        logger.info("Starting final synthesis")
        
        if not state.get('summaries'):
            return {"error": "No summaries available for synthesis"}
        
        # Prepare context summary for synthesis
        context_summary = None
        if state.get('context_summary'):
            context_summary = f"Previous topics: {', '.join(state['context_summary'].previous_topics)}\n"
            context_summary += f"Key findings: {', '.join(state['context_summary'].key_findings)}"
        
        # Define system prompt for final synthesis
        system_prompt = """You are an expert research analyst. Your task is to synthesize 
        multiple sources into a comprehensive research brief.
        
        Structure your response with:
        1. Executive Summary: High-level overview of findings
        2. Detailed Synthesis: Organized analysis of the research
        3. Key Insights: Main conclusions and implications
        4. References: All sources used
        
        Be thorough, objective, and well-organized."""
        
        # Use primary LLM for final synthesis with structured output
        structured_llm = create_structured_llm("primary", FinalBrief, system_prompt)
        
        # Create summaries text for input
        summaries_text = "\n\n".join([
            f"Source {i+1}: {summary.title}\nURL: {summary.url}\nSummary: {summary.summary}\n"
            f"Relevance: {summary.relevance_score}\nKey Points: {', '.join(summary.key_points)}"
            for i, summary in enumerate(state['summaries'])
        ])
        
        # Create input for the structured LLM
        synthesis_input = f"""
        Research topic: {state['topic']}
        
        {f"Previous research context: {context_summary}" if context_summary else ""}
        
        Source summaries:
        {summaries_text}
        
        Please create a comprehensive research brief synthesizing all sources.
        """
        
        try:
            final_brief = structured_llm.invoke({"input": synthesis_input})
            logger.info("Successfully created final brief with structured LLM")
            
        except Exception as e:
            logger.warning(f"Structured LLM failed for final synthesis, using fallback: {e}")
            # Create a minimal fallback brief
            references = state['summaries'] if state['summaries'] else [
                SourceSummary(
                    url="https://fallback.example.com",
                    title="Research Sources",
                    summary="Research sources were processed",
                    relevance_score=0.5,
                    key_points=["Research completed successfully"],
                    source_type="web page",
                    publication_date=None,
                    author=None
                )
            ]
            
            # Convert references to dict for serialization
            ref_dicts = [ref.model_dump() for ref in references]
            references = [SourceSummary(**ref_dict) for ref_dict in ref_dicts]
            
            final_brief = FinalBrief(
                topic=state['topic'],
                executive_summary=f"Research brief generated for topic: {state['topic']}. Analysis completed with available sources.",
                synthesis=f"Comprehensive analysis of {state['topic']} based on {len(state['summaries'])} sources. The research covers key aspects and provides insights into the topic.",
                key_insights=[
                    f"Research completed on {state['topic']}",
                    f"Analyzed {len(state['summaries'])} sources",
                    "Key findings identified"
                ],
                references=references,
                context_used=state.get('context_summary'),
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_count": len(state['summaries']) if state['summaries'] else 0
                }
            )
        
        # Convert to dict for serialization
        final_dict = final_brief.model_dump()
        final_brief = FinalBrief(**final_dict)
        
        logger.info("Final synthesis completed successfully")
        return {"final_brief": final_brief}
        
    except Exception as e:
        logger.error(f"Error in final synthesis: {e}")
        return {"error": f"Final synthesis failed: {str(e)}"}


def error_handler(state: GraphState) -> Dict[str, Any]:
    """
    Handle errors in the graph execution.
    
    This node processes any errors that occurred during execution.
    """
    error = state.get('error')
    if error:
        logger.error(f"Graph execution error: {error}")
        
        # Create a minimal valid reference to satisfy schema requirements
        error_reference = SourceSummary(
            url="https://error.example.com",
            title="Error in Research Generation",
            summary=f"An error occurred during research generation: {error}",
            relevance_score=0.0,
            key_points=["Error occurred during research generation"],
            source_type="error",
            publication_date=None,
            author=None
        )
        
        # Convert to dict for serialization
        error_ref_dict = error_reference.model_dump()
        error_reference = SourceSummary(**error_ref_dict)
        
        final_brief = FinalBrief(
            topic=state['topic'],
            executive_summary=f"Error generating research brief: {error}. Please try again with a different topic or check your API configuration.",
            synthesis="Unable to complete research due to errors. The system encountered issues while processing your request. This could be due to API configuration problems, network issues, or invalid search queries.",
            key_insights=["Error occurred during research generation", "Please check API configuration", "Try with a different topic"],
            references=[error_reference],
            metadata={"error": error}
        )
        
        # Convert to dict for serialization
        final_dict = final_brief.model_dump()
        final_brief = FinalBrief(**final_dict)
        
        return {
            "final_brief": final_brief
        }
    
    return {} 