"""
Enhanced PDF processor with header/footer removal and better formatting preservation
"""

import io
import fitz  # PyMuPDF
import pdfplumber
import re
from typing import List, Dict, Any, Set
from collections import Counter

class EnhancedPDFProcessor:
    """Enhanced PDF processor for legal documents with clean extraction"""
    
    def __init__(self):
        self.header_footer_patterns = []
        self.detected_headers_footers = set()
        
    async def extract_text_enhanced(self, file_content: bytes, filename: str) -> str:
        """Extract text with header/footer removal and better formatting"""
        
        print(f"Starting enhanced PDF extraction for {filename}")
        
        # Method 1: Try enhanced PyMuPDF extraction
        try:
            result = await self._extract_with_pymupdf_enhanced(file_content)
            if result and len(result.strip()) > 100:
                print(f"Enhanced PyMuPDF successful: {len(result)} chars")
                return result
        except Exception as e:
            print(f"Enhanced PyMuPDF failed: {e}")
        
        # Method 2: Fallback to enhanced pdfplumber
        try:
            result = await self._extract_with_pdfplumber_enhanced(file_content)
            if result and len(result.strip()) > 100:
                print(f"Enhanced pdfplumber successful: {len(result)} chars")
                return result
        except Exception as e:
            print(f"Enhanced pdfplumber failed: {e}")
        
        return "Error: Could not extract text from PDF"
    
    async def _extract_with_pymupdf_enhanced(self, file_content: bytes) -> str:
        """Enhanced PyMuPDF extraction with header/footer removal and formatting"""
        
        doc = fitz.open(stream=file_content, filetype="pdf")
        all_pages_text = []
        
        # First pass: collect all text to identify headers/footers
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            page_lines = self._extract_lines_with_position(text_dict, page_num)
            all_pages_text.append(page_lines)
        
        doc.close()
        
        # Identify headers and footers
        self._detect_headers_footers(all_pages_text)
        
        # Second pass: extract clean text
        doc = fitz.open(stream=file_content, filetype="pdf")
        clean_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            clean_text = self._extract_clean_page_text(text_dict, page_num)
            if clean_text.strip():
                clean_pages.append(clean_text)
        
        doc.close()
        
        # Combine and clean
        result = self._combine_and_clean_pages(clean_pages)
        return result
    
    async def _extract_with_pdfplumber_enhanced(self, file_content: bytes) -> str:
        """Enhanced pdfplumber extraction as fallback"""
        
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            all_pages_text = []
            
            # First pass: collect text to identify headers/footers
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
                if text:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    all_pages_text.append(lines)
                else:
                    all_pages_text.append([])
            
            # Detect headers/footers from pdfplumber text
            self._detect_headers_footers_simple(all_pages_text)
            
            # Second pass: extract clean text
            clean_pages = []
            for page_num, page in enumerate(pdf.pages):
                clean_text = self._extract_clean_pdfplumber_text(page, page_num)
                if clean_text.strip():
                    clean_pages.append(clean_text)
            
            result = self._combine_and_clean_pages(clean_pages)
            return result
    
    def _extract_lines_with_position(self, text_dict: dict, page_num: int) -> List[Dict]:
        """Extract lines with position information for header/footer detection"""
        lines_data = []
        page_height = text_dict.get("height", 800)
        
        if "blocks" not in text_dict:
            return lines_data
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                if "spans" not in line:
                    continue
                
                line_text = ""
                is_bold = False
                y_position = line.get("bbox", [0, 0, 0, 0])[1]  # Y coordinate
                
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        # Check for bold
                        flags = span.get("flags", 0)
                        font = span.get("font", "").lower()
                        if (flags & 16) or 'bold' in font:
                            is_bold = True
                        line_text += text + " "
                
                line_text = line_text.strip()
                if line_text:
                    lines_data.append({
                        "text": line_text,
                        "y_position": y_position,
                        "page_height": page_height,
                        "is_bold": is_bold,
                        "page_num": page_num,
                        "is_header": y_position < page_height * 0.15,  # Top 15% of page
                        "is_footer": y_position > page_height * 0.85   # Bottom 15% of page
                    })
        
        return lines_data
    
    def _detect_headers_footers(self, all_pages_text: List[List[Dict]]) -> None:
        """Detect repeating headers and footers across pages"""
        
        # Collect potential headers and footers
        header_candidates = []
        footer_candidates = []
        
        for page_lines in all_pages_text:
            # Top 15% of page lines as header candidates
            headers = [line for line in page_lines if line.get("is_header", False)]
            header_candidates.extend([line["text"] for line in headers])
            
            # Bottom 15% of page lines as footer candidates  
            footers = [line for line in page_lines if line.get("is_footer", False)]
            footer_candidates.extend([line["text"] for line in footers])
        
        # Find repeated lines (appear on 3+ pages)
        min_repetitions = max(3, len(all_pages_text) // 3)  # Appear on at least 1/3 of pages
        
        header_counts = Counter(header_candidates)
        footer_counts = Counter(footer_candidates)
        
        detected_headers = {text for text, count in header_counts.items() if count >= min_repetitions}
        detected_footers = {text for text, count in footer_counts.items() if count >= min_repetitions}
        
        # Also detect common web/document artifacts
        web_artifacts = {
            text for text in header_candidates + footer_candidates
            if any(pattern in text.lower() for pattern in [
                'http', 'www.', '.com', '.pdf', 'page', 'terms of service',
                'anthropic', 'commercial terms', 'version', '/', '\\',
                '4:07 pm', '5/19/25', 'effective', 'previous'
            ])
        }
        
        self.detected_headers_footers = detected_headers | detected_footers | web_artifacts
        
        print(f"Detected {len(self.detected_headers_footers)} header/footer patterns to remove")
        if self.detected_headers_footers:
            print("Sample patterns:", list(self.detected_headers_footers)[:3])
    
    def _detect_headers_footers_simple(self, all_pages_text: List[List[str]]) -> None:
        """Simple header/footer detection for pdfplumber text"""
        
        all_lines = []
        for page_lines in all_pages_text:
            # Consider first 3 and last 3 lines of each page as potential headers/footers
            if len(page_lines) > 6:
                all_lines.extend(page_lines[:3])  # Headers
                all_lines.extend(page_lines[-3:])  # Footers
        
        # Find lines that appear on multiple pages
        line_counts = Counter(all_lines)
        min_repetitions = max(3, len(all_pages_text) // 3)
        
        repeated_lines = {line for line, count in line_counts.items() if count >= min_repetitions}
        
        # Add web artifacts
        web_artifacts = {
            line for line in all_lines
            if any(pattern in line.lower() for pattern in [
                'http', 'www.', '.com', '.pdf', 'page', 'terms of service',
                'anthropic', 'commercial terms', 'version', '/', '\\',
                '4:07 pm', '5/19/25', 'effective', 'previous'
            ])
        }
        
        self.detected_headers_footers = repeated_lines | web_artifacts
        print(f"Simple detection found {len(self.detected_headers_footers)} header/footer patterns")
    
    def _extract_clean_page_text(self, text_dict: dict, page_num: int) -> str:
        """Extract clean text from page, removing headers/footers"""
        
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
                
                # Skip if this line is a detected header/footer
                if line_text and not self._is_header_footer(line_text):
                    # Detect section headers and preserve formatting
                    if self._is_legal_section_header(line_text):
                        if block_lines:  # Add spacing before section headers
                            block_lines.append("")
                        block_lines.append(line_text)
                        block_lines.append("")  # Add spacing after headers
                    else:
                        block_lines.append(line_text)
            
            if block_lines:
                block_text = '\n'.join(block_lines)
                lines.append(block_text)
        
        result = '\n\n'.join(lines)
        return self._clean_legal_text(result)
    
    def _extract_clean_pdfplumber_text(self, page, page_num: int) -> str:
        """Extract clean text from pdfplumber page"""
        
        text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
        if not text:
            return ""
        
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or self._is_header_footer(line):
                continue
            
            # Detect section headers
            if self._is_legal_section_header(line):
                if clean_lines and clean_lines[-1]:  # Add spacing before headers
                    clean_lines.append("")
                clean_lines.append(line)
                clean_lines.append("")  # Add spacing after headers
            else:
                clean_lines.append(line)
        
        result = '\n'.join(clean_lines)
        return self._clean_legal_text(result)
    
    def _is_header_footer(self, text: str) -> bool:
        """Check if text line is a detected header or footer"""
        text_clean = text.strip()
        
        # Direct match
        if text_clean in self.detected_headers_footers:
            return True
        
        # Partial match for flexible detection
        for pattern in self.detected_headers_footers:
            if len(pattern) > 10 and pattern in text_clean:
                return True
            if len(text_clean) > 10 and text_clean in pattern:
                return True
        
        return False
    
    def _is_legal_section_header(self, text: str) -> bool:
        """Enhanced detection of legal section headers"""
        text_clean = text.strip()
        text_upper = text_clean.upper()
        
        # Section letter patterns (A., B., C., etc.)
        if re.match(r'^[A-Z]\.\s+[A-Z]', text_clean):
            return True
        
        # Numbered sections
        if re.match(r'^\d+\.\s+[A-Z]', text_clean):
            return True
        
        # All caps headers (but filter out common words)
        if (len(text_upper) >= 5 and text_upper.isupper() and 
            not any(word in text_upper for word in ['SHALL', 'NOT', 'THE', 'AND', 'FOR', 'OF', 'WITH', 'WILL'])):
            return True
        
        
        # Common legal headers
        legal_headers = [
            'DEFINITIONS', 'TERMS', 'CONDITIONS', 'LIABILITY', 'TERMINATION',
            'INTELLECTUAL PROPERTY', 'CONFIDENTIALITY', 'GOVERNING LAW',
            'DISPUTE RESOLUTION', 'PAYMENT', 'WARRANTIES', 'INDEMNIFICATION',
            'SERVICES', 'CUSTOMER CONTENT', 'DATA PROCESSING', 'COMPLIANCE'
        ]
        
        return any(header in text_upper for header in legal_headers)
    
    def _is_likely_header_by_size(self, text: str, size: float) -> bool:
        """Detect if text is likely a header based on font size"""
        
        # If size is significantly larger than normal text (usually 12pt)
        if size >= 14:  # Headers are usually 14pt or larger
            return True
        
        # Check if text looks like a section header
        if re.match(r'^[A-Z\d]\.\s+[A-Z]', text):  # "A. SECTION" or "1. TITLE"
            return True
        
        # All caps short text at larger size
        if size >= 12 and len(text) < 50 and text.isupper():
            return True
        
        return False
    
    def _combine_and_clean_pages(self, pages: List[str]) -> str:
        """Combine pages and apply final cleaning"""
        
        if not pages:
            return ""
        
        # Join pages with appropriate spacing
        combined = '\n\n'.join(pages)
        
        # Final cleaning
        result = self._clean_legal_text(combined)
        
        print(f"Final result: {len(result)} characters")
        return result
    
    def _clean_legal_text(self, text: str) -> str:
        """Enhanced text cleaning for legal documents"""
        
        if not text:
            return ""
        
        # Fix broken lettered sections
        text = re.sub(r'\n([A-F])\.\s*\n', r'\n\n\1. ', text)
        
        # Fix numbered sections
        text = re.sub(r'(\d+)\s*\.\s*([A-Z])', r'\1. \2', text)
        
        # Fix broken words at line endings
        text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', text)
        
        # Normalize excessive whitespace
        text = re.sub(r' {3,}', ' ', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Ensure proper spacing around section markers
        text = re.sub(r'([a-z])(\n\n[A-F]\.)', r'\1\n\2', text)
        
        # Clean up quotation marks
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        return text.strip()

# Integration function for existing document processor
async def extract_pdf_enhanced(file_content: bytes, filename: str) -> str:
    """Enhanced PDF extraction function for integration"""
    processor = EnhancedPDFProcessor()
    return await processor.extract_text_enhanced(file_content, filename)