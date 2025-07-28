#!/usr/bin/env python3
"""
Test script to debug the truncation issue in unified analysis.
This will help identify where the text "The DPA grants Anthropic general authorization to engage sub-processors, but requires Anthropic to enter" is being cut off.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from agents.multi_document_orchestrator import MultiDocumentOrchestrator

async def test_chunking_debug():
    """Test the chunking and unified analysis with the actual PDFs to find truncation issue"""
    
    sample_files_dir = os.path.join(os.path.dirname(__file__), '..', 'sample-files')
    
    # File paths
    tos_file = os.path.join(sample_files_dir, 'Anthropic-tos.pdf')
    dpa_file = os.path.join(sample_files_dir, 'Anthropic-data-processing.pdf')
    
    print("DEBUG: Testing unified analysis truncation issue...")
    print(f"Files to test:")
    print(f"  1. {tos_file}")
    print(f"  2. {dpa_file}")
    print()
    
    # Check if files exist
    if not os.path.exists(tos_file):
        print(f"ERROR: TOS file not found: {tos_file}")
        return
    if not os.path.exists(dpa_file):
        print(f"ERROR: DPA file not found: {dpa_file}")
        return
    
    # Read the files
    files_data = []
    for file_path in [tos_file, dpa_file]:
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                files_data.append({
                    'filename': os.path.basename(file_path),
                    'file_content': file_content
                })
                print(f"SUCCESS: Loaded {os.path.basename(file_path)}: {len(file_content)} bytes")
        except Exception as e:
            print(f"ERROR: Failed to load {file_path}: {e}")
            return
    
    print()
    
    # Create orchestrator
    orchestrator = MultiDocumentOrchestrator(max_concurrent_documents=2)
    
    # Test prompt (same as the one causing issues)
    prompt = """You are a legal analysis expert. Analyze this document for potential red flags, risks, and legal issues that require attention. Focus on:

1. Liability and indemnification clauses
2. Termination and cancellation rights
3. Payment and financial obligations
4. Intellectual property and confidentiality
5. Dispute resolution and governing law
6. Any unusual or one-sided terms

Provide a detailed analysis with specific quotes from the document and recommendations for legal review."""

    try:
        print("STARTING: Multi-document analysis...")
        result = await orchestrator.analyze_multiple_documents(files_data, prompt, unified=True)
        
        # Debug: Print the actual result structure to understand what we're getting
        print("\nDEBUG: Raw result structure:")
        for key, value in result.items():
            if key == 'unified_analysis':
                print(f"  {key}: {len(str(value))} characters")
                print(f"    First 200 chars: {str(value)[:200]}...")
                print(f"    Last 200 chars: ...{str(value)[-200:]}")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "="*80)
        print("FINAL UNIFIED ANALYSIS RESULT:")
        print("="*80)
        
        unified_analysis = result.get('unified_analysis', 'No unified analysis found')
        print(f"Length of unified analysis: {len(unified_analysis)} characters")
        print()
        
        # Look specifically for the truncation issue
        if "The DPA grants Anthropic general authorization to engage sub-processors, but requires Anthropic to enter" in unified_analysis:
            print("WARNING: FOUND THE TRUNCATED TEXT! Let's see the context:")
            
            # Find the position and show surrounding text
            truncated_text = "The DPA grants Anthropic general authorization to engage sub-processors, but requires Anthropic to enter"
            position = unified_analysis.find(truncated_text)
            
            # Show 200 characters before and after
            start = max(0, position - 200)
            end = min(len(unified_analysis), position + len(truncated_text) + 200)
            context = unified_analysis[start:end]
            
            print(f"Position: {position}")
            print(f"Context around truncation:")
            print("-" * 40)
            print(context)
            print("-" * 40)
        else:
            print("DEBUG: Truncated text not found in unified analysis. Checking full result...")
            
            # Print the full unified analysis to see what we're getting
            print("FULL UNIFIED ANALYSIS:")
            print(unified_analysis)
        
        print(f"\nAnalysis Summary:")
        print(f"  - Analysis type: {result.get('analysis_type', 'unknown')}")
        print(f"  - Total documents: {result.get('total_documents', 0)}")
        print(f"  - Completed: {result.get('completed', 0)}")
        print(f"  - Failed: {result.get('failed', 0)}")
        print(f"  - Processing time: {result.get('processing_time', 0):.2f}s")
        
        source_docs = result.get('source_documents', [])
        print(f"  - Source documents: {source_docs}")
        
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chunking_debug())