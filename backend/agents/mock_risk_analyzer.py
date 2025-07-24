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
        
        # Generate comprehensive mock analysis
        analysis = f"""
COMPREHENSIVE LEGAL RISK ASSESSMENT

EXECUTIVE SUMMARY:
This document section contains multiple high-risk provisions that significantly favor the service provider and expose the customer to substantial legal and business risks. The terms require immediate attention and negotiation.

LIABILITY AND INDEMNIFICATION ANALYSIS:
- HIGH RISK: Liability is severely limited to fees paid in previous 12 months, which may be inadequate for actual damages
- HIGH RISK: All consequential, incidental, and indirect damages are excluded, including lost profits and business interruption
- MEDIUM RISK: Customer bears indemnification obligations for third-party claims related to their use
- RECOMMENDATION: Negotiate higher liability caps and carve-outs for data breaches, IP infringement, and gross negligence

INTELLECTUAL PROPERTY RISKS:
- MEDIUM RISK: Service provider retains broad rights to use customer feedback and data
- MEDIUM RISK: Limited IP protections for customer-generated content
- LOW RISK: Standard IP indemnification provided by service provider
- RECOMMENDATION: Ensure stronger data ownership rights and restrict provider's use of customer data

TERMINATION AND CONTRACT DURATION:
- HIGH RISK: Service provider can terminate immediately with minimal notice requirements
- MEDIUM RISK: Asymmetric termination rights favor the provider
- MEDIUM RISK: Broad suspension rights allow provider to cut off service without customer consent
- RECOMMENDATION: Negotiate mutual termination rights and require reasonable cure periods

FINANCIAL AND PAYMENT RISKS:
- MEDIUM RISK: Fees are subject to unilateral changes with only 30 days notice
- MEDIUM RISK: Customer responsible for all taxes and withholding obligations
- LOW RISK: Standard payment terms and credit arrangements
- RECOMMENDATION: Cap fee increases and negotiate fixed-term pricing commitments

COMPLIANCE AND REGULATORY:
- MEDIUM RISK: Customer bears primary responsibility for regulatory compliance
- MEDIUM RISK: Export control and sanctions compliance requirements may be burdensome
- LOW RISK: Standard data processing agreement incorporated
- RECOMMENDATION: Ensure adequate compliance support and shared responsibility for regulatory changes

OPERATIONAL AND PERFORMANCE RISKS:
- HIGH RISK: No service level agreements or uptime guarantees
- HIGH RISK: "As is" provision with no warranties creates significant operational risk
- MEDIUM RISK: Limited recourse for service outages or performance issues
- RECOMMENDATION: Negotiate SLA commitments and service credits for downtime

BOILERPLATE AND GOVERNANCE:
- MEDIUM RISK: Mandatory arbitration limits customer's legal options
- MEDIUM RISK: Jury waiver and class action waiver reduce customer leverage
- LOW RISK: Standard governing law and venue provisions
- RECOMMENDATION: Preserve right to seek injunctive relief and negotiate arbitration alternatives

CRITICAL RED FLAGS IDENTIFIED:
1. Unlimited liability exclusions that could expose customer to uncapped risk
2. One-sided termination rights allowing immediate service cutoff
3. No warranties or SLA commitments for business-critical services
4. Broad indemnification obligations placing risk on customer
5. Unilateral right to modify terms with minimal notice

OVERALL RISK RATING: HIGH
This agreement strongly favors the service provider and contains multiple provisions that could result in significant business disruption, financial exposure, and operational risk for the customer organization.

IMMEDIATE RECOMMENDATIONS:
- Negotiate liability caps that reflect actual business impact
- Require mutual termination rights and reasonable cure periods  
- Demand service level commitments appropriate for business criticality
- Limit indemnification scope and add carve-outs for provider negligence
- Preserve customer's right to judicial remedies for critical disputes
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