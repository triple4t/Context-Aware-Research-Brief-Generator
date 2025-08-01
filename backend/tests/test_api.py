"""
API endpoint tests for the research brief generator.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json

from app.main import app
from app.schemas import FinalBrief, SourceSummary, ResearchDepth


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_endpoint(self, client):
        """Test that the health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "environment" in data
        assert "llm_provider" in data
        assert "langsmith" in data


class TestBriefEndpoint:
    """Test the brief generation endpoint."""
    
    @patch('app.main.research_graph')
    @patch('app.main.metrics_collector')
    @patch('app.main.storage')
    def test_generate_brief_success(self, mock_storage, mock_metrics, mock_graph, client):
        """Test successful brief generation."""
        # Mock the graph execution as an async generator
        async def mock_astream(state):
            # Create a proper FinalBrief object
            from app.schemas import FinalBrief, SourceSummary
            from datetime import datetime
            
            test_brief = FinalBrief(
                topic="test topic",
                executive_summary="Test executive summary with sufficient length to meet the minimum requirement of 50 characters for validation",
                synthesis="Test synthesis with sufficient length to meet the minimum requirement",
                key_insights=["insight 1", "insight 2"],
                references=[
                    SourceSummary(
                        url="https://example.com",
                        title="Test Source",
                        summary="Test summary",
                        relevance_score=0.8,
                        key_points=["point 1"],
                        source_type="article",
                        publication_date="2024-01-15",
                        author="Test Author"
                    )
                ],
                generated_at=datetime(2024, 1, 1)
            )
            
            yield {
                "planner": {"plan": {"queries": ["test query"]}},
                "search_and_fetch": {"fetched_content": [{"url": "test.com"}]},
                "per_source_summarizer": {"summaries": [{"title": "Test"}]},
                "synthesizer": {
                    "final_brief": test_brief
                }
            }
        
        mock_graph.astream = mock_astream
        
        # Mock metrics collector context manager
        mock_metrics_context = Mock()
        mock_metrics_context.__enter__ = Mock(return_value=mock_metrics_context)
        mock_metrics_context.__exit__ = Mock(return_value=None)
        mock_metrics_context.token_usage = [
            Mock(
                operation="completion",
                model="gpt-4",
                prompt_tokens=500,
                completion_tokens=500,
                total_tokens=1000
            )
        ]
        mock_metrics_context.get_total_tokens = Mock(return_value=1000)
        mock_metrics_context.get_cost_estimate = Mock(return_value=0.05)
        
        mock_metrics.track_execution.return_value = mock_metrics_context
        mock_metrics.get_trace_url.return_value = "https://smith.langchain.com/test"
        mock_metrics.langsmith_manager.is_enabled = True
        
        # Mock storage
        mock_storage.get_user_history.return_value = []
        mock_storage.save_brief.return_value = True
        
        # Mock the log_execution_metrics function to avoid any issues
        with patch('app.main.log_execution_metrics'):
            # Make request
            response = client.post(
                "/brief",
                json={
                    "topic": "test topic with sufficient length",
                    "depth": "moderate",
                    "follow_up": False,
                    "user_id": "test-user"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "brief" in data
            assert "execution_time" in data
            assert "trace_url" in data
            assert data["brief"]["topic"] == "test topic"
    
    def test_generate_brief_invalid_request(self, client):
        """Test brief generation with invalid request."""
        response = client.post(
            "/brief",
            json={
                "topic": "short",  # Too short
                "depth": "moderate",
                "follow_up": False,
                "user_id": "test-user"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_brief_missing_fields(self, client):
        """Test brief generation with missing required fields."""
        response = client.post(
            "/brief",
            json={
                "topic": "test topic with sufficient length"
                # Missing required fields
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestMonitoringEndpoint:
    """Test the monitoring endpoint."""
    
    def test_monitoring_endpoint(self, client):
        """Test that the monitoring endpoint returns status."""
        response = client.get("/monitoring")
        assert response.status_code == 200
        data = response.json()
        assert "langsmith_enabled" in data
        assert "tracing_enabled" in data
        assert "trace_urls" in data


class TestStatsEndpoint:
    """Test the stats endpoint."""
    
    @patch('app.main.storage')
    def test_stats_endpoint(self, mock_storage, client):
        """Test that the stats endpoint returns user statistics."""
        # Mock storage response
        mock_storage.get_user_stats.return_value = {
            "total_briefs": 5,
            "recent_briefs": 2,
            "user_created": "2024-01-01"
        }
        
        response = client.get("/stats/test-user")
        assert response.status_code == 200
        data = response.json()
        assert "total_briefs" in data
        assert "recent_briefs" in data
        assert data["total_briefs"] == 5


class TestHistoryEndpoint:
    """Test the history endpoint."""
    
    @patch('app.main.storage')
    def test_history_endpoint(self, mock_storage, client):
        """Test that the history endpoint returns user history."""
        # Mock storage response
        mock_storage.get_user_history.return_value = [
            {
                "topic": "test topic",
                "executive_summary": "Test summary with sufficient length",
                "generated_at": "2024-01-01T00:00:00",
                "key_insights": ["insight 1"],
                "references": []
            }
        ]
        
        response = client.get("/history/test-user")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["topic"] == "test topic"


class TestConfigEndpoint:
    """Test the configuration endpoint."""
    
    def test_config_endpoint(self, client):
        """Test that the config endpoint returns configuration."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "llm_provider" in data
        assert "storage" in data


class TestErrorHandling:
    """Test error handling in the API."""
    
    @patch('app.main.research_graph')
    def test_graph_execution_error(self, mock_graph, client):
        """Test handling of graph execution errors."""
        # Mock graph to raise exception
        mock_graph.astream.side_effect = Exception("Graph execution failed")
        
        response = client.post(
            "/brief",
            json={
                "topic": "test topic with sufficient length",
                "depth": "moderate",
                "follow_up": False,
                "user_id": "test-user"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Graph execution failed" in data["error"]
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/brief",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422 