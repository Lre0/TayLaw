#!/usr/bin/env python3
"""
Debug script to test the full PDF processing pipeline with a real PDF
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
from agents.document_processor import DocumentProcessor

async def debug_pdf_analysis():
    """Debug the full PDF processing pipeline"""
    
    print("=== PDF ANALYSIS PIPELINE DEBUG ===")
    print()
    
    # Check if we have the Anthropic ToS PDF
    pdf_path = "anthropic-tos.md"  # Looks like you have this file
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found at: {pdf_path}")
        print("Available files:")
        for file in os.listdir('.'):
            if file.endswith(('.pdf', '.txt', '.md')):
                print(f"  - {file}")
        return
    
    print(f"1. READING FILE: {pdf_path}")
    print("-" * 50)
    
    # Read the file content
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    print(f"File size: {len(file_content)} bytes")
    
    # Test document processing
    print("\n2. TESTING DOCUMENT PROCESSOR:")
    print("-" * 50)
    
    processor = DocumentProcessor()
    try:
        doc_data = await processor.process_document(file_content, pdf_path)
        print(f"Extracted text length: {len(doc_data['text'])} characters")
        print(f"Word count: {doc_data['word_count']}")
        print("First 500 characters:")
        print(doc_data['text'][:500])
        print("...")
    except Exception as e:
        print(f"Document processing failed: {e}")
        return
    
    # Test orchestrator processing
    print("\n3. TESTING FULL ORCHESTRATOR PIPELINE:")
    print("-" * 50)
    
    orchestrator = LangGraphOrchestrator()
    prompt = "Analyze this document for red flags and legal risks that could harm the customer. Focus on liability limitations, termination rights, indemnification clauses, and other provisions that favor the service provider."
    
    try:
        print("Starting full pipeline analysis...")
        result = await orchestrator.process_document(file_content, pdf_path, prompt)
        
        print(f"Analysis completed!")
        print(f"Result length: {len(result)} characters")
        
        # Look for key indicators in the result
        print("\n4. ANALYZING RESULT CONTENT:")
        print("-" * 50)
        
        if "Total Findings: 0" in result:
            print("ISSUE FOUND: Result shows 0 findings")
        else:
            print("Result appears to have findings")
        
        if "0.50 confidence" in result or "Average Confidence: 0.50" in result:
            print("ISSUE FOUND: Low confidence scores (0.50) indicate no findings extracted")
        else:
            print("Confidence scores look normal")
        
        # Extract key metrics from result
        import re
        total_findings_match = re.search(r'Total Findings: (\d+)', result)
        if total_findings_match:
            findings_count = int(total_findings_match.group(1))
            print(f"Total findings reported: {findings_count}")
        
        confidence_matches = re.findall(r'(\d+\.\d+) confidence', result)
        if confidence_matches:
            confidences = [float(c) for c in confidence_matches]
            print(f"Confidence scores found: {confidences}")
        
        print("\n5. FULL RESULT:")
        print("-" * 50)
        print(result)
        
    except Exception as e:
        print(f"Orchestrator processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_pdf_analysis())