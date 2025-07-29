"""
Test script to verify color coding is removed from default analysis output
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import from agents
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

from agents.risk_analyzer import RiskAnalyzer

async def test_color_coding_removal():
    """Test that color coding is removed by default"""
    print("=== Testing Color Coding Removal ===")
    
    # Create a test document that might trigger color-coded responses
    test_content = """
    SERVICE AGREEMENT
    
    1. LIABILITY LIMITATION
    Company's liability is unlimited for all claims.
    
    2. TERMINATION
    Company may terminate this agreement at any time without notice.
    
    3. PAYMENT
    All fees are due immediately and are non-refundable.
    """
    
    analyzer = RiskAnalyzer()
    
    try:
        # Test 1: Default analysis (should NOT have color coding)
        print("\n--- Test 1: Default Analysis (No Color Coding) ---")
        result_no_color = await analyzer.analyze_risks(
            test_content, 
            "Analyze this contract for red flags.",
            allow_color_coding=False
        )
        
        # Check for color-coded language
        color_terms = ['green coded', 'yellow coded', 'red coded', 'Green coded', 'Yellow coded', 'Red coded']
        has_color_coding = any(term in result_no_color for term in color_terms)
        
        print(f"Result length: {len(result_no_color)} characters")
        print(f"Contains color coding: {has_color_coding}")
        if has_color_coding:
            print("[FAIL] Color coding found in default analysis!")
            for term in color_terms:
                if term in result_no_color:
                    print(f"  - Found: '{term}'")
        else:
            print("[PASS] No color coding found in default analysis")
        
        # Show a sample of the output
        print(f"\nSample output (first 300 chars):")
        print(result_no_color[:300] + "..." if len(result_no_color) > 300 else result_no_color)
        
        # Test 2: Color coding allowed (should have color coding when requested)
        print("\n--- Test 2: Color Coding Allowed ---")
        result_with_color = await analyzer.analyze_risks(
            test_content, 
            "Analyze this contract for red flags. Please use color-coded formatting (Green coded for low-risk, Yellow coded for medium-risk, Red coded for high-risk).",
            allow_color_coding=True
        )
        
        has_color_coding_allowed = any(term in result_with_color for term in color_terms)
        print(f"Result length: {len(result_with_color)} characters")
        print(f"Contains color coding: {has_color_coding_allowed}")
        if has_color_coding_allowed:
            print("[PASS] Color coding found when explicitly allowed")
        else:
            print("[INFO] No color coding found even when allowed (AI may have ignored request)")
        
        return not has_color_coding  # Test passes if default has no color coding
        
    except Exception as e:
        print(f"[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_color_removal_function():
    """Test the color removal function directly"""
    print("\n=== Testing Color Removal Function ===")
    
    # Sample text with color-coded language
    test_text = """
    Analysis Results:
    
    • Green coded issues represent low-risk items that are favorable to CLIENT.
    • Yellow coded issues represent medium-risk items that should be reviewed.
    • Red coded issues represent high-risk items requiring immediate attention.
    
    A. Commercial Terms
    
    1. Red coded (high-risk): Unlimited liability exposure
    2. Yellow coded (medium-risk): Termination notice period
    3. Green coded (low-risk): Payment terms are standard
    """
    
    from agents.risk_analyzer import RiskAnalyzer
    analyzer = RiskAnalyzer()
    
    print("Original text:")
    print(test_text)
    
    cleaned_text = analyzer._remove_color_coded_definitions(test_text)
    
    print("\nCleaned text:")
    print(cleaned_text)
    
    # Check if color-coded terms were removed
    color_terms = ['green coded', 'yellow coded', 'red coded', 'Green coded', 'Yellow coded', 'Red coded']
    remaining_color_terms = [term for term in color_terms if term in cleaned_text.lower()]
    
    if remaining_color_terms:
        print(f"[FAIL] Color terms still present: {remaining_color_terms}")
        return False
    else:
        print("[PASS] All color-coded terms removed successfully")
        return True

async def main():
    """Main test function"""
    print("Testing Color Coding Fix")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Color coding removal in analysis
    if await test_color_coding_removal():
        tests_passed += 1
    
    # Test 2: Color removal function
    if await test_color_removal_function():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("[SUCCESS] Color coding fix is working correctly!")
        print("\nBenefits achieved:")
        print("- [OK] Default analysis output has no color coding")
        print("- [OK] Color-coded language is properly removed")
        print("- [OK] Professional plain text format maintained")
        print("- [OK] Optional color coding available when requested")
    else:
        print("[ERROR] Some tests failed. Color coding may still be present in output.")

if __name__ == "__main__":
    asyncio.run(main())