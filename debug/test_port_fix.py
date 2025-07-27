#!/usr/bin/env python3
"""
Quick test to verify the port fix for single document upload
"""
import requests
import os

def test_backend_connection():
    """Test if backend is running on the correct port"""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ Backend is running on port 8000")
        print(f"Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on port 8000")
        print("Please start the backend with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

def test_analyze_multiple_endpoint():
    """Test if the analyze-multiple endpoint is available"""
    try:
        # Create a simple test file
        test_content = "This is a test contract document."
        files = {'files': ('test.txt', test_content, 'text/plain')}
        data = {'prompt': 'Test analysis'}
        
        response = requests.post(
            "http://localhost:8000/api/analyze-multiple", 
            files=files, 
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ analyze-multiple endpoint is working")
            result = response.json()
            print(f"Response structure: {list(result.keys())}")
            return True
        else:
            print(f"❌ analyze-multiple endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to analyze-multiple endpoint")
        return False
    except Exception as e:
        print(f"❌ Error testing analyze-multiple endpoint: {e}")
        return False

if __name__ == "__main__":
    print("Testing port fix for single document upload issue...")
    print("=" * 50)
    
    # Test 1: Check if backend is running
    backend_ok = test_backend_connection()
    
    if backend_ok:
        # Test 2: Check if endpoint is working
        endpoint_ok = test_analyze_multiple_endpoint()
        
        if endpoint_ok:
            print("=" * 50)
            print("✅ All tests passed! The port fix should work.")
            print("You can now try uploading a single document in the frontend.")
        else:
            print("=" * 50)
            print("❌ Endpoint test failed. Check backend logs for errors.")
    else:
        print("=" * 50)
        print("❌ Backend connection failed. Please start the backend first.")
        print("\nTo start the backend:")
        print("1. cd backend")
        print("2. python main.py")