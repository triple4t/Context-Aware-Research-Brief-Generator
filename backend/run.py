#!/usr/bin/env python3
"""
Entry point for the Context-Aware Research Brief Generator.

This script provides a simple way to run the application in different modes.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run.py api     - Start the FastAPI server")
        print("  python run.py cli     - Run the CLI interface")
        print("  python run.py test    - Run tests")
        print("  python run.py example - Generate an example brief")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "api":
        import uvicorn
        from app.main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    
    elif command == "cli":
        from app.cli import cli_app
        cli_app()
    
    elif command == "test":
        import pytest
        pytest.main(["tests/", "-v"])
    
    elif command == "example":
        from app.cli import cli_app
        import sys
        sys.argv = ["cli", "generate", "--topic", "artificial intelligence trends 2024", "--verbose"]
        cli_app()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 