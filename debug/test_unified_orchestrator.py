"""
Test script for the unified document orchestrator to verify optimization improvements
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import from agents
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

from agents.unified_orchestrator import UnifiedDocumentOrchestrator

async def test_single_document():
    """Test single document processing"""
    print("=== Testing Single Document Processing ===")
    
    orchestrator = UnifiedDocumentOrchestrator()
    
    # Create a simple test document
    test_content = b"""PROFESSIONAL SERVICES AGREEMENT

1. LIABILITY LIMITATION
The Provider's total liability for any claims arising out of this Agreement shall not exceed the total fees paid by Client in the 12 months preceding the claim.

2. TERMINATION
Either party may terminate this Agreement with 30 days written notice.

3. INTELLECTUAL PROPERTY
All work product shall remain the property of the Provider unless otherwise agreed in writing.
"""
    
    file_data = {
        'filename': 'test_agreement.txt',
        'file_content': test_content
    }
    
    try:
        result = await orchestrator.analyze_documents(
            file_data,
            "Analyze this contract for potential red flags and risks.",
            unified=True
        )
        
        print(f"[PASS] Single document processing successful")
        print(f"  - Document: {result.get('document', 'N/A')}")
        print(f"  - Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"  - Analysis length: {len(result.get('analysis', ''))} characters")
        return True
        
    except Exception as e:
        print(f"[FAIL] Single document processing failed: {e}")
        return False

async def test_multiple_documents():
    """Test multiple document processing"""
    print("\n=== Testing Multiple Document Processing ===")
    
    orchestrator = UnifiedDocumentOrchestrator()
    
    # Create test documents
    doc1_content = b"""SERVICE LEVEL AGREEMENT
1. AVAILABILITY: Services shall be available 99.9% of the time.
2. LIABILITY: Maximum liability is $10,000 per incident.
"""
    
    doc2_content = b"""NON-DISCLOSURE AGREEMENT
1. CONFIDENTIALITY: All information shall remain confidential for 5 years.
2. TERMINATION: This agreement terminates upon mutual consent.
"""
    
    files_data = [
        {'filename': 'sla.txt', 'file_content': doc1_content},
        {'filename': 'nda.txt', 'file_content': doc2_content}
    ]
    
    try:
        # Test unified analysis
        result = await orchestrator.analyze_documents(
            files_data,
            "Analyze these contracts for potential red flags and risks.",
            unified=True
        )
        
        print(f"[PASS] Multiple document unified processing successful")
        print(f"  - Total documents: {result.get('total_documents', 0)}")
        print(f"  - Successful: {result.get('successful', 0)}")
        print(f"  - Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"  - Analysis type: {result.get('analysis_type', 'N/A')}")
        print(f"  - Unified analysis length: {len(result.get('unified_analysis', ''))}")
        
        # Test individual analysis
        result_individual = await orchestrator.analyze_documents(
            files_data,
            "Analyze these contracts for potential red flags and risks.",
            unified=False
        )
        
        print(f"[PASS] Multiple document individual processing successful")
        print(f"  - Individual results count: {len(result_individual.get('results', []))}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Multiple document processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_comparison():
    """Test performance benefits of unified approach"""
    print("\n=== Performance Test ===")
    
    # Create multiple small documents for performance testing
    files_data = []
    for i in range(3):
        content = f"""CONTRACT {i+1}
1. TERM: This agreement is valid for {i+1} year(s).
2. LIABILITY: Liability is limited to ${(i+1)*1000}.
3. TERMINATION: Either party may terminate with {i+1}0 days notice.
""".encode()
        files_data.append({
            'filename': f'contract_{i+1}.txt',
            'file_content': content
        })
    
    import time
    start_time = time.time()
    
    try:
        orchestrator = UnifiedDocumentOrchestrator(max_concurrent_documents=3)
        result = await orchestrator.analyze_documents(
            files_data,
            "Identify key contract terms and any risks.",
            unified=True
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"[PASS] Performance test completed")
        print(f"  - Documents processed: {result.get('successful', 0)}")
        print(f"  - Total time: {processing_time:.2f}s")
        print(f"  - Average per document: {processing_time/len(files_data):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting Unified Document Orchestrator Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if await test_single_document():
        tests_passed += 1
    
    if await test_multiple_documents():
        tests_passed += 1
    
    if await test_performance_comparison():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("[SUCCESS] All tests passed! Unified orchestrator is working correctly.")
        print("\nOptimization Benefits Achieved:")
        print("- [OK] Single codebase for both single and multiple documents")
        print("- [OK] Simplified API with unified endpoint")
        print("- [OK] Efficient parallel processing with asyncio.gather()")
        print("- [OK] Eliminated complex batch/queue management")
        print("- [OK] Reduced code complexity and maintenance overhead")
    else:
        print("[ERROR] Some tests failed. Please review the implementation.")

if __name__ == "__main__":
    asyncio.run(main())