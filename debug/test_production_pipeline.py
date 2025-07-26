#!/usr/bin/env python3
"""
Test the exact same pipeline that the frontend uses
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
sys.path.append('backend')

from agents.langgraph_orchestrator import LangGraphOrchestrator

async def test_production_pipeline():
    """Test using the exact same method as the production API"""
    
    print("=== TESTING PRODUCTION PIPELINE (FastAPI Route) ===")
    print()
    
    pdf_path = "debug\\test-red-flags.pdf"
    
    # Read the PDF exactly like the FastAPI endpoint does
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    filename = "test-red-flags.pdf"
    prompt = "Analyze this document for red flags and legal risks that could harm the customer."
    
    print(f"File: {filename}")
    print(f"Size: {len(file_content)} bytes")
    print(f"Prompt: {prompt}")
    print()
    
    # Use the exact same orchestrator and method as main.py
    langgraph_orchestrator = LangGraphOrchestrator()
    
    try:
        print("Running production pipeline...")
        result = await langgraph_orchestrator.process_document(
            file_content=file_content,
            filename=filename,
            prompt=prompt
        )
        
        print("SUCCESS! Production pipeline completed.")
        print()
        
        # Extract key metrics
        import re
        
        findings_match = re.search(r'Total Findings: (\d+)', result)
        findings_count = int(findings_match.group(1)) if findings_match else 0
        
        efficiency_match = re.search(r'Parallel Processing Efficiency: (\d+)/(\d+)', result)
        if efficiency_match:
            successful = int(efficiency_match.group(1))
            total = int(efficiency_match.group(2))
            efficiency = f"{successful}/{total}"
        else:
            efficiency = "Unknown"
        
        print(f"PRODUCTION RESULTS:")
        print(f"- Total Findings: {findings_count}")
        print(f"- Processing Efficiency: {efficiency}")
        
        if findings_count > 0:
            print(f"✅ PRODUCTION PIPELINE IS WORKING!")
            print(f"Your TayLaw system should be finding {findings_count} red flag issues.")
        else:
            print(f"❌ PRODUCTION PIPELINE ISSUE CONFIRMED")
            print("The production pipeline is returning 0 findings.")
        
        # Show summary section
        summary_start = result.find("PARALLEL PROCESSING SUMMARY:")
        if summary_start != -1:
            summary_end = result.find("CHUNK-BY-CHUNK ANALYSIS:", summary_start)
            if summary_end != -1:
                summary = result[summary_start:summary_end].strip()
                print(f"\nProduction Summary:")
                print("-" * 50)
                print(summary)
        
    except Exception as e:
        print(f"Production pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_production_pipeline())