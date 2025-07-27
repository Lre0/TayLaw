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
    
    async def _extract_pdf_simple(self, file_content: bytes) -> str:
        """Enhanced PDF extraction with header/footer removal and better formatting"""
        
        # Method 1: Try enhanced processor first
        try:
            from .enhanced_pdf_processor import extract_pdf_enhanced
            result = await extract_pdf_enhanced(file_content, "document.pdf")
            if result and len(result.strip()) > 100 and not result.startswith("Error:"):
                print(f"Enhanced PDF processor successful: {len(result)} chars")
                return result
        except Exception as e:
            print(f"Enhanced PDF processor failed: {e}")
        
        # Method 2: PyMuPDF with enhanced formatting preservation (fallback)
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get structured text with formatting information
                text_dict = page.get_text("dict")
                page_text = self._extract_structured_text(text_dict, page_num + 1)
                
                if page_text and page_text.strip():
                    text_parts.append(page_text)
            
            doc.close()
            
            if text_parts:
                result = '\n\n'.join(text_parts)
                print(f"Enhanced PDF extraction successful: {len(result)} chars")
                return result
                
        except Exception as e:
            print(f"Enhanced PyMuPDF failed: {e}")
        
        # Method 3: pdfplumber with layout preservation
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_parts = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with layout preservation
                    page_text = self._extract_pdfplumber_formatted(page, page_num + 1)
                    
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                
                if text_parts:
                    result = '\n\n'.join(text_parts)
                    print(f"Enhanced pdfplumber extraction successful: {len(result)} chars")
                    return result
                    
        except Exception as e:
            print(f"Enhanced pdfplumber failed: {e}")
        
        # Method 4: Fallback to basic extraction
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text and page_text.strip():
                    cleaned = self._legal_document_clean_text(page_text)
                    text_parts.append(cleaned)
            
            doc.close()
            
            if text_parts:
                result = '\n\n'.join(text_parts)
                print(f"Fallback PDF extraction: {len(result)} chars")
                return result
                
        except Exception as e:
            print(f"Fallback extraction failed: {e}")
        
        return "Error: Could not extract text from PDF"
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX with improved formatting"""
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Skip empty paragraphs
                cleaned_text = self._minimal_clean_text(paragraph.text)
                text += cleaned_text + "\n"
        return text.strip()
    
    def _extract_structured_text(self, text_dict: dict, page_num: int) -> str:
        """Extract text from PyMuPDF dict format with formatting preservation"""
        lines = []
        
        if "blocks" not in text_dict:
            return ""
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            block_lines = []
            for line in block["lines"]:
                if "spans" not in line:
                    continue
                    
                line_text = ""
                
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        # Remove bold detection - just extract plain text
                        line_text += text + " "
                
                line_text = line_text.strip()
                if line_text:
                    # Preserve important line breaks for legal structure
                    if self._is_legal_header(line_text):
                        if block_lines:  # Add spacing before headers
                            block_lines.append("")
                        block_lines.append(line_text)
                        block_lines.append("")  # Add spacing after headers
                    else:
                        block_lines.append(line_text)
            
            if block_lines:
                # Join lines in block, preserving paragraph structure
                block_text = '\n'.join(block_lines)
                lines.append(block_text)
        
        result = '\n\n'.join(lines)
        return self._legal_document_clean_text(result)
    
    def _extract_pdfplumber_formatted(self, page, page_num: int) -> str:
        """Extract text from pdfplumber with layout preservation"""
        try:
            # Extract text with layout information
            text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
            
            if not text:
                return ""
            
            # Process the text to preserve legal document structure
            lines = text.split('\n')
            processed_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    processed_lines.append("")
                    continue
                
                # Detect legal headers and add proper spacing
                if self._is_legal_header(line):
                    if processed_lines and processed_lines[-1]:  # Add spacing before headers
                        processed_lines.append("")
                    processed_lines.append(line)
                    processed_lines.append("")  # Add spacing after headers
                else:
                    processed_lines.append(line)
            
            result = '\n'.join(processed_lines)
            return self._legal_document_clean_text(result)
            
        except Exception as e:
            print(f"pdfplumber formatted extraction error: {e}")
            # Fallback to basic text extraction
            return page.extract_text() or ""
    
    def _is_legal_header(self, text: str) -> bool:
        """Detect if text is likely a legal document header or section"""
        text_upper = text.upper().strip()
        
        # Common legal document patterns
        legal_patterns = [
            r'^\d+\.\s+[A-Z]',  # Numbered sections like "1. DEFINITIONS"
            r'^ARTICLE\s+[IVX]+',  # Article headers
            r'^SECTION\s+\d+',  # Section headers
            r'^\*\*.*\*\*$',  # Bold text markers
            r'DEFINITIONS?$',
            r'TERMS\s+AND\s+CONDITIONS',
            r'LIABILITY',
            r'TERMINATION',
            r'INTELLECTUAL\s+PROPERTY',
            r'CONFIDENTIALITY',
            r'GOVERNING\s+LAW',
            r'DISPUTE\s+RESOLUTION',
            r'PAYMENT\s+TERMS',
            r'WARRANTIES?',
            r'INDEMNIFICATION',
        ]
        
        # Check for all caps headers (but not regular sentences)
        if len(text_upper) >= 5 and text_upper.isupper() and not any(word in text_upper for word in ['SHALL', 'NOT', 'THE', 'AND', 'FOR', 'OF']):
            return True
        
        return any(re.search(pattern, text_upper) for pattern in legal_patterns)
    
    def _legal_document_clean_text(self, text: str) -> str:
        """Enhanced text cleaning for legal documents with formatting preservation"""
        if not text:
            return ""
        
        # Fix obvious OCR errors in legal terms
        legal_fixes = {
            'C o m m e r c i a l': 'Commercial',
            'T e r m s': 'Terms', 
            'S e r v i c e': 'Service',
            'A g r e e m e n t': 'Agreement',
            'L i a b i l i t y': 'Liability',
            'I n d e m n i f i c a t i o n': 'Indemnification',
            'C o n f i d e n t i a l': 'Confidential',
            'T e r m i n a t i o n': 'Termination',
            'G o v e r n i n g': 'Governing',
            'J u r i s d i c t i o n': 'Jurisdiction',
        }
        
        for broken, fixed in legal_fixes.items():
            text = text.replace(broken, fixed)
        
        # Fix broken numbered sections
        text = re.sub(r'(\d+)\s*\.\s*([A-Z])', r'\1. \2', text)
        
        # Fix excessive whitespace but preserve paragraph breaks
        text = re.sub(r' {3,}', ' ', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 consecutive newlines
        
        # Fix broken words at line endings (common PDF issue)
        text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', text)
        
        # Normalize line breaks - remove excessive internal spaces but preserve structure
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                cleaned_lines.append(line.strip())
            else:
                cleaned_lines.append("")
        
        text = '\n'.join(cleaned_lines)
        
        # Ensure proper spacing around legal section markers
        text = re.sub(r'([a-z])(\d+\.)\s*([A-Z])', r'\1\n\n\2 \3', text)
        
        return text.strip()
    
    def _minimal_clean_text(self, text: str) -> str:
        """Legacy minimal text cleaning - kept for compatibility"""
        if not text:
            return ""
        
        # Only fix obvious broken legal terms
        text = text.replace('C o m m e r c i a l', 'Commercial')
        text = text.replace('T e r m s', 'Terms')
        text = text.replace('S e r v i c e', 'Service')
        text = text.replace('A g r e e m e n t', 'Agreement')
        text = text.replace('L i a b i l i t y', 'Liability')
        
        # Minimal whitespace cleanup - only excessive spaces
        text = re.sub(r' {4,}', ' ', text)
        
        return text.strip()
    
    async def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process document and return structured data"""
        text = await self.extract_text(file_content, filename)
        
        return {
            "filename": filename,
            "text": text,
            "word_count": len(text.split()),
            "char_count": len(text)
        }