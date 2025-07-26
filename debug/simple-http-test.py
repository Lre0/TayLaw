#!/usr/bin/env python3
"""
Simple HTTP test to isolate the FastAPI issue
"""

import requests
import io

def test_simple_http():
    """Test simple HTTP request"""
    
    print("Testing Simple HTTP Request")
    print("=" * 40)
    
    # Test with ToS chunk content  
    with open('test-tos-chunk.txt', 'r', encoding='utf-8') as f:
        content = f.read().encode('utf-8')
    
    # Create file-like object
    file_content = io.BytesIO(content)
    
    files = {'file': ('test.txt', file_content, 'text/plain')}
    data = {'prompt': 'Analyze for legal risks'}
    
    try:
        print("Sending request...")
        response = requests.post(
            'http://localhost:8001/api/analyze',
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', 'No analysis')
            print(f"Analysis length: {len(analysis)} characters")
            print(f"Word count: ~{len(analysis.split())} words")
            
            # Clean for display
            analysis_clean = analysis.encode('ascii', 'replace').decode('ascii')
            print(f"Analysis preview: {analysis_clean[:500]}...")
        else:
            print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_simple_http()