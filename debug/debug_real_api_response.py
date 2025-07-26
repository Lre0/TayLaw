#!/usr/bin/env python3
"""
Debug script to examine actual API responses and finding extraction
"""

import asyncio
import os
import sys
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
sys.path.append('backend')

from agents.risk_analyzer import RiskAnalyzer
from agents.langgraph_orchestrator import LangGraphOrchestrator

async def debug_real_api_response():
    """Debug what the real API is returning"""
    
    print("=== REAL API RESPONSE DEBUG ===")
    print()
    
    # Sample legal text with obvious red flags
    legal_text = """
    COMMERCIAL TERMS OF SERVICE
    
    5. LIABILITY LIMITATIONS
    Provider's total liability under this Agreement shall not exceed the amounts paid by Customer in the twelve (12) months preceding the claim. Provider disclaims all warranties, express or implied, including merchantability and fitness for a particular purpose.
    
    6. TERMINATION
    Provider may suspend or terminate your access immediately upon notice for any reason or no reason. Customer may terminate with thirty (30) days written notice.
    
    7. INDEMNIFICATION
    Customer agrees to defend, indemnify and hold harmless Provider from any claims arising from Customer's use of the Services.
    """
    
    print("1. TESTING REAL API ANALYZER:")
    print("-" * 50)
    
    # Test real API
    analyzer = RiskAnalyzer()
    prompt = "Analyze this contract for red flags and legal risks that could harm the customer."
    
    try:
        print("Calling real API...")
        raw_response = await analyzer.analyze_risks(legal_text, prompt)
        
        print(f"API Response Length: {len(raw_response)} characters")
        print(f"API Response Type: {type(raw_response)}")
        print()
        print("2. RAW API RESPONSE:")
        print("-" * 50)
        print(raw_response)
        print()
        
        # Test the orchestrator's finding extraction
        print("3. TESTING FINDING EXTRACTION:")
        print("-" * 50)
        orchestrator = LangGraphOrchestrator()
        findings = orchestrator._extract_findings_from_analysis(raw_response, 0)
        
        print(f"Extracted {len(findings)} findings:")
        for i, finding in enumerate(findings):
            print(f"  Finding {i+1}:")
            print(f"    Severity: {finding['severity']}")
            print(f"    Description: {finding['description'][:100]}...")
            print(f"    Confidence: {finding.get('confidence', 'N/A')}")
            print()
        
        # Test pattern-based extraction specifically
        print("4. TESTING PATTERN MATCHING:")
        print("-" * 50)
        
        # Check if response contains risk indicators
        risk_patterns = [
            r'(?i)(high[- ]?risk|critical|severe|major concern)',
            r'(?i)(medium[- ]?risk|moderate|concerning)',
            r'(?i)(low[- ]?risk|minor|note)',
            r'(?i)(liability|termination|indemnif|warranty)',
            r'(?i)(risk|concern|issue|problem|flag)'
        ]
        
        for i, pattern in enumerate(risk_patterns):
            matches = re.findall(pattern, raw_response)
            print(f"Pattern {i+1} '{pattern}': {len(matches)} matches")
            if matches:
                print(f"  Matches: {matches[:3]}")  # Show first 3 matches
        
        print()
        print("5. ANALYZING RESPONSE STRUCTURE:")
        print("-" * 50)
        
        # Check response structure
        lines = raw_response.split('\n')
        print(f"Total lines: {len(lines)}")
        print(f"Non-empty lines: {len([l for l in lines if l.strip()])}")
        
        # Check for numbered sections
        numbered_sections = re.findall(r'^\d+\.', raw_response, re.MULTILINE)
        print(f"Numbered sections found: {len(numbered_sections)}")
        
        # Check for bullet points
        bullet_points = re.findall(r'^[-*•]\s', raw_response, re.MULTILINE)
        print(f"Bullet points found: {len(bullet_points)}")
        
        # Show first few lines for structure analysis
        print("\nFirst 10 lines of response:")
        for i, line in enumerate(lines[:10]):
            print(f"  Line {i+1}: {repr(line)}")
        
    except Exception as e:
        print(f"Error testing real API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_real_api_response())