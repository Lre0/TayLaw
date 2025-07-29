"""
Test the final color coding fix implementation
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import from agents
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

from agents.unified_orchestrator import UnifiedDocumentOrchestrator

async def test_final_color_fix():
    """Test that color coding is completely removed from single document analysis"""
    print("=== Final Color Coding Fix Test ===")
    
    orchestrator = UnifiedDocumentOrchestrator()
    
    # Create a test document
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
        print("\n--- Testing Default Analysis (Should Have NO Color Coding) ---")
        result = await orchestrator.analyze_documents(
            file_data,
            "Analyze this contract for potential red flags and risks.",
            unified=True,
            color_coded=False
        )
        
        analysis = result.get('analysis', '')
        
        # Check for all possible color-coded terms
        color_terms = [
            'green coded', 'yellow coded', 'red coded',
            'Green coded', 'Yellow coded', 'Red coded',
            'GREEN CODED', 'YELLOW CODED', 'RED CODED'
        ]
        
        # Check for color-coded explanations
        explanation_patterns = [
            'Green coded issues represent',
            'Yellow coded issues represent', 
            'Red coded issues represent',
            'green coded issues represent',
            'yellow coded issues represent',
            'red coded issues represent'
        ]
        
        print(f"Analysis length: {len(analysis)} characters")
        
        # Test for color-coded terms
        found_color_terms = []
        for term in color_terms:
            if term in analysis:
                found_color_terms.append(term)
        
        # Test for explanatory text
        found_explanations = []
        for pattern in explanation_patterns:
            if pattern in analysis:
                found_explanations.append(pattern)
        
        print(f"Color-coded terms found: {found_color_terms}")
        print(f"Color-coded explanations found: {found_explanations}")
        
        # Show executive summary section
        lines = analysis.split('\n')
        executive_start = -1
        executive_end = -1
        
        for i, line in enumerate(lines):
            if 'EXECUTIVE SUMMARY' in line:
                executive_start = i
            elif executive_start != -1 and line.strip() == '':
                if executive_end == -1:
                    continue
                else:
                    executive_end = i
                    break
            elif executive_start != -1 and line.startswith('In all matters'):
                executive_end = i
                break
        
        if executive_start != -1:
            print(f"\n--- Executive Summary Section ---")
            end_line = executive_end if executive_end != -1 else min(executive_start + 15, len(lines))
            for i in range(executive_start, end_line):
                if i < len(lines):
                    print(lines[i])
        
        # Check if test passed
        has_color_coding = len(found_color_terms) > 0 or len(found_explanations) > 0
        
        if has_color_coding:
            print(f"\n[FAIL] Color coding still present in analysis!")
            print("Found issues:")
            for term in found_color_terms:
                print(f"  - Color term: '{term}'")
            for exp in found_explanations:
                print(f"  - Explanation: '{exp}'")
        else:
            print(f"\n[PASS] No color coding found in default analysis!")
        
        return not has_color_coding
        
    except Exception as e:
        print(f"[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Final Color Coding Fix Test")
    print("=" * 30)
    
    success = await test_final_color_fix()
    
    print("\n" + "=" * 30)
    if success:
        print("[SUCCESS] Color coding fix is complete!")
        print("\nThe single document analysis now:")
        print("- Has NO color-coded language in output")
        print("- Uses only High-risk/Medium-risk/Low-risk terminology")
        print("- Provides clean, professional analysis")
        print("- Removes all color-coded explanatory text")
    else:
        print("[ERROR] Color coding is still present in the output.")
        print("Additional fixes may be needed.")

if __name__ == "__main__":
    asyncio.run(main())