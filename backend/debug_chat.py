#!/usr/bin/env python3
"""
Debug script for chat functionality
"""

import requests
import json

def test_chat_api():
    """Test the chat API with detailed error handling."""
    print("🧪 Debugging Chat API")
    print("=" * 50)
    
    # Test basic health first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Backend Health: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Backend Health Error: {e}")
        return
    
    # Test chat with simple message
    test_message = "What time is it?"
    
    try:
        print(f"\n📡 Testing Chat API with: '{test_message}'")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "message": test_message,
                "user_id": "debug-user"
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_chat_api() 