#!/usr/bin/env python3
"""
Simple test for chat API
"""

import requests
import json

def test_simple_chat():
    """Test the chat API with minimal request."""
    print("🧪 Simple Chat API Test")
    print("=" * 40)
    
    # Test with minimal payload
    payload = {
        "message": "Hello",
        "user_id": "test-user"
    }
    
    try:
        print(f"📡 Sending request: {payload}")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_simple_chat() 