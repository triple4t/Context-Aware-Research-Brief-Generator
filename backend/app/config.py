"""
Configuration management for the research brief generator.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_ENDPOINT: Optional[str] = os.getenv("LANGSMITH_ENDPOINT")
    LANGSMITH_PROJECT: Optional[str] = os.getenv("LANGSMITH_PROJECT")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")  # Fallback for backward compatibility
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "Research Assistant")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    # Use new LangSmith variables if available, fallback to old ones
    @property
    def langsmith_tracing_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled using new or old variables."""
        return self.LANGSMITH_TRACING or self.LANGCHAIN_TRACING_V2
    
    @property
    def langsmith_api_key(self) -> Optional[str]:
        """Get LangSmith API key from new or old variables."""
        return self.LANGSMITH_API_KEY or self.LANGCHAIN_API_KEY
    
    @property
    def langsmith_project(self) -> str:
        """Get LangSmith project from new or old variables."""
        return self.LANGSMITH_PROJECT or self.LANGCHAIN_PROJECT
    
    @property
    def langsmith_endpoint(self) -> str:
        """Get LangSmith endpoint from new or old variables."""
        return self.LANGSMITH_ENDPOINT or self.LANGCHAIN_ENDPOINT
    
    # Google Generative AI Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Search Tool
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    
    # Database Configuration (SQLite only)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./research_assistant.db")
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Research Settings
    MAX_SOURCES_PER_QUERY: int = int(os.getenv("MAX_SOURCES_PER_QUERY", "5"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # LLM Model Settings
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "gemini-1.5-pro")
    SECONDARY_MODEL: str = os.getenv("SECONDARY_MODEL", "gemini-1.5-flash")  # Using flash for faster tasks
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required environment variables are set."""
        required_vars = [
            "GOOGLE_API_KEY",
            "TAVILY_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file."
            )
        
        # Log LangSmith configuration status
        if cls.LANGSMITH_API_KEY or cls.LANGCHAIN_API_KEY:
            logger = logging.getLogger(__name__)
            logger.info(f"LangSmith API key configured: {'Yes' if cls.LANGSMITH_API_KEY else 'No (using fallback)'}")
            logger.info(f"LangSmith tracing enabled: {cls.LANGCHAIN_TRACING_V2}")
            logger.info(f"LangSmith project: {cls.LANGCHAIN_PROJECT}")


# Global settings instance
settings = Settings() 