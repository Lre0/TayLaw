import os
import asyncio
from anthropic import Anthropic
from typing import Dict, Any, List
import time

class RiskAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Use Haiku for maximum speed - optimized for fast legal analysis
        self.model = "claude-3-haiku-20240307"
    
    async def analyze_risks(self, document_text: str, user_prompt: str) -> str:
        """Analyze document for legal risks and red flags with timeout and retry logic"""
        
        system_prompt = """You are an experienced legal advisor conducting a contract risk assessment. Analyze the document text and provide structured findings.

        CRITICAL REQUIREMENT: You must quote the exact text from the document that supports each finding. Do not make assumptions about what might be missing.

        FOCUS AREAS - Analyze these key risk categories:
        1. LIABILITY: Caps, exclusions, unlimited liability exposures
        2. INTELLECTUAL PROPERTY: Ownership, licensing, confidentiality gaps  
        3. TERMINATION: Rights, notice periods, consequences
        4. FINANCIAL: Payment terms, penalties, cost escalations
        5. COMPLIANCE: Data protection, regulatory requirements
        6. PERFORMANCE: SLAs, delivery timelines, dispute resolution

        REQUIRED OUTPUT FORMAT:
        For each finding, use this exact structure:

        FINDING [number]:
        SEVERITY: [HIGH/MEDIUM/LOW]
        CATEGORY: [One of the 6 categories above]
        DESCRIPTION: [Clear description of the specific issue found]
        DOCUMENT_QUOTE: "[Exact text from document that supports this finding]"
        BUSINESS_IMPACT: [Specific business consequences]
        RECOMMENDATION: [Specific action recommended]

        IMPORTANT: Only report findings where you can quote specific text from the document. Do not report on clauses that are missing unless you can quote related text."""
        
        combined_prompt = f"""
        DOCUMENT ANALYSIS REQUEST:
        {user_prompt}
        
        DOCUMENT CONTENT TO ANALYZE:
        {document_text[:8000]}  # Increased for better analysis
        
        INSTRUCTIONS:
        Analyze this document section and identify specific legal risks. Quote the exact text that supports each finding.
        Focus on findings where you can cite specific clauses or provisions from the document text above."""
        
        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Add timeout wrapper around the API call - aggressive timeout for speed
                response = await asyncio.wait_for(
                    self._make_api_call(system_prompt, combined_prompt),
                    timeout=8.0  # 8 second timeout for maximum speed
                )
                
                processing_time = time.time() - start_time
                print(f"Risk analysis completed in {processing_time:.2f}s (attempt {attempt + 1})")
                
                return response.content[0].text
                
            except asyncio.TimeoutError:
                error_msg = f"API call timed out after 8 seconds (attempt {attempt + 1}/{max_retries})"
                print(error_msg)
                if attempt == max_retries - 1:
                    return f"Error: Analysis timed out after {max_retries} attempts. Please try with a smaller document or contact support."
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                error_msg = f"API call failed: {str(e)} (attempt {attempt + 1}/{max_retries})"
                print(error_msg)
                if attempt == max_retries - 1:
                    return f"Error analyzing document after {max_retries} attempts: {str(e)}"
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
    
    async def _make_api_call(self, system_prompt: str, combined_prompt: str):
        """Make the actual API call - separated for timeout handling"""
        return self.client.messages.create(
            model=self.model,
            max_tokens=1200,  # Aggressive optimization for speed
            temperature=0.1,  # Lower temperature for more consistent legal analysis
            system=system_prompt,
            messages=[
                {"role": "user", "content": combined_prompt}
            ]
        )
    
    async def categorize_risks(self, analysis: str) -> Dict[str, List[str]]:
        """Categorize identified risks into different types"""
        # Simple categorization - can be enhanced with more sophisticated NLP
        categories = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "compliance": [],
            "financial": []
        }
        
        # Basic keyword-based categorization
        if "liability" in analysis.lower():
            categories["high_risk"].append("Liability concerns identified")
        
        if "termination" in analysis.lower():
            categories["medium_risk"].append("Termination clause issues")
        
        if "payment" in analysis.lower():
            categories["financial"].append("Payment terms require review")
        
        return categories