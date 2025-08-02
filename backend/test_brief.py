#!/usr/bin/env python3
import requests
import json

def test_brief_generation():
    url = "http://localhost:8000/brief"
    payload = {
        "topic": "India growth in AI compared to US China and Japan",
        "depth": "moderate",
        "user_id": "test-user-789",
        "follow_up": False
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        print("=" * 60)
        print("EXECUTIVE SUMMARY")
        print("=" * 60)
        print(result['brief']['executive_summary'])
        
        print("\n" + "=" * 60)
        print("DETAILED SYNTHESIS")
        print("=" * 60)
        print(result['brief']['synthesis'])
        
        print("\n" + "=" * 60)
        print("KEY INSIGHTS")
        print("=" * 60)
        for i, insight in enumerate(result['brief']['key_insights'], 1):
            print(f"{i}. {insight}")
        
        print(f"\n" + "=" * 60)
        print(f"SOURCES: {len(result['brief']['references'])}")
        print("=" * 60)
        
        # Show first few sources
        for i, ref in enumerate(result['brief']['references'][:3], 1):
            print(f"\nSource {i}:")
            print(f"Title: {ref['title']}")
            print(f"URL: {ref['url']}")
            print(f"Relevance: {ref['relevance_score']}")
            print(f"Key Points: {ref['key_points'][:2]}")  # Show first 2 key points
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_brief_generation() 