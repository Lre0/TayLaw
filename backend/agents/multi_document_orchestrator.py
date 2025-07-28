import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from .langgraph_orchestrator import LangGraphOrchestrator
from .agent_monitor import agent_monitor, AgentStatus, LogLevel

class DocumentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DocumentJob:
    """Individual document processing job"""
    job_id: str
    filename: str
    file_content: bytes
    prompt: str
    status: DocumentStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0

@dataclass
class BatchJob:
    """Batch of documents for processing"""
    batch_id: str
    documents: List[DocumentJob]
    created_at: float
    total_documents: int
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    completed_count: int = 0
    failed_count: int = 0
    cached_unified_analysis: Optional[str] = None

class DocumentProcessingQueue:
    """Queue manager for document processing with concurrency control"""
    
    def __init__(self, max_concurrent_documents: int = 5):
        self.max_concurrent = max_concurrent_documents
        self.active_jobs: Dict[str, DocumentJob] = {}
        self.batch_jobs: Dict[str, BatchJob] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_documents)
        self.orchestrator = LangGraphOrchestrator()
    
    async def create_batch(self, documents: List[Dict[str, Any]], prompt: str) -> str:
        """Create a new batch processing job"""
        batch_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create individual document jobs
        document_jobs = []
        for i, doc_info in enumerate(documents):
            job_id = f"{batch_id}_doc_{i}"
            document_job = DocumentJob(
                job_id=job_id,
                filename=doc_info['filename'],
                file_content=doc_info['file_content'],
                prompt=prompt,
                status=DocumentStatus.PENDING,
                created_at=current_time
            )
            document_jobs.append(document_job)
            self.active_jobs[job_id] = document_job
        
        # Create batch job
        batch_job = BatchJob(
            batch_id=batch_id,
            documents=document_jobs,
            created_at=current_time,
            total_documents=len(documents)
        )
        self.batch_jobs[batch_id] = batch_job
        
        await agent_monitor.log_activity(
            "Multi-Document Queue Manager",
            AgentStatus.PROCESSING,
            f"Created batch {batch_id[:8]} with {len(documents)} documents",
            LogLevel.INFO,
            metadata={"batch_id": batch_id, "document_count": len(documents)}
        )
        
        return batch_id
    
    async def process_batch(self, batch_id: str) -> BatchJob:
        """Process all documents in a batch with controlled concurrency"""
        batch_job = self.batch_jobs.get(batch_id)
        if not batch_job:
            raise ValueError(f"Batch {batch_id} not found")
        
        batch_job.started_at = time.time()
        
        await agent_monitor.log_activity(
            "Multi-Document Queue Manager",
            AgentStatus.PROCESSING,
            f"Starting parallel processing of batch {batch_id[:8]}",
            LogLevel.INFO,
            metadata={"batch_id": batch_id, "concurrency_limit": self.max_concurrent}
        )
        
        # Start parallel processing with concurrency control
        print(f"Creating {len(batch_job.documents)} processing tasks")
        tasks = []
        for i, document_job in enumerate(batch_job.documents):
            print(f"Creating task {i+1} for {document_job.filename}")
            task = self._process_single_document(document_job, batch_id)
            tasks.append(task)
        
        # Wait for all documents to complete
        print("Starting parallel processing...")
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print(f"Parallel processing completed. Results: {len(results)} items")
            
            # Check for exceptions in results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Task {i+1} failed with exception: {result}")
                else:
                    print(f"Task {i+1} completed successfully")
        except Exception as gather_error:
            print(f"asyncio.gather failed: {gather_error}")
            import traceback
            traceback.print_exc()
            raise gather_error
        
        batch_job.completed_at = time.time()
        batch_job.completed_count = len([d for d in batch_job.documents if d.status == DocumentStatus.COMPLETED])
        batch_job.failed_count = len([d for d in batch_job.documents if d.status == DocumentStatus.FAILED])
        
        processing_time = batch_job.completed_at - batch_job.started_at
        
        await agent_monitor.log_activity(
            "Multi-Document Queue Manager",
            AgentStatus.COMPLETED,
            f"Batch {batch_id[:8]} completed in {processing_time:.2f}s - {batch_job.completed_count}/{batch_job.total_documents} successful",
            LogLevel.SUCCESS if batch_job.failed_count == 0 else LogLevel.WARNING,
            metadata={
                "batch_id": batch_id,
                "processing_time": processing_time,
                "completed": batch_job.completed_count,
                "failed": batch_job.failed_count
            }
        )
        
        return batch_job
    
    async def _process_single_document(self, document_job: DocumentJob, batch_id: str):
        """Process a single document with semaphore control"""
        async with self.semaphore:  # Limit concurrent processing
            document_job.status = DocumentStatus.PROCESSING
            document_job.started_at = time.time()
            document_job.progress = 10.0
            
            await agent_monitor.log_activity(
                "Document Queue Processor",
                AgentStatus.PROCESSING,
                f"Starting analysis of {document_job.filename} (batch {batch_id[:8]})",
                LogLevel.INFO,
                metadata={
                    "batch_id": batch_id,
                    "document_id": document_job.job_id,
                    "filename": document_job.filename
                }
            )
            
            try:
                # Update progress
                document_job.progress = 30.0
                
                # Process document using existing orchestrator
                print(f"Processing document: {document_job.filename}")
                try:
                    result = await self.orchestrator.process_document(
                        file_content=document_job.file_content,
                        filename=document_job.filename,
                        prompt=document_job.prompt
                    )
                    print(f"Document processing successful for: {document_job.filename}")
                except Exception as process_error:
                    print(f"Document processing failed for {document_job.filename}: {process_error}")
                    import traceback
                    traceback.print_exc()
                    raise process_error
                
                # Success
                document_job.status = DocumentStatus.COMPLETED
                document_job.result = result
                document_job.progress = 100.0
                document_job.completed_at = time.time()
                
                processing_time = document_job.completed_at - document_job.started_at
                
                await agent_monitor.log_activity(
                    "Document Queue Processor",
                    AgentStatus.COMPLETED,
                    f"Completed analysis of {document_job.filename} in {processing_time:.2f}s",
                    LogLevel.SUCCESS,
                    metadata={
                        "batch_id": batch_id,
                        "document_id": document_job.job_id,
                        "filename": document_job.filename,
                        "processing_time": processing_time
                    }
                )
                
            except Exception as e:
                # Failure
                document_job.status = DocumentStatus.FAILED
                document_job.error = str(e)
                document_job.progress = 100.0
                document_job.completed_at = time.time()
                
                processing_time = document_job.completed_at - document_job.started_at
                
                await agent_monitor.log_activity(
                    "Document Queue Processor",
                    AgentStatus.ERROR,
                    f"Failed to analyze {document_job.filename}: {str(e)}",
                    LogLevel.ERROR,
                    metadata={
                        "batch_id": batch_id,
                        "document_id": document_job.job_id,
                        "filename": document_job.filename,
                        "processing_time": processing_time,
                        "error": str(e)
                    }
                )
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a batch"""
        batch_job = self.batch_jobs.get(batch_id)
        if not batch_job:
            return None
        
        return {
            "batch_id": batch_id,
            "total_documents": batch_job.total_documents,
            "completed_count": batch_job.completed_count,
            "failed_count": batch_job.failed_count,
            "started_at": batch_job.started_at,
            "completed_at": batch_job.completed_at,
            "documents": [
                {
                    "job_id": doc.job_id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "progress": doc.progress,
                    "started_at": doc.started_at,
                    "completed_at": doc.completed_at,
                    "error": doc.error
                }
                for doc in batch_job.documents
            ]
        }
    
    async def get_batch_results(self, batch_id: str, unified: bool = True) -> Optional[Dict[str, Any]]:
        """Get final results of a completed batch"""
        batch_job = self.batch_jobs.get(batch_id)
        if not batch_job:
            return None
        
        base_result = {
            "batch_id": batch_id,
            "total_documents": batch_job.total_documents,
            "completed": batch_job.completed_count,
            "failed": batch_job.failed_count,
            "processing_time": (batch_job.completed_at - batch_job.started_at) if batch_job.completed_at else None,
        }
        
        if unified:
            # Use cached unified analysis if available, otherwise generate it
            if batch_job.cached_unified_analysis is None:
                # DEBUG: Generating unified analysis for batch {batch_id} (first time)
                batch_job.cached_unified_analysis = await self._create_unified_analysis(batch_job)
            else:
                # DEBUG: Using cached unified analysis for batch {batch_id}
                pass
                
            base_result.update({
                "analysis_type": "unified",
                "unified_analysis": batch_job.cached_unified_analysis,
                "source_documents": [doc.filename for doc in batch_job.documents if doc.status == DocumentStatus.COMPLETED]
            })
        else:
            # Return individual results for each document
            base_result.update({
                "analysis_type": "individual",
                "results": [
                    {
                        "filename": doc.filename,
                        "status": "completed" if doc.status == DocumentStatus.COMPLETED else "failed",
                        "analysis": doc.result,
                        "error": doc.error,
                        "processing_time": (doc.completed_at - doc.started_at) if doc.completed_at and doc.started_at else None
                    }
                    for doc in batch_job.documents
                ]
            })
        
        return base_result
    
    async def _create_unified_analysis(self, batch_job: BatchJob) -> str:
        """Combine individual document analyses into a unified red flags report"""
        # DEBUG: Creating unified analysis for batch {batch_job.batch_id} - SHOULD ONLY HAPPEN ONCE
        completed_docs = [doc for doc in batch_job.documents if doc.status == DocumentStatus.COMPLETED and doc.result]
        
        if not completed_docs:
            return "No documents were successfully analyzed."
        
        # Parse and consolidate all red flags from individual analyses
        consolidated_issues = await self._consolidate_red_flags(completed_docs)
        
        # Create unified analysis report
        unified_report = f"""# Unified Red Flags Analysis Report

## Executive Summary
Multi-document consolidated analysis for {len(completed_docs)} document(s):
{chr(10).join(f"• {doc.filename}" for doc in completed_docs)}

## Processing Summary
- **Total Documents**: {batch_job.total_documents}
- **Successfully Analyzed**: {batch_job.completed_count}
- **Failed**: {batch_job.failed_count}
- **Processing Time**: {(batch_job.completed_at - batch_job.started_at):.2f} seconds

## Key Issues Identified

{consolidated_issues}

## Risk Assessment Summary
This unified analysis consolidates findings from all {len(completed_docs)} document(s) into a single comprehensive red flags report. Each issue listed above represents risks identified across the document set, with specific document references where the issues were found.

## Recommendations
1. Address critical and high-risk issues identified above as priority
2. Review moderate-risk items for potential business impact
3. Consider cumulative risk exposure across all analyzed documents
4. Implement standardized language improvements for future documents
"""
        
        return unified_report

    async def _consolidate_red_flags(self, completed_docs: List[DocumentJob]) -> str:
        """Parse individual analyses and consolidate into unified red flags list"""
        import re
        
        # Collect all individual analyses and check for error messages
        all_analyses = []
        error_analyses = []
        
        for doc in completed_docs:
            if doc.result:
                # Check if the result is an error message
                if doc.result.startswith("Error analyzing document after") or "attempts:" in doc.result:
                    error_analyses.append({
                        'filename': doc.filename,
                        'error': doc.result
                    })
                    # Error result for {doc.filename}: {doc.result[:100]}...
                else:
                    all_analyses.append({
                        'filename': doc.filename,
                        'content': doc.result
                    })
                    # Analysis received for {doc.filename}: {len(doc.result)} characters
            else:
                # No result for {doc.filename}
                pass
        
        # If we have error analyses, skip API consolidation and go straight to fallback
        if error_analyses:
            # Found {len(error_analyses)} error analyses, using fallback consolidation
            return self._simple_consolidation_fallback(completed_docs)
        
        if not all_analyses:
            # No analyses found - returning fallback message
            return "No issues identified in the analyzed documents."
        
        # Use RiskAnalyzer to consolidate findings into unified format
        try:
            from .risk_analyzer import RiskAnalyzer
            
            # Prepare consolidation prompt
            analyses_text = "\n\n---DOCUMENT SEPARATOR---\n\n".join([
                f"DOCUMENT: {analysis['filename']}\nANALYSIS:\n{analysis['content']}"
                for analysis in all_analyses
            ])
            
            consolidation_prompt = f"""You are a legal analysis consolidation expert. Your task is to take multiple individual document red flags analyses and create a single, unified list of key issues with detailed section references and actionable guidance.

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

• **[Next issue title if any]** (Section: [clause reference])
  - **Finding**: [Description]
  - **Risk**: [Risk explanation]
  - **Recommendation**: [Action guidance]

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

### Critical Issues
• **[Issue Title]** (Section: [clause reference])
  - **Finding**: [Description]
  - **Risk**: [Risk explanation]  
  - **Recommendation**: [Action guidance]

[Continue for all documents...]

IMPORTANT FORMATTING NOTES:
- Always include section/clause references when they can be identified from the source analysis
- If no section reference is available, use "(Section: Not specified)" 
- Each issue should have Finding, Risk, and Recommendation subsections
- If a document has no issues in a risk category, omit that section for that document
- If a document has no significant issues at all, state "No significant red flags identified in this document."
"""

            # Get consolidation using existing RiskAnalyzer
            risk_analyzer = RiskAnalyzer()
            # Consolidating {len(all_analyses)} analyses...
            
            # Log consolidation start
            from .agent_monitor import agent_monitor, AgentStatus, LogLevel
            await agent_monitor.log_activity(
                "Analysis Consolidation Agent",
                AgentStatus.PROCESSING,
                f"Consolidating findings from {len(all_analyses)} documents...",
                LogLevel.INFO
            )
            
            consolidated_result = await risk_analyzer.analyze_risks(analyses_text, consolidation_prompt)
            
            # Log consolidation completion
            await agent_monitor.log_activity(
                "Analysis Consolidation Agent",
                AgentStatus.COMPLETED,
                f"Consolidation complete - {len(consolidated_result)} characters generated",
                LogLevel.SUCCESS
            )
            
            # Consolidation complete: {len(consolidated_result)} characters
            
            return consolidated_result
            
        except Exception as e:
            print(f"Consolidation failed: {e}")
            # Fallback to simple consolidation if API fails
            fallback_result = self._simple_consolidation_fallback(completed_docs)
            # Using fallback consolidation
            return fallback_result

    def _simple_consolidation_fallback(self, completed_docs: List[DocumentJob]) -> str:
        """Enhanced fallback consolidation when Claude API is unavailable"""
        issues_found = []
        
        # Enhanced keyword search for legal issues
        risk_keywords = ['risk', 'issue', 'concern', 'problem', 'flag', 'liability', 'termination', 
                        'breach', 'violation', 'penalty', 'damages', 'disclaimer', 'limitation',
                        'exclusion', 'indemnify', 'indemnification', 'warranty', 'represent',
                        'compliance', 'regulatory', 'jurisdiction', 'governing law', 'dispute']
        
        for doc in completed_docs:
            if doc.result:
                doc_issues = []
                content_lower = doc.result.lower()
                
                # Look for any risk-related keywords in the entire document
                if any(keyword in content_lower for keyword in risk_keywords):
                    # Extract sentences that contain legal risk terms
                    sentences = doc.result.split('.')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in risk_keywords):
                            # Clean up sentence and truncate if too long
                            clean_sentence = sentence.replace('\n', ' ').strip()
                            if len(clean_sentence) > 150:
                                clean_sentence = clean_sentence[:150] + "..."
                            doc_issues.append(clean_sentence)
                            if len(doc_issues) >= 3:  # Limit to 3 issues per document
                                break
                
                # If we found legal content, include it
                if doc_issues:
                    issues_found.append(f"**{doc.filename}:**")
                    for issue in doc_issues:
                        issues_found.append(f"• {issue}")
                    issues_found.append("")  # Add spacing between documents
                else:
                    # Even if no keywords, check if there's substantial legal content
                    if len(doc.result) > 500:  # Substantial content
                        issues_found.append(f"**{doc.filename}:**")
                        issues_found.append(f"• Document analyzed - {len(doc.result)} characters of legal content processed")
                        issues_found.append("")
        
        if not issues_found:
            return "• No significant red flags identified across the analyzed documents"
            
        return "### Issues Identified Across Documents\n\n" + "\n".join(issues_found)

class MultiDocumentOrchestrator:
    """High-level orchestrator for multi-document analysis workflows"""
    
    def __init__(self, max_concurrent_documents: int = 5):
        self.queue = DocumentProcessingQueue(max_concurrent_documents)
        self.active_batches: Dict[str, str] = {}  # batch_id -> status
    
    async def analyze_multiple_documents(self, files_data: List[Dict[str, Any]], prompt: str, unified: bool = True) -> Dict[str, Any]:
        """Analyze multiple documents with full orchestration"""
        print(f"MultiDocumentOrchestrator: Starting analysis of {len(files_data)} documents")
        start_time = time.time()
        
        # Clear previous workflow history  
        print("Clearing agent monitor history")
        agent_monitor.clear_history()
        
        await agent_monitor.log_activity(
            "Multi-Document Orchestrator",
            AgentStatus.PROCESSING,
            f"Starting multi-document analysis workflow for {len(files_data)} documents (unified={unified})",
            LogLevel.INFO,
            metadata={"document_count": len(files_data), "unified_analysis": unified}
        )
        
        try:
            # Create batch
            print("Creating batch...")
            batch_id = await self.queue.create_batch(files_data, prompt)
            print(f"Batch created with ID: {batch_id}")
            self.active_batches[batch_id] = "processing"
            
            # Process batch
            print("Processing batch...")
            batch_job = await self.queue.process_batch(batch_id)
            print("Batch processing completed")
            self.active_batches[batch_id] = "completed"
            
            # Generate results with unified analysis by default
            print("Generating results...")
            results = await self.queue.get_batch_results(batch_id, unified=unified)
            print("Results generated successfully")
            
            total_time = time.time() - start_time
            
            await agent_monitor.log_activity(
                "Multi-Document Orchestrator",
                AgentStatus.COMPLETED,
                f"Multi-document analysis completed in {total_time:.2f}s with {'unified' if unified else 'individual'} results",
                LogLevel.SUCCESS,
                metadata={
                    "batch_id": batch_id,
                    "total_time": total_time,
                    "documents_processed": len(files_data),
                    "success_rate": f"{batch_job.completed_count}/{batch_job.total_documents}",
                    "analysis_type": "unified" if unified else "individual"
                }
            )
            
            return results
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Multi-Document Orchestrator",
                AgentStatus.ERROR,
                f"Multi-document analysis failed: {str(e)}",
                LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            raise e
    
    def get_active_batches(self) -> Dict[str, Any]:
        """Get information about all active batches"""
        return {
            batch_id: self.queue.get_batch_status(batch_id)
            for batch_id in self.active_batches.keys()
        }
    
    async def compare_documents(self, batch_id: str) -> Dict[str, Any]:
        """Compare documents within a batch (future enhancement)"""
        batch_job = self.queue.batch_jobs.get(batch_id)
        if not batch_job:
            raise ValueError(f"Batch {batch_id} not found")
        
        # Placeholder for document comparison logic
        # This would analyze the results from multiple documents and provide comparative insights
        comparison_result = {
            "batch_id": batch_id,
            "comparison_type": "risk_assessment_comparison",
            "documents_compared": batch_job.total_documents,
            "comparative_analysis": "Comparative analysis would be implemented here",
            "risk_level_distribution": {
                "high_risk_documents": 0,
                "medium_risk_documents": 0,
                "low_risk_documents": 0
            },
            "common_issues": [],
            "unique_issues": [],
            "recommendations": []
        }
        
        return comparison_result