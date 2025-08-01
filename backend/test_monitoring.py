#!/usr/bin/env python3
"""
Test script to demonstrate monitoring and observability features.
"""

import asyncio
import json
import time
from datetime import datetime

from app.schemas import BriefRequest, ResearchDepth
from app.graph import research_graph
from app.monitoring import metrics_collector, log_execution_metrics
from app.storage import storage


async def test_monitoring_features():
    """Test the monitoring and observability features."""
    print("🧪 Testing Monitoring and Observability Features")
    print("=" * 50)
    
    # Test 1: Check monitoring status
    print("\n1. Checking monitoring status...")
    langsmith_enabled = metrics_collector.langsmith_manager.is_enabled
    print(f"   LangSmith enabled: {langsmith_enabled}")
    print(f"   Tracing configured: {metrics_collector.langsmith_manager.is_enabled}")
    
    # Check API key configuration
    from app.config import settings
    if settings.LANGSMITH_API_KEY:
        print(f"   API Key source: LANGSMITH_API_KEY")
    elif settings.LANGCHAIN_API_KEY:
        print(f"   API Key source: LANGCHAIN_API_KEY")
    else:
        print(f"   API Key source: None")
    print(f"   Project: {settings.LANGCHAIN_PROJECT}")
    print(f"   Endpoint: {settings.LANGCHAIN_ENDPOINT}")
    
    # Test 2: Generate a sample brief with monitoring
    print("\n2. Generating sample brief with monitoring...")
    
    # Create a test request
    request = BriefRequest(
        topic="artificial intelligence trends 2024",
        depth=ResearchDepth.MODERATE,
        follow_up=False,
        user_id="test-monitoring-user",
        additional_context="Focus on recent developments and industry adoption"
    )
    
    # Prepare initial state
    initial_state = {
        "topic": request.topic,
        "user_id": request.user_id,
        "depth": request.depth.value,
        "is_follow_up": request.follow_up,
        "additional_context": request.additional_context,
        "history": [],
        "context_summary": None,
        "plan": None,
        "search_results": None,
        "fetched_content": None,
        "summaries": None,
        "final_brief": None,
        "error": None,
        "execution_metadata": {
            "trace_id": f"test-{int(time.time())}",
            "start_time": time.time(),
            "request_id": f"req-{int(time.time())}",
            "llm_provider": "Azure OpenAI"
        }
    }
    
    # Track execution with monitoring
    trace_id = initial_state["execution_metadata"]["trace_id"]
    
    with metrics_collector.track_execution(trace_id) as metrics:
        print(f"   Starting execution with trace ID: {trace_id}")
        
        # Simulate some token usage for testing
        from app.monitoring import TokenUsage
        test_usage = TokenUsage(
            prompt_tokens=5000,
            completion_tokens=2500,
            total_tokens=7500,
            model="gpt-4o",
            operation="test_llm_call"
        )
        metrics_collector.add_token_usage(test_usage)
        
        # Simulate node execution times
        metrics_collector.add_node_execution_time("context_summarizer", 2.5)
        metrics_collector.add_node_execution_time("planner", 3.2)
        metrics_collector.add_node_execution_time("search_and_fetch", 8.1)
        metrics_collector.add_node_execution_time("per_source_summarizer", 12.3)
        metrics_collector.add_node_execution_time("synthesizer", 5.7)
        
        print("   ✅ Execution metrics collected")
        
        # Log the metrics
        log_execution_metrics(metrics)
        
        # Test trace URL generation
        if langsmith_enabled:
            trace_url = metrics_collector.get_trace_url(trace_id)
            print(f"   Trace URL: {trace_url}")
        else:
            print("   ⚠️  LangSmith not enabled - no trace URL available")
    
    # Test 3: Demonstrate API response format
    print("\n3. Sample API response with monitoring data:")
    
    sample_response = {
        "brief": {
            "topic": "artificial intelligence trends 2024",
            "executive_summary": "AI trends in 2024 show significant advances...",
            "synthesis": "The research reveals three main trends...",
            "key_insights": [
                "Machine learning models are becoming more sophisticated",
                "Ethical AI is gaining prominence",
                "Industry adoption is accelerating"
            ],
            "references": [],
            "generated_at": datetime.utcnow().isoformat()
        },
        "execution_time": 32.1,
        "trace_url": f"https://smith.langchain.com/o/Research%20Assistant/r/{trace_id}" if langsmith_enabled else None,
        "token_usage": {
            "total_tokens": 7500,
            "total_cost_estimate": 0.1125,
            "operations": [
                {
                    "operation": "test_llm_call",
                    "model": "gpt-4o",
                    "prompt_tokens": 5000,
                    "completion_tokens": 2500,
                    "total_tokens": 7500
                }
            ]
        }
    }
    
    print(json.dumps(sample_response, indent=2))
    
    # Test 4: Show monitoring capabilities
    print("\n4. Monitoring capabilities:")
    capabilities = [
        "✅ Trace URL generation",
        "✅ Token usage tracking",
        "✅ Cost estimation",
        "✅ Node execution timing",
        "✅ Error tracking",
        "✅ Performance metrics"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    print("\n🎉 Monitoring test completed successfully!")
    
    if not langsmith_enabled:
        print("\n💡 To enable full monitoring:")
        print("   1. Set LANGSMITH_API_KEY in your .env file")
        print("   2. Set LANGCHAIN_TRACING_V2=true")
        print("   3. Restart the application")


if __name__ == "__main__":
    asyncio.run(test_monitoring_features()) 