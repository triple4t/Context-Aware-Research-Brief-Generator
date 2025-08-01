"""
Component-level tests for the research brief generator.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.schemas import (
    ResearchPlan, SourceSummary, FinalBrief, BriefRequest, 
    ResearchDepth, ContextSummary
)
from app.state import GraphState


class TestComponentValidation:
    """Test individual component validation."""
    
    def test_research_plan_validation(self):
        """Test ResearchPlan validation."""
        # Valid plan
        plan = ResearchPlan(
            queries=["test query"],
            rationale="Test rationale",
            expected_sources=5,
            focus_areas=["test area"]
        )
        assert len(plan.queries) == 1
        assert plan.expected_sources == 5
        
        # Invalid plan - empty queries
        with pytest.raises(ValueError):
            ResearchPlan(
                queries=[],
                rationale="Test rationale",
                expected_sources=5,
                focus_areas=["test area"]
            )
        
        # Invalid plan - too many expected sources
        with pytest.raises(ValueError):
            ResearchPlan(
                queries=["test query"],
                rationale="Test rationale",
                expected_sources=20,
                focus_areas=["test area"]
            )
    
    def test_source_summary_validation(self):
        """Test SourceSummary validation."""
        # Valid summary
        summary = SourceSummary(
            url="https://example.com",
            title="Test Source",
            summary="Test summary",
            relevance_score=0.8,
            key_points=["point 1"],
            source_type="article",
            publication_date="2024-01-15",
            author="Test Author"
        )
        assert summary.relevance_score == 0.8
        assert summary.source_type == "article"
        
        # Invalid relevance score
        with pytest.raises(ValueError):
            SourceSummary(
                url="https://example.com",
                title="Test Source",
                summary="Test summary",
                relevance_score=1.5,  # Too high
                key_points=["point 1"],
                source_type="article",
                publication_date="2024-01-15",
                author="Test Author"
            )
    
    def test_final_brief_validation(self):
        """Test FinalBrief validation."""
        source = SourceSummary(
            url="https://example.com",
            title="Test Source",
            summary="Test summary",
            relevance_score=0.8,
            key_points=["point 1"],
            source_type="article",
            publication_date="2024-01-15",
            author="Test Author"
        )
        
        # Valid brief
        brief = FinalBrief(
            topic="Test Topic",
            executive_summary="Test executive summary with sufficient length to meet the minimum requirement of 50 characters for validation",
            synthesis="Test synthesis with sufficient length to meet the minimum requirement",
            key_insights=["insight 1", "insight 2"],
            references=[source]
        )
        assert brief.topic == "Test Topic"
        assert len(brief.key_insights) == 2
        
        # Invalid brief - too short executive summary
        with pytest.raises(ValueError):
            FinalBrief(
                topic="Test Topic",
                executive_summary="Short",  # Too short
                synthesis="Test synthesis with sufficient length",
                key_insights=["insight 1"],
                references=[source]
            )
    
    def test_brief_request_validation(self):
        """Test BriefRequest validation."""
        # Valid request
        request = BriefRequest(
            topic="Test research topic with sufficient length",
            depth=ResearchDepth.MODERATE,
            follow_up=False,
            user_id="test-user"
        )
        assert request.topic == "Test research topic with sufficient length"
        assert request.depth == ResearchDepth.MODERATE
        
        # Invalid request - too short topic
        with pytest.raises(ValueError):
            BriefRequest(
                topic="Test",  # Too short
                depth=ResearchDepth.MODERATE,
                follow_up=False,
                user_id="test-user"
            )
    
    def test_context_summary_validation(self):
        """Test ContextSummary validation."""
        context = ContextSummary(
            previous_topics=["topic 1", "topic 2"],
            key_findings=["finding 1", "finding 2"],
            continuity_notes="Test continuity notes"
        )
        assert len(context.previous_topics) == 2
        assert len(context.key_findings) == 2
        assert context.user_preferences == {}  # Default value


class TestStateManagement:
    """Test state management functionality."""
    
    def test_graph_state_creation(self):
        """Test GraphState creation."""
        state = GraphState(
            topic="test topic",
            user_id="test-user",
            depth="moderate",
            is_follow_up=False,
            additional_context=None,
            history=[],
            context_summary=None,
            plan=None,
            search_results=None,
            fetched_content=None,
            summaries=None,
            final_brief=None,
            error=None,
            execution_metadata={}
        )
        
        assert state["topic"] == "test topic"
        assert state["user_id"] == "test-user"
        assert state["depth"] == "moderate"
        assert state["is_follow_up"] is False
    
    def test_graph_state_update(self):
        """Test GraphState updates."""
        state = GraphState(
            topic="test topic",
            user_id="test-user",
            depth="moderate",
            is_follow_up=False,
            additional_context=None,
            history=[],
            context_summary=None,
            plan=None,
            search_results=None,
            fetched_content=None,
            summaries=None,
            final_brief=None,
            error=None,
            execution_metadata={}
        )
        
        # Update state
        state["plan"] = ResearchPlan(
            queries=["test query"],
            rationale="Test rationale",
            expected_sources=3,
            focus_areas=["test area"]
        )
        
        assert state["plan"] is not None
        assert len(state["plan"].queries) == 1


class TestSchemaSerialization:
    """Test schema serialization and deserialization."""
    
    def test_research_plan_serialization(self):
        """Test ResearchPlan serialization."""
        plan = ResearchPlan(
            queries=["query 1", "query 2"],
            rationale="Test rationale",
            expected_sources=5,
            focus_areas=["area 1", "area 2"]
        )
        
        # Serialize
        data = plan.model_dump()
        assert "queries" in data
        assert "rationale" in data
        assert "expected_sources" in data
        assert "focus_areas" in data
        
        # Deserialize
        new_plan = ResearchPlan(**data)
        assert new_plan.queries == plan.queries
        assert new_plan.rationale == plan.rationale
        assert new_plan.expected_sources == plan.expected_sources
    
    def test_final_brief_serialization(self):
        """Test FinalBrief serialization."""
        source = SourceSummary(
            url="https://example.com",
            title="Test Source",
            summary="Test summary",
            relevance_score=0.8,
            key_points=["point 1"],
            source_type="article",
            publication_date="2024-01-15",
            author="Test Author"
        )
        
        brief = FinalBrief(
            topic="Test Topic",
            executive_summary="Test executive summary with sufficient length to meet the minimum requirement of 50 characters for validation",
            synthesis="Test synthesis with sufficient length to meet the minimum requirement",
            key_insights=["insight 1", "insight 2"],
            references=[source]
        )
        
        # Serialize
        data = brief.model_dump()
        assert "topic" in data
        assert "executive_summary" in data
        assert "key_insights" in data
        assert "references" in data
        
        # Deserialize
        new_brief = FinalBrief(**data)
        assert new_brief.topic == brief.topic
        assert new_brief.executive_summary == brief.executive_summary
        assert len(new_brief.key_insights) == len(brief.key_insights)


class TestResearchDepth:
    """Test ResearchDepth enum functionality."""
    
    def test_depth_values(self):
        """Test all depth values."""
        assert ResearchDepth.SHALLOW.value == "shallow"
        assert ResearchDepth.MODERATE.value == "moderate"
        assert ResearchDepth.DEEP.value == "deep"
    
    def test_depth_comparison(self):
        """Test depth comparison."""
        assert ResearchDepth.SHALLOW != ResearchDepth.MODERATE
        assert ResearchDepth.MODERATE != ResearchDepth.DEEP
        assert ResearchDepth.SHALLOW != ResearchDepth.DEEP
    
    def test_depth_in_request(self):
        """Test depth in BriefRequest."""
        request = BriefRequest(
            topic="Test topic with sufficient length",
            depth=ResearchDepth.DEEP,
            follow_up=False,
            user_id="test-user"
        )
        assert request.depth == ResearchDepth.DEEP 