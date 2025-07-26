#!/usr/bin/env python3
"""
Debug script to test the specific PDF that's giving 0 findings
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

async def test_your_pdf():
    """Test the specific PDF that's causing issues"""
    
    print("=== TESTING YOUR SPECIFIC PDF ===")
    print()
    
    pdf_path = "debug\\test-red-flags.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF not found at: {pdf_path}")
        return
    
    print(f"1. READING PDF: {pdf_path}")
    print("-" * 50)
    
    # Read the PDF file
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    print(f"PDF file size: {len(file_content)} bytes ({len(file_content)/1024:.1f} KB)")
    
    # Test document extraction
    print("\n2. TESTING PDF TEXT EXTRACTION:")
    print("-" * 50)
    
    processor = DocumentProcessor()
    try:
        doc_data = await processor.process_document(file_content, pdf_path)
        
        print(f"Extraction successful!")
        print(f"- Text length: {len(doc_data['text'])} characters")
        print(f"- Word count: {doc_data['word_count']}")
        print(f"- Character count: {doc_data['char_count']}")
        
        # Show first part of extracted text
        print(f"\nFirst 1000 characters of extracted text:")
        print("-" * 50)
        print(repr(doc_data['text'][:1000]))
        
        print(f"\nReadable preview (first 1000 chars):")
        print("-" * 50)
        print(doc_data['text'][:1000])
        
        # Check for common legal terms
        legal_terms = ['liability', 'termination', 'indemnif', 'warranty', 'agreement', 'contract', 'terms', 'service']
        found_terms = []
        for term in legal_terms:
            if term.lower() in doc_data['text'].lower():
                count = doc_data['text'].lower().count(term.lower())
                found_terms.append(f"{term}: {count}")
        
        print(f"\nLegal terms found:")
        print("-" * 50)
        if found_terms:
            for term_info in found_terms:
                print(f"  - {term_info}")
        else:
            print("  No common legal terms found - this might be the issue!")
        
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test chunking
    print(f"\n3. TESTING DOCUMENT CHUNKING:")
    print("-" * 50)
    
    orchestrator = LangGraphOrchestrator()
    chunks = orchestrator._create_intelligent_chunks(doc_data['text'], pdf_path)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk['content'])} chars, pages {chunk['page_range']}")
        print(f"    Section: {chunk['section_context']}")
        print(f"    Preview: {chunk['content'][:100]}...")
        print()
    
    # Test single chunk analysis
    print(f"4. TESTING SINGLE CHUNK ANALYSIS:")
    print("-" * 50)
    
    if chunks:
        test_chunk = chunks[0]  # Test first chunk
        prompt = "Analyze this document for red flags and legal risks that could harm the customer. Focus on liability limitations, termination rights, indemnification clauses, and other provisions that favor the service provider."
        
        try:
            print(f"Analyzing chunk 1 with {len(test_chunk['content'])} characters...")
            analyzed_chunk = await orchestrator._analyze_single_chunk(test_chunk, prompt)
            
            print(f"Analysis completed!")
            print(f"- Status: {analyzed_chunk['status']}")
            print(f"- Findings count: {len(analyzed_chunk['findings'])}")
            print(f"- Confidence: {analyzed_chunk['confidence_score']}")
            print(f"- Processing time: {analyzed_chunk['processing_time']:.2f}s")
            
            print(f"\nRaw API analysis output:")
            print("-" * 50)
            print(analyzed_chunk['risk_analysis'])
            
            if analyzed_chunk['findings']:
                print(f"\nExtracted findings:")
                print("-" * 50)
                for i, finding in enumerate(analyzed_chunk['findings']):
                    print(f"Finding {i+1}:")
                    print(f"  - Severity: {finding['severity']}")
                    print(f"  - Description: {finding['description'][:200]}...")
                    print(f"  - Confidence: {finding.get('confidence', 'N/A')}")
                    print()
            else:
                print(f"\nNO FINDINGS EXTRACTED!")
                print("This confirms the issue - API returned analysis but finding extraction failed.")
            
        except Exception as e:
            print(f"Chunk analysis failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test full pipeline
    print(f"\n5. TESTING FULL TAYLAW PIPELINE:")
    print("-" * 50)
    
    try:
        print("Running full TayLaw analysis pipeline...")
        result = await orchestrator.process_document(
            file_content, 
            "test-red-flags.pdf", 
            "Analyze this document for red flags and legal risks that could harm the customer."
        )
        
        # Extract key metrics
        import re
        
        # Look for findings count
        findings_match = re.search(r'Total Findings: (\d+)', result)
        findings_count = int(findings_match.group(1)) if findings_match else 0
        
        # Look for confidence scores
        confidence_matches = re.findall(r'(\d+\.\d+) confidence', result)
        avg_confidence = sum(float(c) for c in confidence_matches) / len(confidence_matches) if confidence_matches else 0
        
        print(f"PIPELINE RESULTS:")
        print(f"- Total findings: {findings_count}")
        print(f"- Average confidence: {avg_confidence:.2f}")
        
        if findings_count == 0:
            print(f"\nISSUE CONFIRMED: Full pipeline returned 0 findings!")
            print("This suggests the problem is in the finding extraction logic.")
        else:
            print(f"\nPipeline working correctly with {findings_count} findings!")
        
        # Show a portion of the result
        print(f"\nFirst 2000 characters of result:")
        print("-" * 50)
        print(result[:2000])
        
    except Exception as e:
        print(f"Full pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_your_pdf())