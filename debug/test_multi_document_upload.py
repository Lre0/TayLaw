#!/usr/bin/env python3
"""
Test script for multi-document upload functionality
Tests the backend API endpoints for multi-document analysis
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path

async def test_multi_document_upload():
    """Test the multi-document upload and analysis functionality"""
    
    # Test configuration
    API_BASE = "http://localhost:8000"
    
    # Create sample test documents
    test_docs = [
        {
            "filename": "test_contract_1.txt",
            "content": """
            CONTRACT AGREEMENT
            
            This agreement contains the following key terms:
            
            1. Payment Terms: Payment due within 30 days of invoice
            2. Liability Cap: Liability limited to $100,000
            3. Termination: Either party may terminate with 30 days notice
            4. Confidentiality: Both parties agree to maintain confidentiality
            5. Governing Law: This agreement is governed by California state law
            
            RISK INDICATORS:
            - Unlimited liability for intellectual property breaches
            - No force majeure clause
            - Automatic renewal without notice period
            """
        },
        {
            "filename": "test_contract_2.txt", 
            "content": """
            SERVICE AGREEMENT
            
            Key provisions include:
            
            A. Service Levels: 99.5% uptime guarantee
            B. Payment: Net 15 payment terms 
            C. Limitation of Liability: Total liability capped at contract value
            D. Data Protection: GDPR compliance required
            E. Termination: 60 days written notice required
            
            CONCERNING CLAUSES:
            - Indemnification heavily favors vendor
            - Dispute resolution requires arbitration in vendor's jurisdiction
            - Data retention period unclear
            """
        },
        {
            "filename": "test_contract_3.txt",
            "content": """
            PARTNERSHIP AGREEMENT
            
            Partnership terms:
            
            Section 1: Revenue sharing 50/50
            Section 2: Joint IP ownership
            Section 3: 5-year initial term
            Section 4: Quarterly business reviews
            Section 5: Marketing cooperation required
            
            POTENTIAL ISSUES:
            - No clear exit strategy defined
            - Intellectual property assignment ambiguous  
            - Performance metrics not specified
            - Dispute escalation process missing
            """
        }
    ]
    
    print("🚀 Testing Multi-Document Upload API")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("1. Testing API health check...")
        try:
            async with session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ API is running: {data.get('message', 'OK')}")
                else:
                    print(f"   ❌ API health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Cannot connect to API: {e}")
            return False
        
        # Test 2: Multi-document analysis
        print("\n2. Testing multi-document analysis...")
        
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('prompt', 'Please perform a comprehensive red flags review on this contract, identifying potential legal risks, compliance issues, and problematic clauses.')
        
        # Add files to form data
        for doc in test_docs:
            data.add_field('files', 
                          doc['content'].encode(), 
                          filename=doc['filename'],
                          content_type='text/plain')
        
        try:
            print(f"   📤 Uploading {len(test_docs)} test documents...")
            
            async with session.post(f"{API_BASE}/api/analyze-multiple", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Upload successful!")
                    print(f"   📊 Batch ID: {result.get('batch_id', 'N/A')[:8]}...")
                    print(f"   📈 Total documents: {result.get('total_documents', 0)}")
                    print(f"   ✅ Completed: {result.get('completed', 0)}")
                    print(f"   ❌ Failed: {result.get('failed', 0)}")
                    
                    # Print sample results
                    if 'results' in result and result['results']:
                        print(f"\n   📋 Sample analysis result:")
                        sample_result = result['results'][0]
                        print(f"   📄 File: {sample_result.get('filename', 'Unknown')}")
                        print(f"   🎯 Status: {sample_result.get('status', 'Unknown')}")
                        if sample_result.get('analysis'):
                            analysis_preview = sample_result['analysis'][:300] + "..." if len(sample_result['analysis']) > 300 else sample_result['analysis']
                            print(f"   📝 Analysis preview: {analysis_preview}")
                        if sample_result.get('error'):
                            print(f"   ⚠️  Error: {sample_result['error']}")
                    
                    return True
                else:
                    error_data = await response.json()
                    print(f"   ❌ Upload failed: {response.status}")
                    print(f"   📝 Error: {error_data.get('error', 'Unknown error')}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Multi-document analysis failed: {e}")
            return False
        
        # Test 3: File type validation
        print("\n3. Testing file type validation...")
        try:
            invalid_data = aiohttp.FormData()
            invalid_data.add_field('prompt', 'Test prompt')
            invalid_data.add_field('files', b'test content', filename='test.exe', content_type='application/octet-stream')
            
            async with session.post(f"{API_BASE}/api/analyze-multiple", data=invalid_data) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print(f"   ✅ File type validation working: {error_data.get('error', 'Validation error')}")
                else:
                    print(f"   ⚠️  Unexpected response for invalid file: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ File type validation test failed: {e}")
        
        # Test 4: File size validation (simulate large file)
        print("\n4. Testing file size validation...")
        try:
            large_data = aiohttp.FormData()
            large_data.add_field('prompt', 'Test prompt')
            # Simulate 11MB file
            large_content = "x" * (11 * 1024 * 1024)
            large_data.add_field('files', large_content.encode(), filename='large_file.txt', content_type='text/plain')
            
            async with session.post(f"{API_BASE}/api/analyze-multiple", data=large_data) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print(f"   ✅ File size validation working: {error_data.get('error', 'Size validation error')}")
                else:
                    print(f"   ⚠️  Unexpected response for large file: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ File size validation test failed: {e}")
        
        # Test 5: Document limit validation
        print("\n5. Testing document limit validation...")
        try:
            limit_data = aiohttp.FormData()
            limit_data.add_field('prompt', 'Test prompt')
            # Add 11 files (over the limit of 10)
            for i in range(11):
                limit_data.add_field('files', f'Document {i} content'.encode(), filename=f'doc_{i}.txt', content_type='text/plain')
            
            async with session.post(f"{API_BASE}/api/analyze-multiple", data=limit_data) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print(f"   ✅ Document limit validation working: {error_data.get('error', 'Limit validation error')}")
                else:
                    print(f"   ⚠️  Unexpected response for too many files: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ Document limit validation test failed: {e}")

def main():
    """Run the test suite"""
    print("Multi-Document Upload Test Suite")
    print("Ensure the backend server is running on http://localhost:8000")
    print()
    
    try:
        success = asyncio.run(test_multi_document_upload())
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests completed successfully!")
            print("✅ Multi-document upload functionality is working")
        else:
            print("⚠️  Some tests failed or encountered issues")
            print("🔧 Check the backend server and try again")
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()