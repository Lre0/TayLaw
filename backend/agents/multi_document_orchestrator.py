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
        tasks = []
        for document_job in batch_job.documents:
            task = self._process_single_document(document_job, batch_id)
            tasks.append(task)
        
        # Wait for all documents to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
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
                result = await self.orchestrator.process_document(
                    file_content=document_job.file_content,
                    filename=document_job.filename,
                    prompt=document_job.prompt
                )
                
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
    
    def get_batch_results(self, batch_id: str, unified: bool = True) -> Optional[Dict[str, Any]]:
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
            # Return unified analysis combining all documents
            unified_analysis = self._create_unified_analysis(batch_job)
            base_result.update({
                "analysis_type": "unified",
                "unified_analysis": unified_analysis,
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
    
    def _create_unified_analysis(self, batch_job: BatchJob) -> str:
        """Combine individual document analyses into a unified red flags report"""
        completed_docs = [doc for doc in batch_job.documents if doc.status == DocumentStatus.COMPLETED and doc.result]
        
        if not completed_docs:
            return "No documents were successfully analyzed."
        
        # Collect all red flags and findings from individual analyses
        all_red_flags = []
        document_summaries = []
        
        for doc in completed_docs:
            analysis = doc.result
            if analysis:
                # Extract red flags and important findings from each document's analysis
                document_summaries.append(f"**{doc.filename}**: Analyzed successfully")
                
                # Add the analysis content with document identification
                all_red_flags.append(f"\n### Analysis from {doc.filename}\n{analysis}")
        
        # Create unified analysis report
        unified_report = f"""# Unified Red Flags Analysis Report

## Executive Summary
Multi-document analysis completed for {len(completed_docs)} document(s):
{chr(10).join(f"• {doc.filename}" for doc in completed_docs)}

## Processing Summary
- **Total Documents**: {batch_job.total_documents}
- **Successfully Analyzed**: {batch_job.completed_count}
- **Failed**: {batch_job.failed_count}
- **Processing Time**: {(batch_job.completed_at - batch_job.started_at):.2f} seconds

## Comprehensive Red Flags Analysis
The following analysis combines red flags and risk assessments from all documents:

{"".join(all_red_flags)}

## Overall Risk Assessment
This report consolidates findings from {len(completed_docs)} document(s). Each document's specific findings are included above with clear document identification. Review each section carefully for document-specific risks and considerations.

## Next Steps
1. Review each document-specific analysis above
2. Prioritize high-risk findings across all documents
3. Consider cumulative risk exposure across the document set
4. Address critical issues identified in any of the analyzed documents
"""
        
        return unified_report

class MultiDocumentOrchestrator:
    """High-level orchestrator for multi-document analysis workflows"""
    
    def __init__(self, max_concurrent_documents: int = 5):
        self.queue = DocumentProcessingQueue(max_concurrent_documents)
        self.active_batches: Dict[str, str] = {}  # batch_id -> status
    
    async def analyze_multiple_documents(self, files_data: List[Dict[str, Any]], prompt: str, unified: bool = True) -> Dict[str, Any]:
        """Analyze multiple documents with full orchestration"""
        start_time = time.time()
        
        await agent_monitor.log_activity(
            "Multi-Document Orchestrator",
            AgentStatus.PROCESSING,
            f"Starting multi-document analysis workflow for {len(files_data)} documents (unified={unified})",
            LogLevel.INFO,
            metadata={"document_count": len(files_data), "unified_analysis": unified}
        )
        
        try:
            # Create batch
            batch_id = await self.queue.create_batch(files_data, prompt)
            self.active_batches[batch_id] = "processing"
            
            # Process batch
            batch_job = await self.queue.process_batch(batch_id)
            self.active_batches[batch_id] = "completed"
            
            # Generate results with unified analysis by default
            results = self.queue.get_batch_results(batch_id, unified=unified)
            
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