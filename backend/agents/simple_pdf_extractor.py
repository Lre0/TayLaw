"""
Simplified PDF extraction to fix text gaps and font issues
"""

import io
import fitz  # PyMuPDF
import pdfplumber

def extract_pdf_simple(file_content: bytes) -> str:
    """Simple, reliable PDF extraction focusing on content preservation"""
    
    # Method 1: PyMuPDF plain text (most reliable for content)
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            if page_text and page_text.strip():
                # Minimal cleaning - just normalize whitespace
                cleaned = ' '.join(page_text.split())
                text_parts.append(cleaned)
        
        doc.close()
        
        if text_parts:
            result = '\n\n'.join(text_parts)
            print(f"PyMuPDF plain extraction: {len(result)} chars")
            return result
            
    except Exception as e:
        print(f"PyMuPDF failed: {e}")
    
    # Method 2: pdfplumber fallback
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text_parts = []
            
            for page in pdf.pages:
                # Use basic extraction without complex parameters
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    # Minimal cleaning
                    cleaned = ' '.join(page_text.split())
                    text_parts.append(cleaned)
            
            if text_parts:
                result = '\n\n'.join(text_parts)
                print(f"pdfplumber extraction: {len(result)} chars")
                return result
                
    except Exception as e:
        print(f"pdfplumber failed: {e}")
    
    return "Error: Could not extract text from PDF"

def test_extraction(pdf_path: str):
    """Test the simple extraction method"""
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    result = extract_pdf_simple(content)
    print(f"\nExtracted text length: {len(result)}")
    print(f"First 500 characters:\n{result[:500]}")
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_extraction(sys.argv[1])
    else:
        print("Usage: python simple_pdf_extractor.py <pdf_file>")