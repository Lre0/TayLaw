import io
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from docx import Document
from typing import Dict, Any
import re

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from uploaded document"""
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return await self._extract_pdf_simple(file_content)
        elif file_extension == 'docx':
            return await self._extract_docx_text(file_content)
        elif file_extension in ['txt', 'md']:
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF with improved formatting and font awareness"""
        try:
            # First try advanced pdfplumber extraction with better parameters
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                
                for page_num, page in enumerate(pdf.pages):
                    # Try multiple extraction methods for best results
                    page_text = self._extract_page_with_formatting(page)
                    
                    if page_text:
                        # Less aggressive cleaning to preserve content
                        cleaned_text = self._clean_extracted_text_conservative(page_text)
                        text += cleaned_text + "\n\n"
                    else:
                        # Fallback to basic extraction if formatted extraction fails
                        basic_text = page.extract_text()
                        if basic_text:
                            cleaned_text = self._clean_extracted_text_conservative(basic_text)
                            text += cleaned_text + "\n\n"
                
                return text.strip()
                
        except Exception as e:
            print(f"pdfplumber extraction failed, trying PyMuPDF: {e}")
            # Try PyMuPDF for better font handling
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                text = ""
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Get text with formatting information
                    blocks = page.get_text("dict")
                    page_text = self._extract_from_pymupdf_blocks(blocks)
                    
                    if page_text:
                        cleaned_text = self._clean_extracted_text_conservative(page_text)
                        text += cleaned_text + "\n\n"
                
                doc.close()
                return text.strip()
                
            except Exception as e2:
                print(f"PyMuPDF extraction failed, trying PyPDF2: {e2}")
                # Final fallback to PyPDF2
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            cleaned_text = self._clean_extracted_text_conservative(page_text)
                            text += cleaned_text + "\n\n"
                    return text.strip()
                except Exception as e3:
                    print(f"All PDF extraction methods failed: {e3}")
                    return "Error: Could not extract text from PDF"
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX with improved formatting"""
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Skip empty paragraphs
                cleaned_text = self._clean_extracted_text(paragraph.text)
                text += cleaned_text + "\n"
        return text.strip()
    
    def _extract_page_with_formatting(self, page) -> str:
        """Extract text with better formatting awareness"""
        try:
            # Method 1: Advanced text extraction with layout preservation
            text = page.extract_text(
                x_tolerance=2,      # Horizontal tolerance for character grouping
                y_tolerance=3,      # Vertical tolerance for line grouping  
                layout=True,        # Preserve layout information
                keep_blank_chars=True,  # Keep spaces that might be meaningful
                use_text_flow=True  # Follow text flow for better ordering
            )
            
            if text and len(text.strip()) > 50:  # Good extraction
                return text
                
        except Exception as e:
            print(f"Advanced extraction failed: {e}")
        
        try:
            # Method 2: Character-level extraction with font awareness
            chars = page.chars
            if chars:
                return self._reconstruct_text_with_fonts(chars)
        except Exception as e:
            print(f"Character-level extraction failed: {e}")
        
        # Method 3: Basic extraction as final fallback
        return page.extract_text() or ""
    
    def _reconstruct_text_with_fonts(self, chars) -> str:
        """Reconstruct text preserving font information for better formatting"""
        if not chars:
            return ""
        
        text_parts = []
        current_line_y = None
        current_text = ""
        
        for char in chars:
            char_text = char.get('text', '')
            char_y = char.get('y0', 0)
            
            # Detect line breaks based on y-coordinate changes
            if current_line_y is not None and abs(char_y - current_line_y) > 3:
                if current_text.strip():
                    text_parts.append(current_text.strip())
                current_text = char_text
            else:
                current_text += char_text
            
            current_line_y = char_y
        
        # Add the last line
        if current_text.strip():
            text_parts.append(current_text.strip())
        
        return '\n'.join(text_parts)
    
    def _clean_extracted_text_conservative(self, text: str) -> str:
        """Conservative text cleaning that preserves more content"""
        if not text:
            return ""
        
        # More conservative cleaning approach
        
        # 1. Only fix obvious broken words (be more selective)
        # Fix 2-3 character broken words more carefully
        text = re.sub(r'\b([A-Z])\s+([a-z])\s+([a-z])\b', r'\1\2\3', text)  # "C o m" -> "Com"
        text = re.sub(r'\b([A-Z][a-z])\s+([a-z])\s+([a-z])\b', r'\1\2\3', text)  # "Co m" -> "Com"
        
        
        # 2. Only fix well-known problematic legal terms with spacing
        critical_fixes = {
            r'\bT e r m s\b': 'Terms',
            r'\bS e r v i c e\b': 'Service', 
            r'\bC o m m e r c i a l\b': 'Commercial',
            r'\bA g r e e m e n t\b': 'Agreement',
            r'\bL i a b i l i t y\b': 'Liability'
        }
        
        for pattern, replacement in critical_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # 3. Minimal whitespace cleanup - preserve document structure
        # Only fix truly excessive spacing
        text = re.sub(r' {4,}', '   ', text)  # 4+ spaces -> 3 spaces (preserve some formatting)
        
        # 4. Preserve line breaks - only fix obvious sentence breaks
        text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)  # Only lowercase to lowercase
        
        # 5. Minimal paragraph cleanup
        text = re.sub(r'\n{4,}', '\n\n', text)  # Only fix excessive breaks
        
        # 6. Fix only obvious punctuation issues
        text = re.sub(r' +([.,;])', r'\1', text)  # Space before punctuation
        
        return text.strip()
    
    def _extract_from_pymupdf_blocks(self, blocks) -> str:
        \"\"\"Extract text from PyMuPDF blocks with font awareness\"\"\"
        text_parts = []
        
        if not blocks or 'blocks' not in blocks:
            return \"\"
        
        for block in blocks['blocks']:
            if 'lines' not in block:
                continue
                
            block_text = []
            
            for line in block['lines']:
                if 'spans' not in line:
                    continue
                    
                line_text = []
                
                for span in line['spans']:
                    span_text = span.get('text', '')
                    font_flags = span.get('flags', 0)
                    
                    # Check for bold formatting (font flags bit 4)
                    is_bold = bool(font_flags & 2**4)
                    
                    # Preserve bold formatting with markdown-style markers
                    if is_bold and span_text.strip():
                        span_text = f\"**{span_text}**\"
                    
                    line_text.append(span_text)
                
                if line_text:
                    block_text.append(''.join(line_text))
            
            if block_text:
                text_parts.append('\\n'.join(block_text))
        
        return '\\n\\n'.join(text_parts)
    
    def _clean_extracted_text(self, text: str) -> str:
        \"\"\"Legacy cleaning method - now calls conservative version\"\"\"
        return self._minimal_clean_text(text)\n    \n    def _minimal_clean_text(self, text: str) -> str:\n        \"\"\"Minimal text cleaning that only fixes critical issues\"\"\"\n        if not text:\n            return \"\"\n        \n        # Only fix obvious broken legal terms\n        text = text.replace('C o m m e r c i a l', 'Commercial')\n        text = text.replace('T e r m s', 'Terms')\n        text = text.replace('S e r v i c e', 'Service')\n        text = text.replace('A g r e e m e n t', 'Agreement')\n        \n        # Minimal whitespace cleanup - only excessive spaces\n        import re\n        text = re.sub(r' {4,}', ' ', text)\n        \n        return text.strip()
    
    async def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process document and return structured data"""
        text = await self.extract_text(file_content, filename)
        
        return {
            "filename": filename,
            "text": text,
            "word_count": len(text.split()),
            "char_count": len(text)
        }