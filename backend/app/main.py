"""
FastAPI application for the research brief generator using Azure OpenAI.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from app.schemas import (
    BriefRequest, 
    BriefResponse, 
    ErrorResponse, 
    FinalBrief,
    ResearchDepth
)
from app.graph import research_graph, get_graph_state_summary
from app.storage import storage
from app.config import settings
from app.monitoring import metrics_collector, log_execution_metrics

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Context-Aware Research Brief Generator (Azure OpenAI)",
    description="A production-grade research assistant system that generates structured, evidence-linked research briefs using LangGraph and LangChain with Azure OpenAI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Research Brief Generator API (Azure OpenAI)")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"LangSmith tracing: {settings.LANGCHAIN_TRACING_V2}")
    
    # Log LangSmith configuration
    if settings.LANGSMITH_API_KEY:
        logger.info("LangSmith API key: LANGSMITH_API_KEY configured")
    elif settings.LANGCHAIN_API_KEY:
        logger.info("LangSmith API key: LANGCHAIN_API_KEY configured")
    else:
        logger.info("LangSmith API key: Not configured")
    
    logger.info(f"LangSmith project: {settings.LANGCHAIN_PROJECT}")
    logger.info(f"Google API Key: {'Configured' if settings.GOOGLE_API_KEY else 'Not configured'}")
    logger.info(f"Database: SQLite ({settings.DATABASE_URL})")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Context-Aware Research Brief Generator API (Google Generative AI)",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "llm_provider": "Google Generative AI",
        "storage": "SQLite",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.monitoring import metrics_collector
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "llm_provider": "Google Generative AI",
        "storage": "SQLite",
        "langsmith": {
            "enabled": metrics_collector.langsmith_manager.is_enabled,
            "tracing": settings.LANGCHAIN_TRACING_V2,
            "api_key_configured": bool(settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY),
            "project": settings.LANGCHAIN_PROJECT
        }
    }


@app.post("/brief", response_model=BriefResponse)
async def generate_brief(request: BriefRequest, background_tasks: BackgroundTasks):
    """
    Generate a research brief for the given topic using Google Generative AI.
    
    This endpoint orchestrates the entire research brief generation process
    using LangGraph with context-aware processing for follow-up queries.
    """
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting brief generation for user {request.user_id}, topic: {request.topic}")
        
        # Get user history for context
        history = storage.get_user_history(request.user_id, limit=5)
        
        # Prepare initial state
        initial_state = {
            "topic": request.topic,
            "user_id": request.user_id,
            "depth": request.depth.value,
            "is_follow_up": request.follow_up,
            "additional_context": request.additional_context,
            "history": history,
            "context_summary": None,
            "plan": None,
            "search_results": None,
            "fetched_content": None,
            "summaries": None,
            "final_brief": None,
            "error": None,
            "execution_metadata": {
                "trace_id": trace_id,
                "start_time": start_time,
                "request_id": str(uuid.uuid4()),
                "llm_provider": "Google Generative AI"
            }
        }
        
        # Track execution with monitoring
        with metrics_collector.track_execution(trace_id) as metrics:
            # Execute the research graph
            logger.info(f"Executing research graph with trace ID: {trace_id}")
            
            final_brief = None
            execution_events = []
            
            async for event in research_graph.astream(initial_state):
                # Log execution progress
                for node_name, node_output in event.items():
                    if node_name != "__end__":
                        logger.info(f"Node {node_name} completed")
                        execution_events.append({
                            "node": node_name,
                            "timestamp": time.time(),
                            "has_error": "error" in node_output
                        })
                        
                        # Check for final brief
                        if "final_brief" in node_output:
                            final_brief = node_output["final_brief"]
            
            if not final_brief:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate research brief"
                )
            
            # Save brief to storage
            background_tasks.add_task(
                storage.save_brief,
                request.user_id,
                request,
                final_brief
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Get trace URL and token usage
            trace_url = None
            token_usage = None
            
            if metrics_collector.langsmith_manager.is_enabled:
                # Try to get trace URL from the last run
                trace_url = metrics_collector.get_trace_url(trace_id)
            
            if metrics.token_usage:
                token_usage = {
                    "total_tokens": metrics.get_total_tokens(),
                    "total_cost_estimate": metrics.get_cost_estimate(),
                    "operations": [
                        {
                            "operation": usage.operation,
                            "model": usage.model,
                            "prompt_tokens": usage.prompt_tokens,
                            "completion_tokens": usage.completion_tokens,
                            "total_tokens": usage.total_tokens
                        }
                        for usage in metrics.token_usage
                    ]
                }
            
            # Log execution metrics
            log_execution_metrics(metrics)
            
            # Prepare response
            response = BriefResponse(
                brief=final_brief,
                execution_time=execution_time,
                token_usage=token_usage,
                trace_url=trace_url
            )
            
            logger.info(f"Brief generation completed in {execution_time:.2f}s")
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating brief: {e}")
        execution_time = time.time() - start_time
        
        error_response = ErrorResponse(
            error="Failed to generate research brief",
            details={"original_error": str(e)},
            trace_id=trace_id
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )


@app.get("/brief/{brief_id}", response_model=FinalBrief)
async def get_brief(brief_id: int):
    """
    Retrieve a specific research brief by ID.
    
    This endpoint allows retrieving previously generated briefs
    from the storage system.
    """
    try:
        brief = storage.get_brief_by_id(brief_id)
        if not brief:
            raise HTTPException(
                status_code=404,
                detail=f"Brief with ID {brief_id} not found"
            )
        
        return brief
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving brief {brief_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve brief"
        )


@app.get("/user/{user_id}/history")
async def get_user_history(user_id: str, limit: int = 10):
    """
    Get research history for a specific user.
    
    Returns a list of previous research briefs for the user,
    useful for understanding their research patterns and context.
    """
    try:
        history = storage.get_user_history(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "briefs": history,
            "total_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving history for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user history"
        )


@app.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """
    Get statistics for a specific user.
    
    Returns usage statistics and metrics for the user's
    research brief generation activity.
    """
    try:
        stats = storage.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user statistics"
        )


@app.delete("/user/{user_id}")
async def delete_user_data(user_id: str):
    """
    Delete all data for a specific user.
    
    This endpoint allows users to request deletion of their
    research history and associated data.
    """
    try:
        success = storage.delete_user_briefs(user_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete user data"
            )
        
        return {
            "message": f"Successfully deleted all data for user {user_id}",
            "user_id": user_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting data for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user data"
        )


@app.get("/models")
async def get_available_models():
    """
    Get information about available LLM models.
    
    Returns details about the models used in the system
    and their configurations.
    """
    return {
        "primary_model": {
            "name": settings.PRIMARY_MODEL,
            "provider": "Google Generative AI",
            "purpose": "Complex reasoning and synthesis"
        },
        "secondary_model": {
            "name": settings.SECONDARY_MODEL,
            "provider": "Google Generative AI",
            "purpose": "Fast summarization and context processing"
        },
        "search_tool": {
            "name": "Tavily Search",
            "purpose": "Web search and content discovery"
        }
    }


@app.get("/config")
async def get_configuration():
    """
    Get current system configuration.
    
    Returns non-sensitive configuration information
    useful for debugging and monitoring.
    """
    return {
        "environment": settings.ENVIRONMENT,
        "langsmith_enabled": settings.LANGCHAIN_TRACING_V2,
        "langsmith_configured": bool(settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY),
        "llm_provider": "Google Generative AI",
        "google_api_key_configured": bool(settings.GOOGLE_API_KEY),
        "storage": "SQLite",
        "database_url": settings.DATABASE_URL,
        "max_sources_per_query": settings.MAX_SOURCES_PER_QUERY,
        "max_content_length": settings.MAX_CONTENT_LENGTH,
        "request_timeout": settings.REQUEST_TIMEOUT
    }


@app.get("/monitoring/status")
async def get_monitoring_status():
    """
    Get monitoring and observability status.
    
    Returns information about LangSmith integration,
    tracing capabilities, and monitoring setup.
    """
    return {
        "langsmith_enabled": metrics_collector.langsmith_manager.is_enabled,
        "tracing_configured": settings.LANGCHAIN_TRACING_V2,
        "api_key_configured": bool(settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY),
        "project": settings.LANGCHAIN_PROJECT,
        "endpoint": settings.LANGCHAIN_ENDPOINT,
        "capabilities": {
            "trace_urls": metrics_collector.langsmith_manager.is_enabled,
            "token_tracking": True,
            "cost_estimation": True,
            "execution_metrics": True
        }
    }


@app.get("/monitoring/metrics/{trace_id}")
async def get_execution_metrics(trace_id: str):
    """
    Get execution metrics for a specific trace ID.
    
    Returns detailed metrics including token usage,
    execution times, and cost estimates.
    """
    try:
        # Try to get metrics from LangSmith
        run_metrics = metrics_collector.langsmith_manager.get_run_metrics(trace_id)
        
        if run_metrics:
            return {
                "trace_id": trace_id,
                "source": "langsmith",
                "metrics": run_metrics
            }
        else:
            return {
                "trace_id": trace_id,
                "source": "local",
                "message": "Metrics not available for this trace ID"
            }
            
    except Exception as e:
        logger.error(f"Error retrieving metrics for trace {trace_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve execution metrics"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    ) 