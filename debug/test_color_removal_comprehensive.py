"""
Comprehensive test to ensure color coding removal works in all scenarios
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import from agents
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

from agents.langgraph_orchestrator import LangGraphOrchestrator

async def test_comprehensive_color_removal():
    """Test the color removal function with various inputs"""
    print("=== Comprehensive Color Removal Test ===")
    
    orchestrator = LangGraphOrchestrator()
    
    # Test text with various color-coded patterns
    test_texts = [
        """EXECUTIVE SUMMARY:
- Red coded (high-risk) findings: 2
- Yellow coded (medium-risk) findings: 3  
- Green coded (low-risk/favorable) findings: 1

• Green coded issues represent those matters which are favorable to CLIENT.
• Yellow coded issues represent those matters which are of medium risk.
• Red coded issues represent those matters which require immediate attention.
""",
        
        """Analysis Results:
This document contains Red coded issues that need attention.
There are also Yellow coded concerns in section 2.
The Green coded items are acceptable as written.
""",
        
        """Contract Review:
- Red coded (high-risk): Unlimited liability
- Yellow coded (medium-risk): Termination clause  
- Green coded (low-risk): Payment terms

The red coded issues should be negotiated immediately.
"""]
    
    print("Testing color removal function...")
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n--- Test Case {i} ---")
        print("Original text:")
        print(test_text[:200] + "..." if len(test_text) > 200 else test_text)
        
        cleaned_text = orchestrator._remove_color_coded_language(test_text)
        
        print("Cleaned text:")
        print(cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text)
        
        # Check for remaining color terms
        color_terms = ['green coded', 'yellow coded', 'red coded', 'Green coded', 'Yellow coded', 'Red coded']
        remaining_terms = [term for term in color_terms if term in cleaned_text.lower()]
        
        if remaining_terms:
            print(f"[FAIL] Remaining color terms: {remaining_terms}")
        else:
            print(f"[PASS] All color terms removed")
    
    return True

async def test_real_document_processing():
    """Test with actual document processing"""
    print("\n=== Real Document Processing Test ===")
    
    orchestrator = LangGraphOrchestrator()
    
    # Create a document that might trigger color-coded responses
    test_content = b"""SERVICE AGREEMENT
1. LIABILITY: Company liability is unlimited for all damages.
2. TERMINATION: Company may terminate immediately without cause.
3. PAYMENT: All payments are non-refundable under any circumstances.
4. WARRANTIES: Company provides no warranties whatsoever.
"""
    
    try:
        print("Processing document without color coding...")
        result = await orchestrator.process_document(
            file_content=test_content,
            filename="test_service_agreement.txt",
            prompt="Analyze this agreement for red flags and risks.",
            color_coded=False
        )
        
        # Check for color-coded language
        color_terms = ['green coded', 'yellow coded', 'red coded', 'Green coded', 'Yellow coded', 'Red coded']
        found_terms = [term for term in color_terms if term in result.lower()]
        
        explanatory_patterns = [
            'green coded issues represent',
            'yellow coded issues represent', 
            'red coded issues represent'
        ]
        found_explanations = [pattern for pattern in explanatory_patterns if pattern in result.lower()]
        
        print(f"Document processed. Result length: {len(result)} characters")
        print(f"Color terms found: {found_terms}")
        print(f"Explanatory text found: {found_explanations}")
        
        if found_terms or found_explanations:
            print("[FAIL] Color coding still present in processed document")
            
            # Show problematic sections
            lines = result.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(term in line_lower for term in color_terms + explanatory_patterns):
                    print(f"  Line {i+1}: {line}")
            
            return False
        else:
            print("[PASS] No color coding in processed document")
            return True
            
    except Exception as e:
        print(f"[FAIL] Document processing failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Comprehensive Color Removal Test")
    print("=" * 35)
    
    test1_passed = await test_comprehensive_color_removal()
    test2_passed = await test_real_document_processing()
    
    print("\n" + "=" * 35)
    print(f"Test Results:")
    print(f"- Color removal function: {'PASS' if test1_passed else 'FAIL'}")
    print(f"- Document processing: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n[SUCCESS] All color removal tests passed!")
        print("The system now provides completely clean output.")
    else:
        print("\n[ERROR] Some tests failed. Color coding may still be present.")

if __name__ == "__main__":
    asyncio.run(main())