import os
import asyncio
from typing import Dict, Any, List
import time
import random

class MockRiskAnalyzer:
    """Mock risk analyzer that simulates comprehensive legal analysis without API calls"""
    
    def __init__(self):
        self.model = "mock-legal-analyzer"
    
    async def analyze_risks(self, document_text: str, user_prompt: str) -> str:
        """Generate mock comprehensive legal analysis"""
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(2, 6))
        
        # Analyze content to generate realistic findings
        findings = self._generate_realistic_findings(document_text)
        
        # Generate comprehensive mock analysis in the new legal format
        analysis = f"""
A. Commercial Terms of Service

1. Payment Terms and Fee Structure (Section 1): High risk due to limited customer protection against fee changes
Additional Guidance: The Terms of Service provide that fees are subject to unilateral changes with only 30 days notice. This creates potential for unexpected cost increases that could impact CLIENT's budget planning. The payment terms place full tax burden on the customer and include penalty interest charges. We recommend negotiating caps on fee increases and shared responsibility for tax obligations.

2. Termination Rights (Section 2): Medium-to-high risk due to asymmetric termination provisions
Additional Guidance: The service provider retains broad termination rights with minimal notice requirements, while customer termination rights are more restrictive. This creates operational uncertainty for CLIENT's business continuity. The immediate termination clause for material breach lacks adequate cure period protections. We recommend negotiating mutual termination rights and reasonable cure periods.

B. Liability and Risk Allocation

1. Liability Limitations (Section 3): High risk due to inadequate damage caps for business operations
Additional Guidance: The Terms limit Company's aggregate liability to fees paid in the preceding twelve months, which may be substantially less than actual business damages. This limitation could leave CLIENT exposed to significant unrecovered losses in case of service failures or data incidents. We recommend negotiating higher liability caps that reflect the true business impact of service disruption.

2. Consequential Damages Exclusion (Section 3): High risk exposure for business-critical operations
Additional Guidance: The Terms exclude all liability for consequential, indirect, incidental, and punitive damages. For business-critical services, this could include lost profits, business interruption, and reputational damage. CLIENT should consider whether these exclusions are appropriate given the service's importance to business operations.

3. Customer Indemnification (Section 3): Medium risk due to broad scope of indemnification obligations
Additional Guidance: CLIENT is required to indemnify Company against third-party claims arising from Customer's use of the Service. While this is common, the scope should be carefully reviewed to ensure it doesn't extend beyond reasonable use-related claims. We recommend negotiating mutual indemnification and carve-outs for Company's negligence or misconduct.

C. Data Processing and Privacy

1. Data Retention Policies (Section 4): Medium risk for data governance compliance
Additional Guidance: The Terms provide for 90-day data retention after termination, which may not align with CLIENT's data retention policies or regulatory requirements. Cross-border data transfers to worldwide service providers could raise compliance concerns under applicable privacy laws. We recommend ensuring data retention terms align with CLIENT's policies and that adequate data protection safeguards are in place.

D. Intellectual Property

1. Service Provider IP Rights (Section 5): Medium risk regarding customer data usage
Additional Guidance: The Terms grant the service provider broad rights to use customer data to improve the Service. While this is increasingly common, CLIENT should ensure this doesn't extend to confidential or proprietary information. We recommend clarifying the scope of permitted data use and ensuring adequate confidentiality protections.

E. Other Legal Issues

1. Service Warranties and Disclaimers (Overall): High risk due to "as is" service provision
Additional Guidance: The Terms disclaim most warranties and provide services "as is" without performance guarantees. For business-critical applications, this creates operational uncertainty and limits recourse for service deficiencies. CLIENT should consider negotiating appropriate service level commitments and warranties for the intended use case.
"""
        
        return analysis.strip()
    
    def _generate_realistic_findings(self, content: str) -> List[str]:
        """Generate realistic findings based on content analysis"""
        findings = []
        
        # Analyze content for common legal terms and generate appropriate findings
        if "liability" in content.lower():
            findings.extend([
                "HIGH RISK: Liability limitations may be inadequate for actual business damages",
                "MEDIUM RISK: Exclusion of consequential damages could leave customer exposed"
            ])
        
        if "termination" in content.lower() or "terminate" in content.lower():
            findings.extend([
                "HIGH RISK: Asymmetric termination rights favor the service provider",
                "MEDIUM RISK: Immediate termination rights provide insufficient protection"
            ])
        
        if "warranty" in content.lower() or "disclaim" in content.lower():
            findings.extend([
                "HIGH RISK: Warranty disclaimers leave customer without recourse for defective services",
                "MEDIUM RISK: 'As is' provisions create operational uncertainty"
            ])
        
        if "indemnif" in content.lower():
            findings.extend([
                "MEDIUM RISK: Customer indemnification obligations may be overly broad",
                "LOW RISK: Standard IP indemnification provided by service provider"
            ])
        
        if "arbitration" in content.lower():
            findings.extend([
                "MEDIUM RISK: Mandatory arbitration limits customer's legal options",
                "MEDIUM RISK: Jury waiver reduces customer leverage in disputes"
            ])
        
        if "fees" in content.lower() or "payment" in content.lower():
            findings.extend([
                "MEDIUM RISK: Unilateral fee modification rights favor provider",
                "LOW RISK: Standard payment terms are commercially reasonable"
            ])
        
        # Ensure we have sufficient findings
        if len(findings) < 3:
            findings.extend([
                "MEDIUM RISK: Agreement terms may require legal review for business appropriateness",
                "LOW RISK: Standard commercial terms present manageable risk with proper oversight"
            ])
        
        return findings[:8]  # Limit to reasonable number per chunk
    
    async def categorize_risks(self, analysis: str) -> Dict[str, List[str]]:
        """Categorize identified risks into different types"""
        categories = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "compliance": [],
            "financial": []
        }
        
        # Extract risks by category from analysis
        if "high risk" in analysis.lower():
            categories["high_risk"] = [
                "Liability limitations inadequate for business damages",
                "Asymmetric termination rights favor provider", 
                "Warranty disclaimers create operational uncertainty"
            ]
        
        if "medium risk" in analysis.lower():
            categories["medium_risk"] = [
                "Customer indemnification obligations overly broad",
                "Mandatory arbitration limits legal options",
                "Unilateral fee modification rights"
            ]
        
        if "compliance" in analysis.lower():
            categories["compliance"] = [
                "Customer bears primary regulatory compliance responsibility",
                "Export control requirements may be burdensome"
            ]
        
        if "financial" in analysis.lower() or "payment" in analysis.lower():
            categories["financial"] = [
                "Fee increase rights with minimal notice",
                "Customer tax and withholding obligations"
            ]
        
        return categories