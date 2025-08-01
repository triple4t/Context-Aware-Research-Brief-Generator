# Monitoring and Observability Guide

This document provides comprehensive information about the monitoring and observability features implemented in the Research Brief Generator.

## Overview

The system includes comprehensive monitoring capabilities powered by LangSmith integration, providing:

- **Trace URLs**: Direct links to LangSmith traces for each execution
- **Token Usage Tracking**: Real-time token consumption per operation
- **Cost Estimation**: Google Generative AI pricing estimates
- **Execution Metrics**: Node-by-node performance tracking
- **Error Monitoring**: Detailed error tracking and reporting

## Setup

### 1. Environment Configuration

Add the following to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=ls_...  # Your LangSmith API key
LANGCHAIN_PROJECT=Research Assistant
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 2. Verify Setup

Check if monitoring is properly configured:

```bash
# Via CLI
python -m app.cli monitoring

# Via API
curl http://localhost:8000/monitoring/status
```

## Features

### Trace URLs

Each research brief generation creates a trace in LangSmith with a direct URL:

```json
{
  "trace_url": "https://smith.langchain.com/o/Research%20Assistant/r/abc123"
}
```

### Token Usage Tracking

Real-time tracking of token consumption:

```json
{
  "token_usage": {
    "total_tokens": 12500,
    "total_cost_estimate": 0.1875,
    "operations": [
      {
        "operation": "llm_call",
        "model": "gpt-4o",
        "prompt_tokens": 8000,
        "completion_tokens": 4500,
        "total_tokens": 12500
      }
    ]
  }
}
```

### Cost Estimation

Automatic cost estimation based on Google Generative AI pricing:

- Input tokens: $0.005 per 1K tokens
- Output tokens: $0.015 per 1K tokens

### Execution Metrics

Node-by-node performance tracking:

```json
{
  "node_execution_times": {
    "context_summarizer": 2.5,
    "planner": 3.2,
    "search_and_fetch": 8.1,
    "per_source_summarizer": 12.3,
    "synthesizer": 5.7
  }
}
```

## API Endpoints

### GET /monitoring/status

Get monitoring and observability status:

```bash
curl http://localhost:8000/monitoring/status
```

Response:
```json
{
  "langsmith_enabled": true,
  "tracing_configured": true,
  "api_key_configured": true,
  "project": "Research Assistant",
  "endpoint": "https://api.smith.langchain.com",
  "capabilities": {
    "trace_urls": true,
    "token_tracking": true,
    "cost_estimation": true,
    "execution_metrics": true
  }
}
```

### GET /monitoring/metrics/{trace_id}

Get execution metrics for a specific trace:

```bash
curl http://localhost:8000/monitoring/metrics/abc123
```

Response:
```json
{
  "trace_id": "abc123",
  "source": "langsmith",
  "metrics": {
    "run_id": "abc123",
    "name": "planner_abc123",
    "status": "completed",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:30:05Z",
    "latency": 5.2,
    "token_usage": {
      "prompt_tokens": 8000,
      "completion_tokens": 4500,
      "total_tokens": 12500
    }
  }
}
```

## CLI Commands

### Show Monitoring Status

```bash
python -m app.cli monitoring
```

Output:
```
Monitoring Status

┌─────────────────────┬──────────┬─────────────────────────┐
│ Component           │ Status   │ Details                 │
├─────────────────────┼──────────┼─────────────────────────┤
│ LangSmith Integration│ ✅ Enabled│                         │
│ Tracing             │ ✅ Enabled│                         │
│ API Key             │ ✅ Set   │                         │
│ Project             │ Research Assistant                 │
│ Endpoint            │ https://api.smith.langchain.com   │
│ Trace URLs          │ ✅ Available│                       │
│ Token Tracking      │ ✅ Available│ Real-time token usage │
│ Cost Estimation     │ ✅ Available│ Google Generative AI pricing  │
│ Execution Metrics   │ ✅ Available│ Node execution times  │
└─────────────────────┴──────────┴─────────────────────────┘
```

### Show Configuration

```bash
python -m app.cli config
```

## Testing

### Run Monitoring Test

```bash
# Via Makefile
make monitoring-test

# Direct execution
python test_monitoring.py
```

### Test with Sample Data

The monitoring test script demonstrates:

1. Monitoring status check
2. Sample brief generation with metrics
3. Token usage simulation
4. Trace URL generation
5. API response format

## Troubleshooting

### LangSmith Not Enabled

If you see "LangSmith not enabled":

1. Check your `.env` file has the correct API key
2. Verify `LANGCHAIN_TRACING_V2=true`
3. Restart the application

### No Trace URLs

If trace URLs are not appearing:

1. Ensure LangSmith API key is valid
2. Check network connectivity to LangSmith
3. Verify project name is correct

### Token Usage Not Available

If token usage is not tracked:

1. Check if LLM responses include usage information
2. Verify Google Generative AI configuration
3. Check logs for extraction errors

## Best Practices

### 1. Environment Management

- Use different projects for development/staging/production
- Set appropriate log levels for different environments
- Monitor API key usage and costs

### 2. Performance Monitoring

- Track execution times for optimization
- Monitor token usage for cost control
- Set up alerts for error rates

### 3. Security

- Keep API keys secure
- Use environment variables for sensitive data
- Monitor access patterns

## Integration with External Tools

### Grafana Dashboard

You can integrate the metrics with Grafana:

1. Export metrics to Prometheus
2. Create dashboards for visualization
3. Set up alerts for thresholds

### Slack Notifications

Set up notifications for:

- High error rates
- Cost thresholds exceeded
- Performance degradation

### Cost Monitoring

Track costs with:

- Daily/weekly/monthly summaries
- Per-user cost tracking
- Cost optimization recommendations

## Example Workflow

1. **Setup**: Configure LangSmith API key
2. **Generate**: Create a research brief
3. **Monitor**: Check trace URL and metrics
4. **Analyze**: Review performance and costs
5. **Optimize**: Adjust parameters based on insights

## Support

For issues with monitoring:

1. Check the logs for error messages
2. Verify environment configuration
3. Test with the monitoring test script
4. Contact support with trace IDs and error details 