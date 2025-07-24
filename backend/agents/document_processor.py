import io
import PyPDF2
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
            return await self._extract_pdf_text(file_content)
        elif file_extension == 'docx':
            return await self._extract_docx_text(file_content)
        elif file_extension in ['txt', 'md']:
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF with improved formatting"""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            # Clean and format the extracted text
            cleaned_text = self._clean_extracted_text(page_text)
            text += cleaned_text + "\n\n"  # Add page break
        return text.strip()
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX with improved formatting"""
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Skip empty paragraphs
                cleaned_text = self._clean_extracted_text(paragraph.text)
                text += cleaned_text + "\n"
        return text.strip()
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text to improve readability"""
        if not text:
            return ""
        
        # Fix common PDF extraction issues
        
        # 1. Fix broken words with spaces (e.g., "Com m ercial" -> "Commercial")
        # Look for single letters followed by spaces within words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)', r'\1\2\3', text)  # 3 letter words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4', text)  # 4 letter words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4\5', text)  # 5 letter words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4\5\6', text)  # 6 letter words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4\5\6\7', text)  # 7 letter words
        text = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4\5\6\7\8', text)  # 8 letter words
        
        # 2. More targeted approach for common broken words
        common_fixes = {
            r'\bT e r m s\b': 'Terms',
            r'\bS e r v i c e\b': 'Service', 
            r'\bC o m m e r c i a l\b': 'Commercial',
            r'\bA g r e e m e n t\b': 'Agreement',
            r'\bC o n t r a c t\b': 'Contract',
            r'\bL i a b i l i t y\b': 'Liability',
            r'\bI n d e m n i f i c a t i o n\b': 'Indemnification',
            r'\bT e r m i n a t i o n\b': 'Termination',
            r'\bG o v e r n i n g\b': 'Governing',
            r'\bD i s p u t e\b': 'Dispute',
            r'\bR e s o l u t i o n\b': 'Resolution',
            r'\bC o n f i d e n t i a l\b': 'Confidential',
            r'\bI n t e l l e c t u a l\b': 'Intellectual',
            r'\bP r o p e r t y\b': 'Property',
            r'\bP a y m e n t\b': 'Payment',
            r'\bD e f i n i t i o n s\b': 'Definitions',
            r'\bS e c t i o n\b': 'Section',
            r'\bA r t i c l e\b': 'Article',
            r'\bC l a u s e\b': 'Clause',
            r'\bE x h i b i t\b': 'Exhibit',
            r'\bS c h e d u l e\b': 'Schedule',
        }
        
        for pattern, replacement in common_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # 3. Fix excessive whitespace while preserving intentional formatting
        # Remove multiple spaces (but preserve single spaces)
        text = re.sub(r' {3,}', '  ', text)  # Replace 3+ spaces with 2 spaces
        
        # 4. Fix line breaks and paragraph formatting
        # Remove single line breaks that break up sentences
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)
        
        # 5. Preserve proper section breaks but clean up excessive breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 6. Fix common punctuation issues from PDF extraction
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.,;:!?])([A-Z])', r'\1 \2', text)  # Add space after punctuation before capital letters
        
        # 7. Clean up any remaining multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
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