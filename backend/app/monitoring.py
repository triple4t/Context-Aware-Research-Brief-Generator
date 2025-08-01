"""
Monitoring and observability for the research brief generator.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict

from langsmith import Client
from langsmith.run_helpers import traceable
from langchain_core.runnables import RunnableConfig

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics for a single operation."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    operation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionMetrics:
    """Execution metrics for a research brief generation."""
    trace_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    token_usage: List[TokenUsage] = field(default_factory=list)
    node_execution_times: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    success: bool = True
    
    def add_token_usage(self, usage: TokenUsage):
        """Add token usage to the metrics."""
        self.token_usage.append(usage)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all operations."""
        return sum(usage.total_tokens for usage in self.token_usage)
    
    def get_cost_estimate(self) -> float:
        """Estimate cost based on token usage (Azure OpenAI pricing)."""
        # Rough cost estimates for Azure OpenAI GPT-4o
        input_cost_per_1k = 0.005  # $0.005 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
        
        total_input = sum(usage.prompt_tokens for usage in self.token_usage)
        total_output = sum(usage.completion_tokens for usage in self.token_usage)
        
        input_cost = (total_input / 1000) * input_cost_per_1k
        output_cost = (total_output / 1000) * output_cost_per_1k
        
        return input_cost + output_cost


class LangSmithManager:
    """Manages LangSmith integration and tracing."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_enabled = False
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """Setup LangSmith client if API key is available."""
        api_key = settings.langsmith_api_key
        tracing_enabled = settings.langsmith_tracing_enabled
        
        if api_key and tracing_enabled:
            try:
                self.client = Client(
                    api_key=api_key,
                    api_url=settings.langsmith_endpoint
                )
                self.is_enabled = True
                logger.info(f"LangSmith tracing enabled with API key: {'LANGSMITH_API_KEY' if settings.LANGSMITH_API_KEY else 'LANGCHAIN_API_KEY'}")
                logger.info(f"LangSmith project: {settings.langsmith_project}")
                logger.info(f"LangSmith endpoint: {settings.langsmith_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
                self.is_enabled = False
        else:
            if not api_key:
                logger.info("LangSmith tracing disabled - no API key found")
            if not tracing_enabled:
                logger.info("LangSmith tracing disabled - tracing not enabled")
            self.is_enabled = False
    
    def get_trace_url(self, run_id: str) -> Optional[str]:
        """Generate trace URL for a run ID."""
        if not self.is_enabled or not self.client:
            return None
        
        try:
            # Construct the trace URL
            project_id = settings.langsmith_project
            return f"https://smith.langchain.com/o/{project_id}/r/{run_id}"
        except Exception as e:
            logger.warning(f"Failed to generate trace URL: {e}")
            return None
    
    def get_run_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific run."""
        if not self.is_enabled or not self.client:
            return None
        
        try:
            run = self.client.read_run(run_id)
            return {
                "run_id": run_id,
                "name": run.name,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "latency": run.latency.total_seconds() if run.latency else None,
                "token_usage": run.extra.get("token_usage", {}) if run.extra else {},
                "error": run.error if run.error else None
            }
        except Exception as e:
            logger.warning(f"Failed to get run metrics: {e}")
            return None


class MetricsCollector:
    """Collects and manages execution metrics."""
    
    def __init__(self):
        self.current_metrics: Optional[ExecutionMetrics] = None
        self.langsmith_manager = LangSmithManager()
    
    @contextmanager
    def track_execution(self, trace_id: str):
        """Context manager to track execution metrics."""
        start_time = datetime.utcnow()
        self.current_metrics = ExecutionMetrics(
            trace_id=trace_id,
            start_time=start_time
        )
        
        try:
            yield self.current_metrics
        finally:
            self.current_metrics.end_time = datetime.utcnow()
            if self.current_metrics.start_time:
                self.current_metrics.total_duration = (
                    self.current_metrics.end_time - self.current_metrics.start_time
                ).total_seconds()
    
    def add_token_usage(self, usage: TokenUsage):
        """Add token usage to current metrics."""
        if self.current_metrics:
            self.current_metrics.add_token_usage(usage)
    
    def add_node_execution_time(self, node_name: str, duration: float):
        """Add node execution time to metrics."""
        if self.current_metrics:
            self.current_metrics.node_execution_times[node_name] = duration
    
    def get_trace_url(self, run_id: str) -> Optional[str]:
        """Get trace URL for a run."""
        return self.langsmith_manager.get_trace_url(run_id)
    
    def get_current_metrics(self) -> Optional[ExecutionMetrics]:
        """Get current execution metrics."""
        return self.current_metrics


# Global metrics collector
metrics_collector = MetricsCollector()


def create_traceable_config(trace_id: str, node_name: str) -> RunnableConfig:
    """Create a traceable configuration for LangChain operations."""
    config = RunnableConfig(
        tags=[node_name, "research-brief"],
        metadata={
            "trace_id": trace_id,
            "node": node_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    if metrics_collector.langsmith_manager.is_enabled:
        config["run_name"] = f"{node_name}_{trace_id}"
    
    return config


def extract_token_usage_from_response(response: Any) -> Optional[TokenUsage]:
    """Extract token usage from LLM response."""
    try:
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            return TokenUsage(
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0),
                model=getattr(response, 'model', 'unknown'),
                operation="llm_call"
            )
        elif hasattr(response, 'generations') and response.generations:
            # Handle case where usage is in generations
            for gen in response.generations:
                if hasattr(gen[0], 'generation_info') and gen[0].generation_info:
                    usage = gen[0].generation_info.get('usage', {})
                    return TokenUsage(
                        prompt_tokens=usage.get('prompt_tokens', 0),
                        completion_tokens=usage.get('completion_tokens', 0),
                        total_tokens=usage.get('total_tokens', 0),
                        model=getattr(response, 'model', 'unknown'),
                        operation="llm_call"
                    )
    except Exception as e:
        logger.warning(f"Failed to extract token usage: {e}")
    
    return None


def log_execution_metrics(metrics: ExecutionMetrics):
    """Log execution metrics."""
    logger.info(f"Execution completed - Trace ID: {metrics.trace_id}")
    if metrics.total_duration is not None:
        logger.info(f"Total duration: {metrics.total_duration:.2f}s")
    else:
        logger.info("Total duration: Not available")
    logger.info(f"Total tokens: {metrics.get_total_tokens()}")
    logger.info(f"Estimated cost: ${metrics.get_cost_estimate():.4f}")
    logger.info(f"Node execution times: {metrics.node_execution_times}")
    
    if metrics.token_usage:
        for usage in metrics.token_usage:
            logger.info(f"Token usage - {usage.operation}: {usage.total_tokens} tokens "
                       f"({usage.prompt_tokens} prompt, {usage.completion_tokens} completion)")


def create_monitoring_middleware():
    """Create middleware for monitoring graph execution."""
    def middleware(state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """Middleware to track execution metrics."""
        trace_id = state.get("execution_metadata", {}).get("trace_id", "unknown")
        node_name = config.get("metadata", {}).get("node", "unknown")
        
        # Track node execution time
        start_time = time.time()
        
        # Add traceable config
        config.update(create_traceable_config(trace_id, node_name))
        
        return state
    
    return middleware 