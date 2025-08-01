"""
Unit tests for Pydantic schemas using Azure OpenAI.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    ResearchPlan,
    SourceSummary,
    ContextSummary,
    FinalBrief,
    BriefRequest,
    ResearchDepth
)


class TestResearchPlan:
    """Test ResearchPlan schema."""
    
    def test_valid_research_plan(self):
        """Test creating a valid research plan."""
        plan = ResearchPlan(
            queries=["test query 1", "test query 2"],
            rationale="Test rationale",
            expected_sources=5,
            focus_areas=["area 1", "area 2"]
        )
        
        assert len(plan.queries) == 2
        assert plan.expected_sources == 5
        assert len(plan.focus_areas) == 2
    
    def test_invalid_queries_empty(self):
        """Test validation with empty queries list."""
        with pytest.raises(ValidationError):
            ResearchPlan(
                queries=[],
                rationale="Test rationale",
                expected_sources=5,
                focus_areas=["area 1"]
            )
    
    def test_invalid_expected_sources(self):
        """Test validation with invalid expected sources."""
        with pytest.raises(ValidationError):
            ResearchPlan(
                queries=["test query"],
                rationale="Test rationale",
                expected_sources=20,  # Too high
                focus_areas=["area 1"]
            )


class TestSourceSummary:
    """Test SourceSummary schema."""
    
    def test_valid_source_summary(self):
        """Test creating a valid source summary."""
        summary = SourceSummary(
            url="https://example.com",
            title="Test Title",
            summary="Test summary content",
            relevance_score=0.8,
            key_points=["point 1", "point 2"],
            source_type="article",
            publication_date="2024-01-01",
            author="Test Author"
        )
        
        assert summary.relevance_score == 0.8
        assert len(summary.key_points) == 2
        assert summary.source_type == "article"
    
    def test_invalid_relevance_score(self):
        """Test validation with invalid relevance score."""
        with pytest.raises(ValidationError):
            SourceSummary(
                url="https://example.com",
                title="Test Title",
                summary="Test summary",
                relevance_score=1.5,  # Too high
                key_points=["point 1"],
                source_type="article"
            )
    
    def test_invalid_summary_length(self):
        """Test validation with too short summary."""
        with pytest.raises(ValidationError):
            SourceSummary(
                url="https://example.com",
                title="Test Title",
                summary="Short",  # Too short
                relevance_score=0.5,
                key_points=["point 1"],
                source_type="article"
            )


class TestContextSummary:
    """Test ContextSummary schema."""
    
    def test_valid_context_summary(self):
        """Test creating a valid context summary."""
        context = ContextSummary(
            previous_topics=["topic 1", "topic 2"],
            key_findings=["finding 1", "finding 2"],
            user_preferences={"pref1": "value1"},
            continuity_notes="Test continuity notes"
        )
        
        assert len(context.previous_topics) == 2
        assert len(context.key_findings) == 2
        assert "pref1" in context.user_preferences
    
    def test_default_user_preferences(self):
        """Test default user preferences."""
        context = ContextSummary(
            previous_topics=["topic 1"],
            key_findings=["finding 1"],
            continuity_notes="Test notes"
        )
        
        assert context.user_preferences == {}


class TestFinalBrief:
    """Test FinalBrief schema."""
    
    def test_valid_final_brief(self):
        """Test creating a valid final brief."""
        source = SourceSummary(
            url="https://example.com",
            title="Test Source",
            summary="Test source summary",
            relevance_score=0.8,
            key_points=["point 1"],
            source_type="article",
            publication_date="2024-01-15",
            author="Test Author"
        )
        
        brief = FinalBrief(
            topic="Test Topic",
            executive_summary="Test executive summary with sufficient length to meet requirements",
            synthesis="Test synthesis with sufficient length to meet the minimum requirement of 200 characters",
            key_insights=["insight 1", "insight 2"],
            references=[source]
        )
        
        assert brief.topic == "Test Topic"
        assert len(brief.key_insights) == 2
        assert len(brief.references) == 1
        assert brief.generated_at is not None
    
    def test_invalid_executive_summary_length(self):
        """Test validation with too short executive summary."""
        source = SourceSummary(
            url="https://example.com",
            title="Test Source",
            summary="Test source summary",
            relevance_score=0.8,
            key_points=["point 1"],
            source_type="article",
            publication_date="2024-01-15",
            author="Test Author"
        )
        
        with pytest.raises(ValidationError):
            FinalBrief(
                topic="Test Topic",
                executive_summary="Short",  # Too short
                synthesis="Test synthesis with sufficient length",
                key_insights=["insight 1"],
                references=[source]
            )


class TestBriefRequest:
    """Test BriefRequest schema."""
    
    def test_valid_brief_request(self):
        """Test creating a valid brief request."""
        request = BriefRequest(
            topic="Test research topic",
            depth=ResearchDepth.MODERATE,
            follow_up=False,
            user_id="test-user"
        )
        
        assert request.topic == "Test research topic"
        assert request.depth == ResearchDepth.MODERATE
        assert request.follow_up is False
    
    def test_invalid_topic_length(self):
        """Test validation with too short topic."""
        with pytest.raises(ValidationError):
            BriefRequest(
                topic="Test",  # Too short
                depth=ResearchDepth.MODERATE,
                follow_up=False,
                user_id="test-user"
            )


class TestResearchDepth:
    """Test ResearchDepth enum."""
    
    def test_depth_values(self):
        """Test all depth values."""
        assert ResearchDepth.SHALLOW.value == "shallow"
        assert ResearchDepth.MODERATE.value == "moderate"
        assert ResearchDepth.DEEP.value == "deep"
    
    def test_depth_validation(self):
        """Test depth validation in BriefRequest."""
        request = BriefRequest(
            topic="Test topic with sufficient length",
            depth=ResearchDepth.DEEP,
            follow_up=False,
            user_id="test-user"
        )
        
        assert request.depth == ResearchDepth.DEEP 