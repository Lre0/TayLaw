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
        """Simplified PDF extraction focusing on content preservation"""
        
        # Method 1: PyMuPDF plain text (most reliable)
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()  # Plain text only
                
                if page_text and page_text.strip():
                    cleaned = self._minimal_clean_text(page_text)
                    text_parts.append(cleaned)
            
            doc.close()
            
            if text_parts:
                result = '\n\n'.join(text_parts)
                print(f"PDF extraction successful: {len(result)} chars")
                return result
                
        except Exception as e:
            print(f"PyMuPDF failed: {e}")
        
        # Method 2: pdfplumber fallback
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_parts = []
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    
                    if page_text and page_text.strip():
                        cleaned = self._minimal_clean_text(page_text)
                        text_parts.append(cleaned)
                
                if text_parts:
                    result = '\n\n'.join(text_parts)
                    print(f"pdfplumber fallback successful: {len(result)} chars")
                    return result
                    
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
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
    
    def _minimal_clean_text(self, text: str) -> str:
        """Minimal text cleaning that only fixes critical issues"""
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