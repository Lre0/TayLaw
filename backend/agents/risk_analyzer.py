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
        
        system_prompt = """You are an experienced legal advisor conducting a comprehensive contract risk assessment. Provide analysis in the structured professional format used by law firms for client reporting.

        CRITICAL REQUIREMENTS:
        - Quote exact text from the document that supports each finding
        - Assess materiality of each risk to the client organization
        - Provide specific, actionable recommendations for contract negotiation
        - Use professional legal language appropriate for in-house counsel and legal teams
        
        MANDATORY RISK CATEGORIZATION:
        You MUST use these exact risk level terms in your analysis:
        • High Risk: Matters which are of significant risk and require immediate attention and likely contract negotiation
        • Medium Risk: Matters which are of moderate risk to CLIENT in the circumstances and should be reviewed  
        • Low Risk: Matters which are favorable to CLIENT, or for which there are likely adequate protections in place

        CRITICAL: Do NOT include any explanatory text about "Green coded", "Yellow coded", or "Red coded" issues in your response. 
        Do NOT include lines like "• Green coded issues represent..." or "• Red coded issues represent..." in your analysis.
        Use ONLY the High Risk/Medium Risk/Low Risk terminology above unless the user's prompt explicitly requests color-coded language.

        LEGAL ANALYSIS CATEGORIES:
        A. Commercial Terms of Service
           - Payment terms, fees, pricing adjustments
           - Service levels, performance standards, availability guarantees
           - Termination rights, notice periods, consequences of termination
           - Contract duration, renewal terms, modification procedures

        B. Data Processing and Privacy  
           - Data collection, use, and retention policies
           - Cross-border data transfers and international compliance
           - Data subject rights and breach notification requirements
           - Third-party data sharing and sub-processor arrangements

        C. Liability and Risk Allocation
           - Liability caps, exclusions, and unlimited liability exposures
           - Indemnification obligations and scope
           - Insurance requirements and coverage adequacy
           - Force majeure and risk of loss provisions

        D. Intellectual Property
           - IP ownership and assignment provisions
           - Licensing terms and usage rights
           - Confidentiality and trade secret protection
           - Patent, copyright, and trademark considerations

        E. Compliance and Regulatory
           - Audit rights and compliance monitoring
           - Regulatory compliance requirements
           - Dispute resolution mechanisms and governing law
           - Export control and sanctions compliance

        F. Other Legal Issues
           - Assignment and change of control provisions
           - Publicity and marketing rights
           - Representations, warranties, and disclaimers
           - Notice provisions and communication requirements

        REQUIRED OUTPUT FORMAT:
        Structure your analysis with lettered main sections (A., B., C., etc.) and numbered subsections:

        A. [Category Name]

        1. [Issue Title] (Section X.Y): [One line summary of risk level and key concern]
        Additional Guidance: [Detailed legal analysis explaining the provision, its implications, and specific business risks. Include relevant legal context and precedent where applicable. Explain why this matters for the client's business operations and legal position.]

        2. [Next Issue Title] (Section X.Y): [One line summary]
        Additional Guidance: [Detailed analysis...]

        B. [Next Category]...

        ANALYSIS REQUIREMENTS:
        - Reference specific document sections where issues are found
        - Provide one-line summaries followed by detailed "Additional Guidance"
        - Assess materiality from CLIENT's business perspective
        - Include specific negotiation recommendations where risks are identified
        - Quote exact document language that creates the risk
        - Explain legal implications in business terms that non-lawyers can understand

        IMPORTANT: Focus on provisions that could materially impact CLIENT's business operations, legal compliance, or financial position. Include both adverse provisions and any notably client-favorable terms.
        
        OUTPUT FORMAT: Use ONLY "High Risk", "Medium Risk", and "Low Risk" terminology. Do not add any definitions or explanations about color-coded systems unless specifically requested by the user."""
        
        combined_prompt = f"""
        DOCUMENT ANALYSIS REQUEST:
        {user_prompt}
        
        DOCUMENT CONTENT TO ANALYZE:
        {document_text[:8000]}  # Increased for better analysis
        
        INSTRUCTIONS:
        Analyze this document section and identify specific legal risks. Quote the exact text that supports each finding.
        Focus on findings where you can cite specific clauses or provisions from the document text above.
        
        REMINDER: Use High Risk/Medium Risk/Low Risk categories only. Do not include color-coded explanations."""
        
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
                
                # Post-process to remove any color-coded definitions
                result = response.content[0].text
                print(f"BEFORE post-processing: {result[:200]}...")
                result = self._remove_color_coded_definitions(result)
                print(f"AFTER post-processing: {result[:200]}...")
                
                return result
                
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
    
    def _remove_color_coded_definitions(self, text: str) -> str:
        """Remove color-coded definitions from AI response"""
        import re
        
        # Remove lines that define color-coded categories
        patterns_to_remove = [
            r'•\s*Green coded issues represent.*?\n',
            r'•\s*Yellow coded issues represent.*?\n', 
            r'•\s*Red coded issues represent.*?\n',
            r'•\s*Green coded issues.*?adequate protections in place\.\s*\n',
            r'•\s*Yellow coded issues.*?circumstances\.\s*\n',
            r'•\s*Red coded issues.*?circumstances\.\s*\n'
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Also replace any remaining color-coded references in the executive summary
        text = re.sub(r'Red coded \(high-risk\)', 'High-risk', text)
        text = re.sub(r'Yellow coded \(medium-risk\)', 'Medium-risk', text)
        text = re.sub(r'Green coded \(low-risk/favorable\)', 'Low-risk/favorable', text)
        
        return text
    
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