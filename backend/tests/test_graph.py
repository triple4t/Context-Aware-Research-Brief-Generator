"""
End-to-end tests for the research brief generation graph.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.graph import research_graph
from app.schemas import FinalBrief, SourceSummary, ResearchPlan
from app.state import GraphState


class TestGraphExecution:
    """Test the research brief generation graph."""
    
    @pytest.fixture
    def mock_initial_state(self) -> GraphState:
        """Create a mock initial state for testing."""
        return {
            "topic": "artificial intelligence trends 2024",
            "user_id": "test-user",
            "depth": "moderate",
            "is_follow_up": False,
            "additional_context": None,
            "history": [],
            "context_summary": None,
            "plan": None,
            "search_results": None,
            "fetched_content": None,
            "summaries": None,
            "final_brief": None,
            "error": None,
            "execution_metadata": {}
        }
    
    @pytest.fixture
    def mock_source_summary(self) -> SourceSummary:
        """Create a mock source summary."""
        return SourceSummary(
            url="https://example.com/ai-trends",
            title="AI Trends 2024",
            summary="Comprehensive analysis of artificial intelligence trends in 2024",
            relevance_score=0.9,
            key_points=["Machine learning advances", "AI ethics", "Industry adoption"],
            source_type="article",
            publication_date="2024-01-15",
            author="AI Research Team"
        )
    
    @pytest.fixture
    def mock_final_brief(self, mock_source_summary: SourceSummary) -> FinalBrief:
        """Create a mock final brief."""
        return FinalBrief(
            topic="artificial intelligence trends 2024",
            executive_summary="AI trends in 2024 show significant advances in machine learning and increased focus on ethical AI development with comprehensive analysis of emerging technologies.",
            synthesis="The research reveals three main trends: 1) Advanced machine learning models, 2) Growing emphasis on AI ethics and responsible development, 3) Increased industry adoption across sectors with detailed analysis.",
            key_insights=[
                "Machine learning models are becoming more sophisticated",
                "Ethical AI is gaining prominence",
                "Industry adoption is accelerating"
            ],
            references=[mock_source_summary],
            context_used=None,
            metadata={"test": True}
        )
    
    @patch('app.nodes.get_primary_llm')
    @patch('app.nodes.get_secondary_llm')
    @patch('app.nodes.search_tool')
    @pytest.mark.asyncio
    async def test_graph_execution_success(
        self,
        mock_search_tool,
        mock_secondary_llm,
        mock_primary_llm,
        mock_initial_state: GraphState,
        mock_final_brief: FinalBrief
    ):
        """Test successful graph execution."""
        # Mock LLM responses
        mock_primary_llm.return_value = Mock()
        mock_secondary_llm.return_value = Mock()
        
        # Mock search tool
        mock_search_tool.search_and_fetch.return_value = [
            {
                "url": "https://example.com/ai-trends",
                "title": "AI Trends 2024",
                "content": "Comprehensive analysis of artificial intelligence trends...",
                "word_count": 500,
                "extracted_at": 1234567890
            }
        ]
        
        # Mock structured LLM responses
        with patch('app.nodes.create_structured_llm') as mock_structured_llm:
            # Mock planning response
            mock_plan = ResearchPlan(
                queries=["AI trends 2024", "artificial intelligence developments"],
                rationale="Comprehensive search strategy",
                expected_sources=5,
                focus_areas=["machine learning", "AI ethics", "industry adoption"]
            )
            
            # Mock summarization response
            mock_summary = SourceSummary(
                url="https://example.com/ai-trends",
                title="AI Trends 2024",
                summary="Comprehensive analysis of artificial intelligence trends in 2024",
                relevance_score=0.9,
                key_points=["Machine learning advances", "AI ethics"],
                source_type="article",
                publication_date="2024-01-15",
                author="AI Research Team"
            )
            
            # Create mock LLM instances that return proper responses
            mock_plan_llm = Mock()
            mock_plan_llm.invoke.return_value = Mock(content=mock_plan.model_dump())
            
            mock_summary_llm = Mock()
            mock_summary_llm.invoke.return_value = Mock(content=mock_summary.model_dump())
            
            mock_synthesis_llm = Mock()
            mock_synthesis_llm.invoke.return_value = Mock(content=mock_final_brief.model_dump())
            
            # Configure mock responses
            mock_structured_llm.side_effect = [mock_plan_llm, mock_summary_llm, mock_synthesis_llm]
            
            # Execute graph
            final_brief = None
            async for event in research_graph.astream(mock_initial_state):
                for node_name, node_output in event.items():
                    if node_name != "__end__":
                        if "final_brief" in node_output:
                            final_brief = node_output["final_brief"]
            
            # Assertions
            assert final_brief is not None
            assert final_brief.topic == "artificial intelligence trends 2024"
            assert len(final_brief.key_insights) > 0
            assert len(final_brief.references) > 0
    
    @patch('app.nodes.get_primary_llm')
    @patch('app.nodes.get_secondary_llm')
    @patch('app.nodes.search_tool')
    @pytest.mark.asyncio
    async def test_graph_execution_with_error(
        self,
        mock_search_tool,
        mock_secondary_llm,
        mock_primary_llm,
        mock_initial_state: GraphState
    ):
        """Test graph execution with error handling."""
        # Mock LLM to raise exception
        mock_primary_llm.side_effect = Exception("LLM API error")
        
        # Execute graph
        final_brief = None
        async for event in research_graph.astream(mock_initial_state):
            for node_name, node_output in event.items():
                if node_name != "__end__":
                    if "final_brief" in node_output:
                        final_brief = node_output["final_brief"]
        
        # Should still get a final brief (error handler)
        assert final_brief is not None
        assert "error" in final_brief.metadata or "Error" in final_brief.executive_summary
    
    @patch('app.nodes.get_primary_llm')
    @patch('app.nodes.get_secondary_llm')
    @patch('app.nodes.search_tool')
    @pytest.mark.asyncio
    async def test_follow_up_query_execution(
        self,
        mock_search_tool,
        mock_secondary_llm,
        mock_primary_llm,
        mock_initial_state: GraphState
    ):
        """Test graph execution with follow-up query."""
        # Modify state for follow-up
        mock_initial_state["is_follow_up"] = True
        mock_initial_state["history"] = [
            FinalBrief(
                topic="previous topic",
                executive_summary="Previous research summary with sufficient length to meet the minimum requirement of 50 characters for validation",
                synthesis="Previous synthesis with sufficient length to meet the minimum requirement",
                key_insights=["Previous insight"],
                references=[],
                metadata={}
            )
        ]
        
        # Mock LLM responses
        mock_primary_llm.return_value = Mock()
        mock_secondary_llm.return_value = Mock()
        
        # Mock search tool
        mock_search_tool.search_and_fetch.return_value = [
            {
                "url": "https://example.com/follow-up",
                "title": "Follow-up Research",
                "content": "Follow-up content...",
                "word_count": 300,
                "extracted_at": 1234567890
            }
        ]
        
        # Mock structured LLM responses
        with patch('app.nodes.create_structured_llm') as mock_structured_llm:
            mock_plan = ResearchPlan(
                queries=["follow-up query"],
                rationale="Follow-up research strategy",
                expected_sources=3,
                focus_areas=["follow-up area"]
            )
            
            mock_summary = SourceSummary(
                url="https://example.com/follow-up",
                title="Follow-up Research",
                summary="Follow-up research content",
                relevance_score=0.8,
                key_points=["Follow-up point"],
                source_type="article",
                publication_date="2024-01-15",
                author="Follow-up Author"
            )
            
            mock_final_brief = FinalBrief(
                topic="follow-up topic",
                executive_summary="Follow-up executive summary with sufficient length to meet the minimum requirement of 50 characters for validation",
                synthesis="Follow-up synthesis with sufficient length to meet the minimum requirement",
                key_insights=["Follow-up insight"],
                references=[mock_summary],
                metadata={}
            )
            
            # Create mock LLM instances
            mock_plan_llm = Mock()
            mock_plan_llm.invoke.return_value = Mock(content=mock_plan.model_dump())
            
            mock_summary_llm = Mock()
            mock_summary_llm.invoke.return_value = Mock(content=mock_summary.model_dump())
            
            mock_synthesis_llm = Mock()
            mock_synthesis_llm.invoke.return_value = Mock(content=mock_final_brief.model_dump())
            
            # Configure mock responses
            mock_structured_llm.side_effect = [mock_plan_llm, mock_summary_llm, mock_synthesis_llm]
            
            # Execute graph
            final_brief = None
            async for event in research_graph.astream(mock_initial_state):
                for node_name, node_output in event.items():
                    if node_name != "__end__":
                        if "final_brief" in node_output:
                            final_brief = node_output["final_brief"]
            
            # Assertions
            assert final_brief is not None
            assert final_brief.topic == "follow-up topic"
    
    @patch('app.nodes.get_primary_llm')
    @patch('app.nodes.get_secondary_llm')
    @patch('app.nodes.search_tool')
    @pytest.mark.asyncio
    async def test_graph_state_progression(
        self,
        mock_search_tool,
        mock_secondary_llm,
        mock_primary_llm,
        mock_initial_state: GraphState
    ):
        """Test that graph state progresses correctly through nodes."""
        # Mock LLM responses
        mock_primary_llm.return_value = Mock()
        mock_secondary_llm.return_value = Mock()
        
        # Mock search tool
        mock_search_tool.search_and_fetch.return_value = [
            {
                "url": "https://example.com/test",
                "title": "Test Article",
                "content": "Test content...",
                "word_count": 200,
                "extracted_at": 1234567890
            }
        ]
        
        # Mock structured LLM responses
        with patch('app.nodes.create_structured_llm') as mock_structured_llm:
            mock_plan = ResearchPlan(
                queries=["test query"],
                rationale="Test rationale",
                expected_sources=3,
                focus_areas=["test area"]
            )
            
            mock_summary = SourceSummary(
                url="https://example.com/test",
                title="Test Article",
                summary="Test summary",
                relevance_score=0.7,
                key_points=["Test point"],
                source_type="article",
                publication_date="2024-01-15",
                author="Test Author"
            )
            
            mock_final_brief = FinalBrief(
                topic="test topic",
                executive_summary="Test executive summary with sufficient length to meet the minimum requirement of 50 characters for validation",
                synthesis="Test synthesis with sufficient length to meet the minimum requirement",
                key_insights=["Test insight"],
                references=[mock_summary],
                metadata={}
            )
            
            # Create mock LLM instances
            mock_plan_llm = Mock()
            mock_plan_llm.invoke.return_value = Mock(content=mock_plan.model_dump())
            
            mock_summary_llm = Mock()
            mock_summary_llm.invoke.return_value = Mock(content=mock_summary.model_dump())
            
            mock_synthesis_llm = Mock()
            mock_synthesis_llm.invoke.return_value = Mock(content=mock_final_brief.model_dump())
            
            # Configure mock responses
            mock_structured_llm.side_effect = [mock_plan_llm, mock_summary_llm, mock_synthesis_llm]
            
            # Track state progression
            state_progression = []
            
            async for event in research_graph.astream(mock_initial_state):
                for node_name, node_output in event.items():
                    if node_name != "__end__":
                        state_progression.append(node_name)
            
            # Verify node execution order
            expected_nodes = ["planner", "search_and_fetch", "per_source_summarizer", "synthesizer"]
            assert state_progression == expected_nodes 