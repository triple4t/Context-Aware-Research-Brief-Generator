#!/usr/bin/env python3
"""
Test script for the chat functionality
"""

import requests
import json

def test_api_chat():
    """Test the API chat endpoint."""
    print("🧪 Testing API Chat Endpoint")
    print("=" * 50)
    
    # Test questions
    test_questions = [
        "What is research methodology?",
        "How do I choose a research topic?",
        "What are the best data analysis tools?",
        "How do I write a literature review?",
        "Can you help me with research writing?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {question}")
        
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    "message": question,
                    "user_id": "test-user"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response: {data['response'][:100]}...")
                print(f"   Context: {data['context']}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API Chat Test Completed!")

def test_cli_chat():
    """Test the CLI chat functionality."""
    print("\n🧪 Testing CLI Chat Functionality")
    print("=" * 50)
    
    print("To test CLI chat, run:")
    print("python -m app.cli quick-chat --user test-user")
    print("\nThen try these commands:")
    print("• What is research methodology?")
    print("• How do I choose a research topic?")
    print("• brief")
    print("• history")
    print("• quit")

if __name__ == "__main__":
    test_api_chat()
    test_cli_chat() 