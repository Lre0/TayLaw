#!/usr/bin/env python3
"""
Debug script to test risk analysis and finding extraction
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

from agents.langgraph_orchestrator import LangGraphOrchestrator

async def debug_risk_analysis():
    """Debug the risk analysis pipeline"""
    
    print("=== TAYLAW RISK ANALYSIS DEBUG ===")
    print()
    
    # Sample contract text with obvious red flags
    sample_contract = """
    SAMPLE SERVICE AGREEMENT
    
    1. LIABILITY AND INDEMNIFICATION
    Provider's liability shall be limited to the total amount paid under this Agreement.
    Client agrees to indemnify and hold harmless Provider from any claims arising from the use of the delivered services.
    Provider disclaims all warranties, express or implied, including warranties of merchantability and fitness for purpose.
    
    2. TERMINATION
    Provider may terminate this Agreement immediately at any time without notice.
    Client may only terminate with 90 days written notice.
    Upon termination, all fees remain due and payable.
    
    3. PAYMENT TERMS
    Client agrees to pay all fees in advance.
    Provider reserves the right to modify pricing at any time with 5 days notice.
    All sales are final with no refunds under any circumstances.
    
    4. INTELLECTUAL PROPERTY
    All work product and deliverables remain the exclusive property of Provider.
    Client grants Provider unlimited rights to use any feedback or suggestions.
    """
    
    print("1. SAMPLE CONTRACT TEXT:")
    print("-" * 40)
    print(sample_contract)
    print()
    
    # Initialize orchestrator
    print("2. INITIALIZING ORCHESTRATOR...")
    orchestrator = LangGraphOrchestrator()
    
    # Test chunk creation
    print("3. TESTING CHUNK CREATION...")
    chunks = orchestrator._create_intelligent_chunks(sample_contract, "test-contract.txt")
    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk['content'])} characters")
        print(f"    Preview: {chunk['content'][:100]}...")
    print()
    
    # Test single chunk analysis
    print("4. TESTING SINGLE CHUNK ANALYSIS...")
    if chunks:
        test_chunk = chunks[0]
        prompt = "Analyze this contract for red flags and legal risks."
        
        try:
            print("Calling analyze_single_chunk...")
            analyzed_chunk = await orchestrator._analyze_single_chunk(test_chunk, prompt)
            
            print(f"Analysis completed. Status: {analyzed_chunk['status']}")
            print(f"Findings count: {len(analyzed_chunk['findings'])}")
            print(f"Confidence score: {analyzed_chunk['confidence_score']}")
            
            print("\n5. RAW RISK ANALYSIS OUTPUT:")
            print("-" * 40)
            print(analyzed_chunk['risk_analysis'])
            
            print("\n6. EXTRACTED FINDINGS:")
            print("-" * 40)
            for i, finding in enumerate(analyzed_chunk['findings']):
                print(f"Finding {i+1}:")
                print(f"  ID: {finding['id']}")
                print(f"  Severity: {finding['severity']}")
                print(f"  Description: {finding['description']}")
                print(f"  Confidence: {finding.get('confidence', 'N/A')}")
                print(f"  Evidence: {finding.get('evidence', 'N/A')[:100]}...")
                print()
            
        except Exception as e:
            print(f"Error during chunk analysis: {e}")
            import traceback
            traceback.print_exc()
    
    # Test pattern matching directly
    print("7. TESTING PATTERN MATCHING:")
    print("-" * 40)
    
    # Test the finding extraction patterns
    test_analysis = """
    HIGH RISK: Provider's liability is severely limited which could expose customer to significant financial risk.
    MEDIUM RISK: Termination rights are asymmetric and favor the provider.
    LOW RISK: Standard intellectual property provisions are included.
    The customer should negotiate better liability protections.
    """
    
    findings = orchestrator._extract_findings_from_analysis(test_analysis, 0)
    print(f"Pattern matching found {len(findings)} findings:")
    for finding in findings:
        print(f"  - {finding['severity'].upper()}: {finding['description']}")
    
    print("\n8. CHECKING ENVIRONMENT:")
    print("-" * 40)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"ANTHROPIC_API_KEY is set (length: {len(api_key)})")
    else:
        print("WARNING: ANTHROPIC_API_KEY is not set!")
        print("This could explain why no findings are being generated.")
    
    print("\nDEBUG COMPLETE")

if __name__ == "__main__":
    asyncio.run(debug_risk_analysis())