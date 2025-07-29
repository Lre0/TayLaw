import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from .langgraph_orchestrator import LangGraphOrchestrator
from .agent_monitor import agent_monitor, AgentStatus, LogLevel

class UnifiedDocumentOrchestrator:
    """Unified orchestrator that handles both single and multiple document analysis efficiently"""
    
    def __init__(self, max_concurrent_documents: int = 5):
        self.max_concurrent = max_concurrent_documents
        self.langgraph_orchestrator = LangGraphOrchestrator()
        self.semaphore = asyncio.Semaphore(max_concurrent_documents)
    
    async def analyze_documents(self, 
                              files_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                              prompt: str, 
                              unified: bool = True,
                              color_coded: bool = False) -> Dict[str, Any]:
        """
        Unified document analysis - handles single or multiple documents
        
        Args:
            files_data: Single file dict or list of file dicts with 'filename' and 'file_content'
            prompt: Analysis prompt
            unified: Whether to return unified analysis for multiple documents
            color_coded: Whether to use color-coded formatting (green/yellow/red)
        """
        start_time = time.time()
        
        # Normalize input to list format
        if isinstance(files_data, dict):
            # Single document
            files_list = [files_data]
            is_single_document = True
        else:
            # Multiple documents
            files_list = files_data
            is_single_document = False
        
        # Clear agent monitor history
        agent_monitor.clear_history()
        
        # Modify prompt if color coding is requested
        if color_coded:
            enhanced_prompt = f"{prompt}\n\nFORMATTING: Please use color-coded language in your analysis (Green coded for low-risk/favorable, Yellow coded for medium-risk, Red coded for high-risk issues)."
        else:
            enhanced_prompt = prompt

        await agent_monitor.log_activity(
            "Unified Document Orchestrator",
            AgentStatus.PROCESSING,
            f"Starting analysis of {len(files_list)} document(s) (color_coded={color_coded})",
            LogLevel.INFO,
            metadata={"document_count": len(files_list), "unified_analysis": unified, "color_coded": color_coded}
        )
        
        try:
            # Initialize failed_results for all cases
            failed_results = []
            
            # Process documents in parallel with controlled concurrency
            if len(files_list) == 1:
                # Single document - direct processing
                result = await self._process_single_document(files_list[0], enhanced_prompt, color_coded=color_coded)
                results = [result]
            else:
                # Multiple documents - parallel processing
                tasks = [
                    self._process_single_document_with_semaphore(file_data, enhanced_prompt, i, color_coded)
                    for i, file_data in enumerate(files_list)
                ]
                
                await agent_monitor.log_activity(
                    "Unified Document Orchestrator",
                    AgentStatus.PROCESSING,
                    f"Processing {len(tasks)} documents in parallel (max concurrent: {self.max_concurrent})",
                    LogLevel.INFO
                )
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any exceptions in results
                successful_results = []
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        await agent_monitor.log_activity(
                            "Unified Document Orchestrator",
                            AgentStatus.ERROR,
                            f"Document {i+1} ({files_list[i]['filename']}) failed: {str(result)}",
                            LogLevel.ERROR
                        )
                        failed_results.append({
                            'filename': files_list[i]['filename'],
                            'error': str(result),
                            'status': 'failed'
                        })
                    else:
                        successful_results.append(result)
                
                results = successful_results
            
            # Format response based on request type
            total_time = time.time() - start_time
            
            if is_single_document:
                # Single document response
                await agent_monitor.log_activity(
                    "Unified Document Orchestrator",
                    AgentStatus.COMPLETED,
                    f"Single document analysis completed in {total_time:.2f}s",
                    LogLevel.SUCCESS,
                    metadata={"processing_time": total_time}
                )
                return {
                    "analysis": results[0]['analysis'],
                    "processing_time": total_time,
                    "document": results[0]['filename']
                }
            
            elif unified and len(results) > 1:
                # Multiple documents with unified analysis
                unified_analysis = await self._create_unified_analysis(results, enhanced_prompt)
                
                await agent_monitor.log_activity(
                    "Unified Document Orchestrator",
                    AgentStatus.COMPLETED,
                    f"Unified analysis of {len(results)} documents completed in {total_time:.2f}s",
                    LogLevel.SUCCESS,
                    metadata={
                        "processing_time": total_time,
                        "documents_processed": len(results),
                        "analysis_type": "unified"
                    }
                )
                
                return {
                    "analysis_type": "unified",
                    "unified_analysis": unified_analysis,
                    "total_documents": len(files_list),
                    "successful": len(results),
                    "failed": len(failed_results),
                    "processing_time": total_time,
                    "source_documents": [r['filename'] for r in results],
                    "failed_documents": failed_results if failed_results else None
                }
            
            else:
                # Multiple documents with individual analyses
                await agent_monitor.log_activity(
                    "Unified Document Orchestrator",
                    AgentStatus.COMPLETED,
                    f"Individual analysis of {len(results)} documents completed in {total_time:.2f}s",
                    LogLevel.SUCCESS,
                    metadata={
                        "processing_time": total_time,
                        "documents_processed": len(results),
                        "analysis_type": "individual"
                    }
                )
                
                return {
                    "analysis_type": "individual",
                    "results": [
                        {
                            "filename": r['filename'],
                            "status": "completed",
                            "analysis": r['analysis'],
                            "processing_time": r['processing_time']
                        }
                        for r in results
                    ] + [
                        {
                            "filename": f['filename'],
                            "status": "failed",
                            "error": f['error'],
                            "analysis": None,
                            "processing_time": None
                        }
                        for f in failed_results
                    ],
                    "total_documents": len(files_list),
                    "successful": len(results),
                    "failed": len(failed_results),
                    "processing_time": total_time
                }
        
        except Exception as e:
            await agent_monitor.log_activity(
                "Unified Document Orchestrator",
                AgentStatus.ERROR,
                f"Analysis failed: {str(e)}",
                LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            raise e
    
    async def _process_single_document_with_semaphore(self, file_data: Dict[str, Any], prompt: str, index: int, color_coded: bool = False) -> Dict[str, Any]:
        """Process a single document with semaphore control for concurrency limiting"""
        async with self.semaphore:
            return await self._process_single_document(file_data, prompt, index, color_coded)
    
    async def _process_single_document(self, file_data: Dict[str, Any], prompt: str, index: Optional[int] = None, color_coded: bool = False) -> Dict[str, Any]:
        """Process a single document and return structured result"""
        start_time = time.time()
        filename = file_data['filename']
        file_content = file_data['file_content']
        
        doc_identifier = f"Document {index + 1}" if index is not None else filename
        
        await agent_monitor.log_activity(
            "Document Processor",
            AgentStatus.PROCESSING,
            f"Starting analysis of {doc_identifier} ({filename})",
            LogLevel.INFO,
            metadata={"filename": filename, "document_index": index}
        )
        
        try:
            # Use the existing LangGraph orchestrator for actual processing
            analysis = await self.langgraph_orchestrator.process_document(
                file_content=file_content,
                filename=filename,
                prompt=prompt,
                color_coded=color_coded
            )
            
            processing_time = time.time() - start_time
            
            await agent_monitor.log_activity(
                "Document Processor",
                AgentStatus.COMPLETED,
                f"Completed analysis of {doc_identifier} in {processing_time:.2f}s",
                LogLevel.SUCCESS,
                metadata={
                    "filename": filename,
                    "document_index": index,
                    "processing_time": processing_time
                }
            )
            
            return {
                "filename": filename,
                "analysis": analysis,
                "processing_time": processing_time,
                "status": "completed"
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            await agent_monitor.log_activity(
                "Document Processor",
                AgentStatus.ERROR,
                f"Failed to analyze {doc_identifier}: {str(e)}",
                LogLevel.ERROR,
                metadata={
                    "filename": filename,
                    "document_index": index,
                    "processing_time": processing_time,
                    "error": str(e)
                }
            )
            
            raise e
    
    async def _create_unified_analysis(self, successful_results: List[Dict[str, Any]], original_prompt: str) -> str:
        """Create unified analysis from multiple document results"""
        if not successful_results:
            return "No documents were successfully analyzed."
        
        if len(successful_results) == 1:
            return successful_results[0]['analysis']
        
        await agent_monitor.log_activity(
            "Analysis Consolidation Agent",
            AgentStatus.PROCESSING,
            f"Consolidating findings from {len(successful_results)} documents...",
            LogLevel.INFO
        )
        
        try:
            # Use the same consolidation logic as the original multi-document orchestrator
            consolidated_issues = await self._consolidate_analyses(successful_results)
            
            # Create unified analysis report
            unified_report = f"""# Unified Analysis Report

## Executive Summary
Multi-document consolidated analysis for {len(successful_results)} document(s):
{chr(10).join(f"• {result['filename']}" for result in successful_results)}

## Processing Summary
- **Total Documents**: {len(successful_results)}
- **Successfully Analyzed**: {len(successful_results)}
- **Total Processing Time**: {sum(r['processing_time'] for r in successful_results):.2f} seconds

## Consolidated Findings

{consolidated_issues}

## Risk Assessment Summary
This unified analysis consolidates findings from all {len(successful_results)} document(s) into a single comprehensive report. Each issue listed above represents risks identified across the document set, with specific document references where the issues were found.

## Recommendations
1. Address critical and high-risk issues identified above as priority
2. Review moderate-risk items for potential business impact
3. Consider cumulative risk exposure across all analyzed documents
4. Implement standardized language improvements for future documents
"""
            
            await agent_monitor.log_activity(
                "Analysis Consolidation Agent",
                AgentStatus.COMPLETED,
                f"Consolidation complete - {len(unified_report)} characters generated",
                LogLevel.SUCCESS
            )
            
            return unified_report
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Analysis Consolidation Agent",
                AgentStatus.ERROR,
                f"Consolidation failed: {str(e)}",
                LogLevel.ERROR
            )
            # Fallback to simple concatenation
            return self._simple_consolidation_fallback(successful_results)
    
    async def _consolidate_analyses(self, results: List[Dict[str, Any]]) -> str:
        """Consolidate individual analyses using AI when possible"""
        try:
            from .risk_analyzer import RiskAnalyzer
            
            # Prepare consolidation input
            analyses_text = "\n\n---DOCUMENT SEPARATOR---\n\n".join([
                f"DOCUMENT: {result['filename']}\nANALYSIS:\n{result['analysis']}"
                for result in results
            ])
            
            consolidation_prompt = f"""You are a legal analysis consolidation expert. Your task is to take multiple individual document analyses and create a single, unified list of key issues with detailed section references and actionable guidance.

INDIVIDUAL ANALYSES:
{analyses_text}

CONSOLIDATION INSTRUCTIONS:
1. Review all the individual document analyses above
2. Extract the key red flags and issues from each document
3. Organize findings by document first, then by risk level within each document
4. For each document, categorize issues as: Critical, High Risk, Moderate Risk, Low Risk
5. Present each issue with specific section/clause references when available
6. Include actionable commentary and guidance for each issue
7. Focus on actionable legal risks and concerns

FORMAT YOUR RESPONSE EXACTLY AS:

## [Document 1 Name]

### Critical Issues
• **[Issue Title]** (Section: [clause/section reference if available])
  - **Finding**: [Detailed description of the issue]
  - **Risk**: [Explanation of the legal risk or concern]
  - **Recommendation**: [Specific action or consideration for addressing this issue]

### High Risk Issues  
• **[Issue Title]** (Section: [clause/section reference if available])
  - **Finding**: [Detailed description of the issue]
  - **Risk**: [Explanation of the legal risk or concern] 
  - **Recommendation**: [Specific action or consideration for addressing this issue]

### Moderate Risk Issues
• **[Issue Title]** (Section: [clause/section reference if available])
  - **Finding**: [Detailed description of the issue]
  - **Risk**: [Explanation of the legal risk or concern]
  - **Recommendation**: [Specific action or consideration for addressing this issue]

### Low Risk Issues
• **[Issue Title]** (Section: [clause/section reference if available])
  - **Finding**: [Detailed description of the issue]
  - **Risk**: [Explanation of the legal risk or concern]
  - **Recommendation**: [Specific action or consideration for addressing this issue]

## [Document 2 Name]

[Continue for all documents...]

IMPORTANT FORMATTING NOTES:
- Always include section/clause references when they can be identified from the source analysis
- If no section reference is available, use "(Section: Not specified)" 
- Each issue should have Finding, Risk, and Recommendation subsections
- If a document has no issues in a risk category, omit that section for that document
- If a document has no significant issues at all, state "No significant red flags identified in this document."
"""

            # Get consolidation using RiskAnalyzer
            risk_analyzer = RiskAnalyzer()
            consolidated_result = await risk_analyzer.analyze_risks(analyses_text, consolidation_prompt)
            
            return consolidated_result
            
        except Exception as e:
            print(f"AI consolidation failed: {e}")
            return self._simple_consolidation_fallback(results)
    
    def _simple_consolidation_fallback(self, results: List[Dict[str, Any]]) -> str:
        """Simple fallback consolidation when AI is unavailable"""
        consolidated_sections = []
        
        for result in results:
            filename = result['filename']
            analysis = result['analysis']
            
            # Extract key sections from each analysis
            consolidated_sections.append(f"## {filename}")
            consolidated_sections.append("")
            
            # Simple extraction of key content
            if "HIGH RISK" in analysis.upper() or "CRITICAL" in analysis.upper():
                consolidated_sections.append("### High Priority Issues Identified")
            elif "MEDIUM RISK" in analysis.upper() or "MODERATE" in analysis.upper():
                consolidated_sections.append("### Moderate Priority Issues Identified")
            else:
                consolidated_sections.append("### Issues Identified")
            
            # Extract first few meaningful lines as summary
            lines = analysis.split('\n')
            meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 50 and not line.startswith('=')]
            
            for line in meaningful_lines[:5]:  # Limit to first 5 meaningful lines
                if line:
                    consolidated_sections.append(f"• {line}")
            
            consolidated_sections.append("")
        
        return "\n".join(consolidated_sections)