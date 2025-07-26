#!/usr/bin/env python3
"""
Debug script to test PDF extraction methods and identify text gaps and font issues
"""

import io
import sys
import os
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

def test_pdf_extraction_methods(pdf_path):
    """Test all PDF extraction methods to compare results"""
    
    print(f"Testing PDF extraction methods on: {pdf_path}")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Method 1: Basic pdfplumber
    print("\n1. BASIC PDFPLUMBER EXTRACTION:")
    print("-" * 40)
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text1 = ""
            for page in pdf.pages[:2]:  # First 2 pages only
                page_text = page.extract_text()
                if page_text:
                    text1 += page_text + "\n\n"
        print(f"Length: {len(text1)} characters")
        print("First 500 characters:")
        print(repr(text1[:500]))
        print("\nActual text preview:")
        print(text1[:500])
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Advanced pdfplumber
    print("\n\n2. ADVANCED PDFPLUMBER EXTRACTION:")
    print("-" * 40)
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text2 = ""
            for page in pdf.pages[:2]:
                page_text = page.extract_text(
                    x_tolerance=2,
                    y_tolerance=3, 
                    layout=True,
                    keep_blank_chars=True,
                    use_text_flow=True
                )
                if page_text:
                    text2 += page_text + "\n\n"
        print(f"Length: {len(text2)} characters")
        print("First 500 characters:")
        print(repr(text2[:500]))
        print("\nActual text preview:")
        print(text2[:500])
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 3: PyMuPDF with font info
    print("\n\n3. PYMUPDF WITH FONT INFO:")
    print("-" * 40)
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text3 = ""
        font_info = []
        
        for page_num in range(min(2, len(doc))):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            page_text_parts = []
            
            if 'blocks' in blocks:
                for block in blocks['blocks']:
                    if 'lines' not in block:
                        continue
                        
                    for line in block['lines']:
                        if 'spans' not in line:
                            continue
                            
                        line_text = []
                        
                        for span in line['spans']:
                            span_text = span.get('text', '')
                            font_name = span.get('font', '')
                            font_flags = span.get('flags', 0)
                            font_size = span.get('size', 0)
                            
                            # Record font info for debugging
                            if span_text.strip():
                                font_info.append({
                                    'text': span_text[:20],
                                    'font': font_name,
                                    'flags': font_flags,
                                    'size': font_size,
                                    'is_bold': bool(font_flags & 2**4)
                                })
                            
                            # Add bold markers
                            is_bold = bool(font_flags & 2**4)
                            if is_bold and span_text.strip():
                                span_text = f"**{span_text}**"
                            
                            line_text.append(span_text)
                        
                        if line_text:
                            page_text_parts.append(''.join(line_text))
                
                if page_text_parts:
                    text3 += '\n'.join(page_text_parts) + "\n\n"
        
        doc.close()
        
        print(f"Length: {len(text3)} characters")
        print("First 500 characters:")
        print(repr(text3[:500]))
        print("\nActual text preview:")
        print(text3[:500])
        
        print("\nFont information (first 10 spans):")
        for i, info in enumerate(font_info[:10]):
            print(f"  {i+1}. Text: {repr(info['text'])} | Font: {info['font']} | Bold: {info['is_bold']} | Flags: {info['flags']}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 4: PyPDF2
    print("\n\n4. PYPDF2 EXTRACTION:")
    print("-" * 40)
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text4 = ""
        for page_num, page in enumerate(pdf_reader.pages[:2]):
            page_text = page.extract_text()
            if page_text:
                text4 += page_text + "\n\n"
        print(f"Length: {len(text4)} characters")
        print("First 500 characters:")
        print(repr(text4[:500]))
        print("\nActual text preview:")
        print(text4[:500])
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 5: PyMuPDF plain text
    print("\n\n5. PYMUPDF PLAIN TEXT:")
    print("-" * 40)
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text5 = ""
        for page_num in range(min(2, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text:
                text5 += page_text + "\n\n"
        doc.close()
        
        print(f"Length: {len(text5)} characters")
        print("First 500 characters:")
        print(repr(text5[:500]))
        print("\nActual text preview:")
        print(text5[:500])
    except Exception as e:
        print(f"Error: {e}")
    
    # Compare methods
    print("\n\n6. COMPARISON:")
    print("-" * 40)
    methods = [
        ("Basic pdfplumber", text1 if 'text1' in locals() else ""),
        ("Advanced pdfplumber", text2 if 'text2' in locals() else ""),
        ("PyMuPDF with fonts", text3 if 'text3' in locals() else ""),
        ("PyPDF2", text4 if 'text4' in locals() else ""),
        ("PyMuPDF plain", text5 if 'text5' in locals() else "")
    ]
    
    for name, text in methods:
        if text:
            word_count = len(text.split())
            line_count = len(text.split('\n'))
            print(f"{name}: {len(text)} chars, {word_count} words, {line_count} lines")
        else:
            print(f"{name}: Failed")

if __name__ == "__main__":
    # Test with a sample PDF file
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Look for PDF files in the current directory
        pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        if pdf_files:
            pdf_path = pdf_files[0]
            print(f"No PDF specified, using: {pdf_path}")
        else:
            print("Usage: python debug_pdf_extraction.py <path_to_pdf>")
            print("Or place a PDF file in the current directory")
            sys.exit(1)
    
    test_pdf_extraction_methods(pdf_path)