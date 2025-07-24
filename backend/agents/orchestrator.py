from typing import Dict, Any
from .document_processor import DocumentProcessor
from .risk_analyzer import RiskAnalyzer

class Orchestrator:
    """Orchestrates the multi-agent workflow for document analysis"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.risk_analyzer = RiskAnalyzer()
    
    async def process_document(self, file_content: bytes, filename: str, prompt: str) -> str:
        """Main workflow orchestration"""
        
        # Step 1: Process document to extract text
        document_data = await self.document_processor.process_document(
            file_content, filename
        )
        
        # Step 2: Analyze for risks
        risk_analysis = await self.risk_analyzer.analyze_risks(
            document_data["text"], prompt
        )
        
        # Step 3: Categorize risks (optional enhancement)
        risk_categories = await self.risk_analyzer.categorize_risks(risk_analysis)
        
        # Step 4: Format final response
        formatted_response = self._format_response(
            document_data, risk_analysis, risk_categories
        )
        
        return formatted_response
    
    def _format_response(self, document_data: Dict[str, Any], 
                        risk_analysis: str, risk_categories: Dict[str, Any]) -> str:
        """Format the final response for the user"""
        
        response = f"""
DOCUMENT ANALYSIS REPORT
========================

Document: {document_data['filename']}
Word Count: {document_data['word_count']}
Character Count: {document_data['char_count']}

RED FLAGS ANALYSIS:
{risk_analysis}

RISK SUMMARY:
- High Risk Issues: {len(risk_categories.get('high_risk', []))}
- Medium Risk Issues: {len(risk_categories.get('medium_risk', []))}
- Compliance Concerns: {len(risk_categories.get('compliance', []))}
- Financial Issues: {len(risk_categories.get('financial', []))}
        """
        
        return response