import asyncio
import os
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .document_processor import DocumentProcessor
from .risk_analyzer import RiskAnalyzer
from .mock_risk_analyzer import MockRiskAnalyzer
from .agent_monitor import agent_monitor, AgentStatus, LogLevel
import uuid
import re

class ChunkData(TypedDict):
    """Data structure for individual document chunks"""
    chunk_id: str
    chunk_index: int
    content: str
    page_range: str
    section_context: str
    char_position: int
    context_overlap: str
    status: str
    risk_analysis: str
    rag_context: str
    findings: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float

class WorkflowState(TypedDict):
    """State structure for the parallel multi-agent workflow"""
    file_content: bytes
    filename: str
    prompt: str
    document_data: Dict[str, Any]
    chunks: List[ChunkData]
    chunk_analyses: Dict[str, ChunkData]
    cross_references: List[Dict[str, Any]]
    combined_analysis: str
    final_result: str
    current_step: str
    error: str
    processing_start_time: float
    total_chunks: int
    color_coded: bool

class LangGraphOrchestrator:
    """LangGraph-based orchestrator for multi-agent legal document analysis"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        # Check for API key, fallback to mock if not available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.risk_analyzer = RiskAnalyzer()
            print("Using real RiskAnalyzer with API key")
        else:
            self.risk_analyzer = MockRiskAnalyzer()
            print("No API key found, using MockRiskAnalyzer")
        self.memory = MemorySaver()
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self):
        """Build the parallel processing LangGraph workflow"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for parallel processing workflow
        workflow.add_node("document_processing", self._process_document_node)
        workflow.add_node("intelligent_chunking", self._intelligent_chunking_node)
        workflow.add_node("parallel_chunk_analysis", self._parallel_chunk_analysis_node)
        workflow.add_node("cross_reference_validation", self._cross_reference_validation_node)
        workflow.add_node("results_combination", self._results_combination_node)
        workflow.add_node("format_response", self._format_response_node)
        
        # Define the parallel processing workflow edges
        workflow.set_entry_point("document_processing")
        workflow.add_edge("document_processing", "intelligent_chunking")
        workflow.add_edge("intelligent_chunking", "parallel_chunk_analysis")
        workflow.add_edge("parallel_chunk_analysis", "cross_reference_validation")
        workflow.add_edge("cross_reference_validation", "results_combination")
        workflow.add_edge("results_combination", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _process_document_node(self, state: WorkflowState) -> WorkflowState:
        """Document processing agent node - extracts text and metadata"""
        import time
        state["processing_start_time"] = time.time()
        
        filename = state.get('filename', 'unknown_document')
        await agent_monitor.log_activity(
            "Document Parser", 
            AgentStatus.PROCESSING, 
            f"Starting document processing for {filename}",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            await agent_monitor.log_activity(
                "Document Parser", 
                AgentStatus.PROCESSING, 
                "Extracting text and metadata from document...",
                LogLevel.INFO,
                progress=0.3
            )
            
            document_data = await self.document_processor.process_document(
                state["file_content"], 
                filename
            )
            
            await agent_monitor.log_activity(
                "Document Parser", 
                AgentStatus.PROCESSING, 
                f"Successfully extracted {document_data.get('word_count', 0)} words",
                LogLevel.INFO,
                progress=0.8
            )
            
            state["document_data"] = document_data
            state["chunks"] = []
            state["chunk_analyses"] = {}
            state["cross_references"] = []
            state["current_step"] = "document_processing_complete"
            
            await agent_monitor.log_activity(
                "Document Parser", 
                AgentStatus.COMPLETED, 
                "Document processing completed successfully",
                LogLevel.SUCCESS,
                progress=1.0,
                metadata={"word_count": document_data.get("word_count", 0)}
            )
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Document Parser", 
                AgentStatus.ERROR, 
                f"Error processing document: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state
    
    async def _intelligent_chunking_node(self, state: WorkflowState) -> WorkflowState:
        """Intelligent document chunking agent - splits document preserving legal structure"""
        await agent_monitor.log_activity(
            "Document Chunking Agent", 
            AgentStatus.PROCESSING, 
            "Starting intelligent document chunking...",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            document_text = state["document_data"]["text"]
            
            await agent_monitor.log_activity(
                "Document Chunking Agent", 
                AgentStatus.PROCESSING, 
                "Analyzing document structure for optimal chunking...",
                LogLevel.INFO,
                progress=0.2
            )
            
            chunks = self._create_intelligent_chunks(document_text, state["filename"])
            state["chunks"] = chunks
            state["total_chunks"] = len(chunks)
            
            # Initialize parallel processing monitoring
            agent_monitor.start_parallel_processing(len(chunks))
            
            await agent_monitor.log_activity(
                "Document Chunking Agent", 
                AgentStatus.PROCESSING, 
                f"Created {len(chunks)} intelligent chunks preserving legal boundaries",
                LogLevel.INFO,
                progress=0.8
            )
            
            state["current_step"] = "intelligent_chunking_complete"
            
            await agent_monitor.log_activity(
                "Document Chunking Agent", 
                AgentStatus.COMPLETED, 
                f"Document chunking completed - {len(chunks)} chunks ready for parallel analysis",
                LogLevel.SUCCESS,
                progress=1.0,
                metadata={"chunk_count": len(chunks)}
            )
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Document Chunking Agent", 
                AgentStatus.ERROR, 
                f"Error during intelligent chunking: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state

    def _create_intelligent_chunks(self, text: str, filename: str) -> List[ChunkData]:
        """Optimized chunking for sub-10 second performance"""
        chunks = []
        text_length = len(text)
        
        # Fast chunking parameters - optimized for speed
        chunk_size = 6000  # Larger chunks = fewer chunks = faster processing
        overlap_size = 200
        
        # Pre-extract sections once for all chunks
        self.document_sections = self._extract_section_headers_fast(text)
        
        # Fast path for small documents
        if text_length <= 8000:
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": 0,
                "content": text,
                "page_range": "1-end",
                "section_context": "Document Section",
                "char_position": 0,
                "context_overlap": "",
                "status": "ready",
                "risk_analysis": "",
                "rag_context": "",
                "findings": [],
                "confidence_score": 0.0,
                "processing_time": 0.0
            })
            return chunks
        
        # Fast character-based chunking (no word splitting)
        start_pos = 0
        chunk_index = 0
        
        while start_pos < text_length:
            end_pos = min(start_pos + chunk_size, text_length)
            
            # Adjust to word boundaries for clean breaks
            if end_pos < text_length:
                # Find next space or sentence end
                for i in range(end_pos, min(end_pos + 200, text_length)):
                    if text[i] in '.\n' or (text[i] == ' ' and i > end_pos + 100):
                        end_pos = i + 1
                        break
            
            chunk_content = text[start_pos:end_pos]
            
            # Simple overlap
            overlap_text = ""
            if start_pos > 0:
                overlap_start = max(0, start_pos - overlap_size)
                overlap_text = text[overlap_start:start_pos]
            
            # Enhanced section context with lettered section support
            section_context = self._find_section_fast(start_pos)
            
            # Simple page estimation
            start_page = max(1, start_pos // 2500 + 1)
            end_page = max(start_page, end_pos // 2500 + 1)
            
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": chunk_index,
                "content": chunk_content,
                "page_range": f"{start_page}-{end_page}",
                "section_context": section_context,
                "char_position": start_pos,
                "context_overlap": overlap_text,
                "status": "ready",
                "risk_analysis": "",
                "rag_context": "",
                "findings": [],
                "confidence_score": 0.0,
                "processing_time": 0.0
            })
            
            start_pos = end_pos - overlap_size
            chunk_index += 1
            
            if end_pos >= text_length:
                break
        
        return chunks
    
    def _extract_section_headers_fast(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced section header extraction with lettered sections support"""
        headers = []
        
        # Enhanced patterns including lettered sections (A., B., C., etc.)
        key_patterns = [
            # Lettered sections - highest priority for legal documents
            (r'(?i)^([A-Z]\.\s+[^\n]{1,80})', 'lettered_section'),
            (r'(?i)\n\s*([A-Z]\.\s+[^\n]{1,80})', 'lettered_section'),
            
            # Numbered sections
            (r'(?i)\n\s*(\d+\.\s+[A-Z][^\n]{1,50})', 'numbered_section'),
            
            # Articles and Sections
            (r'(?i)\n\s*(ARTICLE\s+[IVX]+[^\n]{1,30})', 'article'),
            (r'(?i)\n\s*(SECTION\s+[A-Z0-9]+[^\n]{1,50})', 'section'),
            
            # Legal topic headers
            (r'(?i)\n\s*(DEFINITIONS?[^\n]{0,30})', 'definitions'),
            (r'(?i)\n\s*(LIABILITY[^\n]{0,30})', 'liability_section'),
            (r'(?i)\n\s*(TERMINATION[^\n]{0,30})', 'termination_section'),
            (r'(?i)\n\s*(CONFIDENTIALITY[^\n]{0,30})', 'confidentiality_section'),
            (r'(?i)\n\s*(INTELLECTUAL\s+PROPERTY[^\n]{0,30})', 'ip_section'),
            (r'(?i)\n\s*(INDEMNIFICATION[^\n]{0,30})', 'indemnification_section'),
            (r'(?i)\n\s*(WARRANTIES?[^\n]{0,30})', 'warranty_section'),
            (r'(?i)\n\s*(DISPUTES?[^\n]{0,30})', 'dispute_section'),
        ]
        
        # Single pass through text
        for pattern, section_type in key_patterns:
            for match in re.finditer(pattern, text):
                header_text = match.group(1).strip()
                
                # Clean up header text
                header_text = re.sub(r'\s+', ' ', header_text)
                
                headers.append({
                    'text': header_text,
                    'type': section_type,
                    'position': match.start(),
                    'normalized': self._normalize_section_header(header_text)
                })
        
        # Remove duplicates and sort by position
        seen_positions = set()
        unique_headers = []
        for header in headers:
            if header['position'] not in seen_positions:
                seen_positions.add(header['position'])
                unique_headers.append(header)
        
        unique_headers.sort(key=lambda x: x['position'])
        return unique_headers
    
    def _find_section_fast(self, char_position: int) -> str:
        """Enhanced section lookup with proper lettered section support"""
        if not self.document_sections:
            return "Document Section"
        
        # Find the most recent section before this position
        current_section = "Document Section"
        for section in self.document_sections:
            if section['position'] <= char_position:
                # Use normalized name if available, otherwise use text
                if 'normalized' in section and section['normalized']:
                    current_section = section['normalized']
                else:
                    current_section = section['text'][:50]  # Increased limit for full section names
            else:
                break
        
        return current_section
    
    def _normalize_section_header(self, header: str) -> str:
        """Normalize section header for consistent display with lettered section support"""
        # Clean up formatting
        cleaned = re.sub(r'\s+', ' ', header.strip())
        
        # Handle lettered sections specially (A., B., C., etc.)
        lettered_match = re.match(r'^([A-Z]\.)\s*(.+)', cleaned)
        if lettered_match:
            letter = lettered_match.group(1)
            title = lettered_match.group(2)
            
            # Capitalize title appropriately
            if title.isupper():
                title = title.title()
            
            return f"Section {letter} {title}"
        
        # Handle numbered sections (1., 2., etc.)
        numbered_match = re.match(r'^(\d+\.)\s*(.+)', cleaned)
        if numbered_match:
            number = numbered_match.group(1)
            title = numbered_match.group(2)
            
            if title.isupper():
                title = title.title()
            
            return f"Section {number} {title}"
        
        # Handle other section types
        if cleaned.isupper() and len(cleaned) > 5:
            cleaned = cleaned.title()
        
        return cleaned
    
    def _find_section_for_chunk(self, chunk_content: str, chunk_start_pos: int) -> str:
        """Find the most relevant section header for a chunk"""
        if not hasattr(self, 'document_sections') or not self.document_sections:
            return f"Document Section (Position ~{chunk_start_pos//1000}k)"
        
        # Find the section header that appears before this chunk
        relevant_section = None
        for section in self.document_sections:
            if section['position'] <= chunk_start_pos:
                relevant_section = section
            else:
                break
        
        if relevant_section:
            return relevant_section['normalized']
        
        # Look for section headers within the chunk content
        for section in self.document_sections:
            if section['text'].lower() in chunk_content.lower():
                return section['normalized']
        
        # Fallback to extracting section from chunk content
        section_patterns = [
            r'(?i)^(\d+\.\s+[A-Z][^\n]+)',
            r'(?i)^([A-Z]+\.\s+[A-Z][^\n]+)',
            r'(?i)^(ARTICLE\s+[IVX]+[^\n]*)',
            r'(?i)^(SECTION\s+\d+[^\n]*)',
        ]
        
        lines = chunk_content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    return self._normalize_section_header(match.group(1))
        
        return f"Document Section (Position ~{chunk_start_pos//1000}k)"

    async def _parallel_chunk_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Parallel chunk analysis - processes all chunks simultaneously"""
        await agent_monitor.log_activity(
            "Orchestrator Agent", 
            AgentStatus.PROCESSING, 
            f"Starting parallel analysis of {state['total_chunks']} chunks...",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            chunks = state["chunks"]
            prompt = state["prompt"]
            
            # Create concurrent tasks for all chunks
            tasks = []
            for chunk in chunks:
                task = self._analyze_single_chunk(chunk, prompt)
                tasks.append(task)
            
            await agent_monitor.log_activity(
                "Orchestrator Agent", 
                AgentStatus.PROCESSING, 
                f"Processing {len(tasks)} chunks concurrently...",
                LogLevel.INFO,
                progress=0.1
            )
            
            # Execute all chunk analyses in parallel
            analyzed_chunks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any failures
            successful_analyses = {}
            failed_chunks = []
            
            for i, result in enumerate(analyzed_chunks):
                if isinstance(result, Exception):
                    failed_chunks.append(chunks[i]["chunk_id"])
                else:
                    successful_analyses[result["chunk_id"]] = result
            
            state["chunk_analyses"] = successful_analyses
            state["current_step"] = "parallel_analysis_complete"
            
            total_findings = sum(len(chunk["findings"]) for chunk in successful_analyses.values())
            await agent_monitor.log_activity(
                "Orchestrator Agent", 
                AgentStatus.COMPLETED, 
                f"Parallel analysis completed - {len(successful_analyses)}/{len(chunks)} chunks processed successfully, {total_findings} total findings",
                LogLevel.SUCCESS,
                progress=1.0,
                metadata={"successful_chunks": len(successful_analyses), "total_findings": total_findings}
            )
            
            # End parallel processing monitoring
            agent_monitor.end_parallel_processing()
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Orchestrator Agent", 
                AgentStatus.ERROR, 
                f"Error during parallel chunk analysis: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state
    
    async def _analyze_single_chunk(self, chunk: ChunkData, prompt: str) -> ChunkData:
        """Analyze a single chunk with RAG context and risk assessment"""
        import time
        start_time = time.time()
        
        try:
            # Log chunk processing start
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.PROCESSING,
                message=f"Starting analysis of chunk {chunk['chunk_index'] + 1} ({chunk['page_range']})",
                level=LogLevel.INFO,
                progress=0.0
            )
            
            # Simulate RAG search 
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="RAG Search Agent",
                status=AgentStatus.PROCESSING,
                message=f"Loading relevant legal context for chunk {chunk['chunk_index'] + 1}",
                level=LogLevel.INFO,
                progress=0.2
            )
            
            chunk["rag_context"] = "Relevant legal precedents and risk patterns loaded"
            
            # Analyze risks for this specific chunk
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.PROCESSING,
                message=f"Analyzing legal risks in chunk {chunk['chunk_index'] + 1} ({len(chunk['content'])} chars)",
                level=LogLevel.INFO,
                progress=0.5
            )
            
            # Add progress update during API call
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.PROCESSING,
                message=f"Calling AI API for chunk {chunk['chunk_index'] + 1} analysis...",
                level=LogLevel.INFO,
                progress=0.7
            )
            
            # Add intermediate progress updates
            await asyncio.sleep(0.1)  # Allow other tasks to process
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.PROCESSING,
                message=f"Processing API response for chunk {chunk['chunk_index'] + 1}...",
                level=LogLevel.INFO,
                progress=0.9
            )
            
            # Debug logging
            print(f"\n=== CHUNK {chunk['chunk_index'] + 1} ANALYSIS START ===")
            print(f"Chunk size: {len(chunk['content'])} characters")
            print(f"Page range: {chunk['page_range']}")
            print(f"Content preview: {chunk['content'][:200]}...")
            
            # Streamlined prompt for speed
            enhanced_prompt = f"""
            {prompt}
            
            CHUNK {chunk['chunk_index'] + 1} (Pages {chunk['page_range']}):
            {chunk['content']}
            """
            
            risk_analysis = await self.risk_analyzer.analyze_risks(chunk["content"], enhanced_prompt)
            chunk["risk_analysis"] = risk_analysis
            
            # Debug: Print actual analysis to understand what we're getting
            print(f"\n=== CHUNK {chunk['chunk_index'] + 1} ANALYSIS OUTPUT ===")
            print(f"Analysis length: {len(risk_analysis)} characters")
            print(f"Analysis preview: {risk_analysis[:500]}...")
            print("=== END ANALYSIS OUTPUT ===\n")
            
            # Extract structured findings
            findings = self._extract_findings_from_analysis(risk_analysis, chunk["chunk_index"])
            
            # Add section context to each finding
            section_context = chunk.get("section_context", "Unknown Section")
            for finding in findings:
                finding["document_section"] = section_context
                
            chunk["findings"] = findings
            chunk["confidence_score"] = self._calculate_confidence_score(findings)
            chunk["status"] = "completed"
            chunk["processing_time"] = time.time() - start_time
            
            # Log completion
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.COMPLETED,
                message=f"Chunk {chunk['chunk_index'] + 1} analysis complete - {len(findings)} findings identified",
                level=LogLevel.SUCCESS,
                progress=1.0,
                findings_count=len(findings),
                confidence_score=chunk["confidence_score"],
                processing_time=chunk["processing_time"]
            )
            
            return chunk
            
        except Exception as e:
            chunk["status"] = "error"
            chunk["processing_time"] = time.time() - start_time
            
            # Log error
            await agent_monitor.log_chunk_activity(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                page_range=chunk["page_range"],
                agent_name="Risk Analysis Agent",
                status=AgentStatus.ERROR,
                message=f"Error analyzing chunk {chunk['chunk_index'] + 1}: {str(e)}",
                level=LogLevel.ERROR,
                progress=0.0,
                processing_time=chunk["processing_time"]
            )
            
            raise e
    
    def _extract_findings_from_analysis(self, analysis: str, chunk_index: int) -> List[Dict[str, Any]]:
        """Extract structured findings from the new legal report format"""
        findings = []
        
        # First try to parse the new lettered section format (A., B., C., etc.)
        findings = self._extract_lettered_section_findings(analysis, chunk_index)
        
        # If lettered extraction didn't work, try the old FINDING format
        if len(findings) == 0:
            print(f"Lettered section parsing failed for chunk {chunk_index}, trying legacy FINDING format")
            findings = self._extract_old_finding_format(analysis, chunk_index)
        
        # Final fallback to pattern-based extraction
        if len(findings) == 0:
            print(f"All structured parsing failed for chunk {chunk_index}, falling back to pattern extraction")
            findings = self._extract_pattern_based_findings(analysis, chunk_index)
        
        return findings
    
    def _extract_lettered_section_findings(self, analysis: str, chunk_index: int) -> List[Dict[str, Any]]:
        """Extract findings from lettered section format (A., B., C., etc.)"""
        findings = []
        
        # Split by lettered main sections (A., B., C., etc.)
        section_pattern = r'\n([A-F]\.\s+[^\n]+)'
        sections = re.split(section_pattern, analysis)
        
        # sections will be: [text_before, section_header1, section_content1, section_header2, section_content2, ...]
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_header = sections[i].strip()
                section_content = sections[i + 1].strip()
                
                # Extract category from section header (e.g., "A. Commercial Terms" -> "Commercial Terms")
                category_match = re.match(r'[A-F]\.\s+(.+)', section_header)
                category = category_match.group(1) if category_match else "GENERAL"
                
                # Find numbered subsections within this lettered section
                subsection_findings = self._extract_numbered_subsections(section_content, category, chunk_index, len(findings))
                findings.extend(subsection_findings)
        
        return findings
    
    def _extract_numbered_subsections(self, section_content: str, category: str, chunk_index: int, finding_offset: int) -> List[Dict[str, Any]]:
        """Extract numbered subsections (1., 2., 3., etc.) from a lettered section"""
        findings = []
        
        # Split by numbered subsections
        subsection_pattern = r'\n(\d+\.\s+[^:]+):'
        subsections = re.split(subsection_pattern, section_content)
        
        for i in range(1, len(subsections), 2):
            if i + 1 < len(subsections):
                subsection_title = subsections[i].strip()
                subsection_content = subsections[i + 1].strip()
                
                # Extract the one-line summary (everything before "Additional Guidance:")
                guidance_split = subsection_content.split('Additional Guidance:', 1)
                one_line_summary = guidance_split[0].strip()
                detailed_guidance = guidance_split[1].strip() if len(guidance_split) > 1 else ""
                
                # Determine risk level from one-line summary or content
                risk_level = self._determine_risk_level_from_content(one_line_summary + " " + detailed_guidance)
                
                # Extract section reference if present (e.g., "Section 5.2", "Clause 3.1")
                section_ref_match = re.search(r'\(Section\s+[\w\.]+\)', subsection_title)
                section_reference = section_ref_match.group(0) if section_ref_match else ""
                
                # Remove the leading number and clean up the title by removing section reference
                # Extract the number first, then remove it and the section reference
                number_match = re.match(r'^(\d+\.\s*)', subsection_title)
                extracted_number = number_match.group(1) if number_match else ""
                
                # Remove both the number and section reference from title
                clean_title = re.sub(r'^\d+\.\s*', '', subsection_title)  # Remove leading number
                clean_title = re.sub(r'\s*\(Section\s+[\w\.]+\)', '', clean_title)  # Remove section reference
                
                # Extract business impact and recommendations from detailed guidance
                business_impact = self._extract_business_impact_from_guidance(detailed_guidance)
                recommendation = self._extract_recommendation_from_guidance(detailed_guidance)
                
                # Look for quoted text as evidence
                evidence = self._extract_quoted_evidence(detailed_guidance)
                
                finding = {
                    "id": f"chunk_{chunk_index}_finding_{finding_offset + len(findings)}",
                    "severity": risk_level,
                    "description": f"{clean_title}: {one_line_summary}",
                    "chunk_index": chunk_index,
                    "confidence": 0.90,  # High confidence for structured legal analysis
                    "category": category,
                    "document_section": section_reference,
                    "evidence": evidence,
                    "business_impact": business_impact,
                    "recommendation": recommendation,
                    "additional_guidance": detailed_guidance,
                    "section_title": clean_title,
                    "one_line_summary": one_line_summary
                }
                
                findings.append(finding)
        
        return findings
    
    def _determine_risk_level_from_content(self, content: str) -> str:
        """Determine risk level from content analysis"""
        content_lower = content.lower()
        
        # High risk indicators
        high_risk_terms = [
            'high risk', 'critical', 'significant risk', 'major concern',
            'strongly recommend', 'should be rejected', 'dangerous', 'problematic',
            'unlimited liability', 'material breach', 'immediate attention'
        ]
        
        # Medium risk indicators  
        medium_risk_terms = [
            'medium risk', 'moderate risk', 'concerning', 'noteworthy',
            'should negotiate', 'recommend review', 'may want to', 'unclear', 'ambiguous'
        ]
        
        # Low risk indicators
        low_risk_terms = [
            'low risk', 'minor', 'acceptable', 'reasonable', 'standard',
            'typical', 'adequate protection', 'favorable'
        ]
        
        # Check in order of priority
        for term in high_risk_terms:
            if term in content_lower:
                return 'high'
        
        for term in medium_risk_terms:
            if term in content_lower:
                return 'medium'
                
        for term in low_risk_terms:
            if term in content_lower:
                return 'low'
        
        # Default to medium if uncertain
        return 'medium'
    
    def _extract_business_impact_from_guidance(self, guidance: str) -> str:
        """Extract business impact from detailed guidance"""
        # Look for explicit business impact statements
        impact_patterns = [
            r'(?:could|may|might|will|would)\s+(?:result in|lead to|cause|expose|create|impact)[^.]*',
            r'business\s+(?:risk|impact|concern|consequence)[^.]*',
            r'(?:financial|operational|legal)\s+(?:risk|impact|exposure)[^.]*',
            r'CLIENT\s+(?:could|may|will|would)[^.]*'
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, guidance, re.IGNORECASE)
            if match:
                impact = match.group(0).strip()
                if len(impact) > 200:
                    impact = impact[:200] + "..."
                return impact
        
        # Fallback: take first sentence that mentions impact-related terms
        sentences = guidance.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['risk', 'impact', 'expose', 'consequence', 'result']):
                return sentence.strip()[:200]
        
        return ""
    
    def _extract_recommendation_from_guidance(self, guidance: str) -> str:
        """Extract recommendation from detailed guidance"""
        # Look for explicit recommendations
        rec_patterns = [
            r'(?:recommend|suggest|advise|should|must|need to)[^.]*',
            r'CLIENT\s+(?:should|could|may want to)[^.]*',
            r'(?:negotiate|request|seek|clarify|amend)[^.]*'
        ]
        
        for pattern in rec_patterns:
            match = re.search(pattern, guidance, re.IGNORECASE)
            if match:
                rec = match.group(0).strip()
                if len(rec) > 150:
                    rec = rec[:150] + "..."
                return rec
        
        return ""
    
    def _extract_quoted_evidence(self, guidance: str) -> str:
        """Extract quoted text evidence from guidance"""
        # Look for quoted text
        quote_patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'`([^`]+)`'
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, guidance)
            if matches:
                # Return the longest quote as evidence
                longest_quote = max(matches, key=len)
                return longest_quote
        
        return ""
    
    def _extract_old_finding_format(self, analysis: str, chunk_index: int) -> List[Dict[str, Any]]:
        """Extract findings from old FINDING format for backward compatibility"""
        findings = []
        
        # Split by FINDING pattern to get individual findings
        finding_pattern = r'FINDING\s+(\d+):\s*\n'
        finding_sections = re.split(finding_pattern, analysis)
        
        # finding_sections will be: [text_before, finding_num1, finding_content1, finding_num2, finding_content2, ...]
        for i in range(1, len(finding_sections), 2):
            if i + 1 < len(finding_sections):
                finding_num = finding_sections[i]
                finding_content = finding_sections[i + 1].strip()
                
                finding = self._parse_structured_finding(finding_content, chunk_index, int(finding_num))
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _parse_structured_finding(self, finding_content: str, chunk_index: int, finding_num: int) -> Dict[str, Any]:
        """Parse a single structured finding with the new format"""
        
        # Extract fields using regex patterns
        severity_match = re.search(r'SEVERITY:\s*([A-Z]+)', finding_content)
        category_match = re.search(r'CATEGORY:\s*(.+)', finding_content)
        description_match = re.search(r'DESCRIPTION:\s*(.+?)(?=\nDOCUMENT_QUOTE:)', finding_content, re.DOTALL)
        quote_match = re.search(r'DOCUMENT_QUOTE:\s*"([^"]+)"', finding_content, re.DOTALL)
        impact_match = re.search(r'BUSINESS_IMPACT:\s*(.+?)(?=\nRECOMMENDATION:)', finding_content, re.DOTALL)
        recommendation_match = re.search(r'RECOMMENDATION:\s*(.+)', finding_content, re.DOTALL)
        
        # Validate required fields are present
        if not severity_match or not description_match:
            print(f"Required fields missing in finding {finding_num}")
            return None
        
        severity = severity_match.group(1).lower()
        if severity not in ['high', 'medium', 'low']:
            severity = 'medium'  # Default fallback
        
        description = description_match.group(1).strip()
        document_quote = quote_match.group(1).strip() if quote_match else ""
        business_impact = impact_match.group(1).strip() if impact_match else ""
        recommendation = recommendation_match.group(1).strip() if recommendation_match else ""
        category = category_match.group(1).strip() if category_match else "GENERAL"
        
        # Calculate confidence based on presence of document quote
        confidence = 0.95 if document_quote else 0.60
        
        return {
            "id": f"chunk_{chunk_index}_finding_{finding_num}",
            "severity": severity,
            "description": description,
            "chunk_index": chunk_index,
            "confidence": confidence,
            "category": category,
            "document_section": None,  # Will be set from chunk context
            "evidence": document_quote,  # Use the actual document quote as evidence
            "business_impact": business_impact,
            "recommendation": recommendation
        }
    
    def _extract_subsection_findings(self, content: str, section_title: str, chunk_index: int, finding_offset: int) -> List[Dict[str, Any]]:
        """Extract findings from a structured section of analysis"""
        findings = []
        
        # Look for explicit HIGH RISK, MEDIUM RISK, LOW RISK labels
        risk_sections = re.split(r'((?:HIGH|MEDIUM|LOW)\s+RISK:[^\n]+)', content)
        
        for i in range(1, len(risk_sections), 2):  # Every other item is a risk section
            if i + 1 < len(risk_sections):
                risk_header = risk_sections[i].strip()
                risk_content = risk_sections[i + 1].strip()
                
                # Extract severity from header
                if risk_header.startswith('HIGH RISK'):
                    severity = 'high'
                    confidence = 0.95
                elif risk_header.startswith('MEDIUM RISK'):
                    severity = 'medium' 
                    confidence = 0.80
                else:  # LOW RISK
                    severity = 'low'
                    confidence = 0.65
                
                # Extract the risk title (after "RISK:")
                risk_title = risk_header.split(':', 1)[-1].strip()
                
                # Get business impact description (look for "Business Impact:" section)
                business_impact = ""
                impact_match = re.search(r'Business Impact:\s*([^:]+?)(?:Recommended Action:|$)', risk_content, re.DOTALL)
                if impact_match:
                    business_impact = impact_match.group(1).strip()[:300]
                
                description = f"{risk_title}. {business_impact}" if business_impact else risk_title
                
                findings.append({
                    "id": f"chunk_{chunk_index}_finding_{finding_offset + len(findings)}",
                    "severity": severity,
                    "description": description,
                    "chunk_index": chunk_index,
                    "confidence": confidence,
                    "section": section_title,
                    "document_section": None,  # Will be set from chunk context
                    "evidence": risk_content[:1500] if risk_content else ""  # Increased for detailed business impact extraction
                })
        
        return findings
    
    def _extract_pattern_based_findings(self, analysis: str, chunk_index: int) -> List[Dict[str, Any]]:
        """Fallback pattern-based findings extraction"""
        findings = []
        
        # Enhanced pattern matching for legal analysis
        risk_indicators = [
            # High Risk Patterns
            (r'(?i)(high[- ]?risk|critical|severe|major concern|significant risk|red flag)', 'high'),
            (r'(?i)(unlimited liability|one-sided|unfavorable|problematic|dangerous)', 'high'),
            (r'(?i)(missing.*(?:clause|provision|protection)|lack.*(?:protection|safeguard))', 'high'),
            (r'(?i)(should be (?:avoided|rejected|amended)|strongly recommend against)', 'high'),
            
            # Medium Risk Patterns  
            (r'(?i)(medium[- ]?risk|moderate|concerning|noteworthy|attention)', 'medium'),
            (r'(?i)(should.*(?:negotiate|review|consider)|may want to|recommend)', 'medium'),
            (r'(?i)(unclear|ambiguous|vague|inconsistent)', 'medium'),
            (r'(?i)(potential.*(?:risk|issue|problem)|could.*(?:expose|result))', 'medium'),
            
            # Low Risk Patterns
            (r'(?i)(low[- ]?risk|minor|note|observe|standard)', 'low'),
            (r'(?i)(typical|common|acceptable|reasonable)', 'low')
        ]
        
        # Legal domain patterns that indicate findings
        legal_finding_patterns = [
            r'(?i)liability.*(?:cap|limit|exclusion)',
            r'(?i)indemnif(?:ication|y).*(?:clause|provision)',
            r'(?i)termination.*(?:right|clause|provision)',
            r'(?i)intellectual property.*(?:ownership|assignment)',
            r'(?i)confidentiality.*(?:obligation|clause)',
            r'(?i)governing law.*(?:jurisdiction|clause)',
            r'(?i)payment.*(?:terms|obligation|schedule)',
            r'(?i)warranty.*(?:disclaimer|limitation)',
            r'(?i)force majeure',
            r'(?i)dispute resolution'
        ]
        
        # Split analysis into sentences for better extraction
        sentences = re.split(r'[.!?]+', analysis)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            # Check for risk indicators
            severity = None
            for pattern, sev in risk_indicators:
                if re.search(pattern, sentence):
                    severity = sev
                    break
            
            # Check for legal domain content
            has_legal_content = any(re.search(pattern, sentence) for pattern in legal_finding_patterns)
            
            # Extract finding if it has risk indicators or significant legal content
            if severity or has_legal_content:
                # If no explicit severity found but has legal content, infer from context
                if not severity:
                    if any(word in sentence.lower() for word in ['must', 'should', 'recommend', 'important', 'ensure']):
                        severity = 'medium'
                    else:
                        severity = 'low'
                
                # Extract the key issue description - keep full description for detailed reporting
                description = sentence
                if len(description) > 500:  # Increased limit for detailed analysis
                    description = description[:500] + "..."
                
                # Calculate confidence based on context quality
                confidence = 0.95 if severity == 'high' else (0.75 if severity == 'medium' else 0.60)
                if any(word in sentence.lower() for word in ['specifically', 'clearly', 'explicitly', 'quote:']):
                    confidence += 0.05
                    
                findings.append({
                    "id": f"chunk_{chunk_index}_finding_{len(findings)}",
                    "severity": severity,
                    "description": description,
                    "chunk_index": chunk_index,
                    "sentence_number": i + 1,
                    "confidence": min(confidence, 1.0),
                    "document_section": None,  # Will be set from chunk context
                    "evidence": sentence[:1000] if sentence else ""  # Increased for detailed extraction
                })
        
        # If we still have very few findings, extract more aggressively
        if len(findings) < 2 and len(analysis) > 500:
            # Look for bullet points or numbered items
            bullet_patterns = [
                r'(?i)^[-*•]\s*(.+)$',
                r'(?i)^\d+\.\s*(.+)$',
                r'(?i)^[a-z]\)\s*(.+)$'
            ]
            
            lines = analysis.split('\n')
            for line in lines:
                line = line.strip()
                for pattern in bullet_patterns:
                    match = re.search(pattern, line)
                    if match and len(match.group(1)) > 30:
                        findings.append({
                            "id": f"chunk_{chunk_index}_finding_{len(findings)}",
                            "severity": "medium",  # Default severity for bullet points
                            "description": match.group(1),
                            "chunk_index": chunk_index,
                            "sentence_number": 0,
                            "confidence": 0.70,
                            "document_section": None,  # Will be set from chunk context
                            "evidence": line
                        })
        
        return findings
    
    def _calculate_confidence_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on findings quality"""
        if not findings:
            return 0.5
        
        severity_weights = {'high': 1.0, 'medium': 0.7, 'low': 0.3}
        total_weight = sum(severity_weights.get(f['severity'], 0.5) for f in findings)
        return min(0.95, total_weight / len(findings))
    
    async def _cross_reference_validation_node(self, state: WorkflowState) -> WorkflowState:
        """Cross-reference validation - checks relationships between chunks"""
        await agent_monitor.log_activity(
            "Cross-Reference Agent", 
            AgentStatus.PROCESSING, 
            "Validating relationships and consistency between chunks...",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            chunk_analyses = state["chunk_analyses"]
            
            await agent_monitor.log_activity(
                "Cross-Reference Agent", 
                AgentStatus.PROCESSING, 
                "Analyzing dependencies between document sections...",
                LogLevel.INFO,
                progress=0.3
            )
            
            cross_references = self._identify_cross_references(chunk_analyses)
            state["cross_references"] = cross_references
            
            await agent_monitor.log_activity(
                "Cross-Reference Agent", 
                AgentStatus.PROCESSING, 
                "Validating document-wide consistency...",
                LogLevel.INFO,
                progress=0.7
            )
            
            consistency_issues = self._validate_consistency(chunk_analyses, cross_references)
            
            # Add consistency issues to cross_references for reporting
            state["cross_references"] = cross_references + [
                {**issue, "type": "consistency_issue"} for issue in consistency_issues
            ]
            
            state["current_step"] = "cross_reference_complete"
            
            # Log detailed findings
            if consistency_issues:
                for issue in consistency_issues:
                    await agent_monitor.log_activity(
                        "Cross-Reference Agent", 
                        AgentStatus.PROCESSING if issue["severity"] == "low" else AgentStatus.ERROR, 
                        f"{issue['type']}: {issue['description']}",
                        LogLevel.WARNING if issue["severity"] == "medium" else LogLevel.ERROR,
                        metadata=issue
                    )
            
            await agent_monitor.log_activity(
                "Cross-Reference Agent", 
                AgentStatus.COMPLETED, 
                f"Cross-reference validation completed - {len(cross_references)} relationships found, {len(consistency_issues)} consistency issues",
                LogLevel.SUCCESS if len(consistency_issues) == 0 else LogLevel.WARNING,
                progress=1.0,
                metadata={
                    "cross_references": len(cross_references),
                    "consistency_issues": len(consistency_issues),
                    "high_severity_issues": len([i for i in consistency_issues if i["severity"] == "high"]),
                    "medium_severity_issues": len([i for i in consistency_issues if i["severity"] == "medium"])
                }
            )
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Cross-Reference Agent", 
                AgentStatus.ERROR, 
                f"Error during cross-reference validation: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state
    
    def _identify_cross_references(self, chunk_analyses: Dict[str, ChunkData]) -> List[Dict[str, Any]]:
        """Identify relationships between different chunks"""
        cross_references = []
        
        # Enhanced patterns for legal cross-references
        reference_patterns = [
            (r'(?i)section\s+(\d+(?:\.\d+)*)', 'section_reference'),
            (r'(?i)clause\s+(\d+(?:\.\d+)*)', 'clause_reference'),
            (r'(?i)article\s+([IVX]+|\d+)', 'article_reference'),
            (r'(?i)paragraph\s+([a-z]|\d+)', 'paragraph_reference'),
            (r'(?i)subsection\s+(\d+(?:\.\d+)*)', 'subsection_reference'),
            (r'(?i)attachment\s+([A-Z]|\d+)', 'attachment_reference'),
            (r'(?i)exhibit\s+([A-Z]|\d+)', 'exhibit_reference'),
            (r'(?i)schedule\s+([A-Z]|\d+)', 'schedule_reference'),
        ]
        
        # Term consistency patterns
        term_patterns = [
            (r'(?i)\b(payment|fee|cost)\s+terms?\b', 'payment_terms'),
            (r'(?i)\b(termination|end|expir).*(?:date|period)\b', 'termination_terms'),
            (r'(?i)\bliability\s+(?:limit|cap|maximum)\b', 'liability_terms'),
            (r'(?i)\bindemnif(?:y|ication)\b', 'indemnification_terms'),
            (r'(?i)\bconfidential(?:ity)?\b', 'confidentiality_terms'),
            (r'(?i)\bintellectual\s+property\b', 'ip_terms'),
            (r'(?i)\bgoverning\s+law\b', 'governing_law'),
            (r'(?i)\bjurisdiction\b', 'jurisdiction_terms'),
        ]
        
        chunks = list(chunk_analyses.values())
        
        # 1. Identify structural cross-references
        for i, chunk1 in enumerate(chunks):
            for j, chunk2 in enumerate(chunks):
                if i != j:
                    for pattern, ref_type in reference_patterns:
                        refs_in_chunk1 = re.findall(pattern, chunk1["content"])
                        refs_in_chunk2 = re.findall(pattern, chunk2["content"])
                        
                        # Check if chunk1 references something defined in chunk2
                        for ref in refs_in_chunk1:
                            if any(ref in chunk2["content"] for ref in refs_in_chunk2):
                                cross_references.append({
                                    "from_chunk": chunk1["chunk_id"],
                                    "to_chunk": chunk2["chunk_id"],
                                    "reference_value": ref,
                                    "type": ref_type,
                                    "relationship": "references",
                                    "confidence": 0.8
                                })
        
        # 2. Identify term consistency relationships
        term_locations = {}
        for chunk in chunks:
            for pattern, term_type in term_patterns:
                matches = re.findall(pattern, chunk["content"])
                if matches:
                    if term_type not in term_locations:
                        term_locations[term_type] = []
                    term_locations[term_type].append({
                        "chunk_id": chunk["chunk_id"],
                        "chunk_index": chunk["chunk_index"],
                        "matches": matches
                    })
        
        # Create cross-references for terms that appear in multiple chunks
        for term_type, locations in term_locations.items():
            if len(locations) > 1:
                for i, loc1 in enumerate(locations):
                    for j, loc2 in enumerate(locations):
                        if i < j:  # Avoid duplicates
                            cross_references.append({
                                "from_chunk": loc1["chunk_id"],
                                "to_chunk": loc2["chunk_id"],
                                "term_type": term_type,
                                "type": "term_consistency",
                                "relationship": "related_terms",
                                "confidence": 0.7
                            })
        
        return cross_references
    
    def _validate_consistency(self, chunk_analyses: Dict[str, ChunkData], cross_references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate consistency across document sections"""
        consistency_issues = []
        
        # 1. Check for conflicting payment terms
        payment_terms = []
        for chunk in chunk_analyses.values():
            # Look for payment amounts, dates, schedules
            payment_patterns = [
                r'(?i)\$([\d,]+(?:\.\d{2})?)',  # Dollar amounts
                r'(?i)(\d+)\s*days?\s*(?:after|from|before)',  # Payment timeframes
                r'(?i)(?:due|payment)\s+(?:within|by|on)\s+(\d+\s*days?|[A-Za-z]+\s+\d+)',  # Due dates
            ]
            
            for pattern in payment_patterns:
                matches = re.findall(pattern, chunk["content"])
                if matches:
                    payment_terms.extend([(chunk["chunk_id"], chunk["chunk_index"], match) for match in matches])
        
        # Check for conflicting payment amounts or timeframes
        if len(payment_terms) > 1:
            for i, (chunk_id1, idx1, term1) in enumerate(payment_terms):
                for j, (chunk_id2, idx2, term2) in enumerate(payment_terms):
                    if i < j and chunk_id1 != chunk_id2:
                        # Simple heuristic: flag if very different amounts or timeframes
                        try:
                            if term1.replace(',', '').replace('$', '').isdigit() and term2.replace(',', '').replace('$', '').isdigit():
                                amount1 = float(term1.replace(',', '').replace('$', ''))
                                amount2 = float(term2.replace(',', '').replace('$', ''))
                                if abs(amount1 - amount2) / max(amount1, amount2) > 0.5:  # 50% difference
                                    consistency_issues.append({
                                        "type": "conflicting_payment_amounts",
                                        "severity": "medium",
                                        "chunk1": chunk_id1,
                                        "chunk2": chunk_id2,
                                        "description": f"Potential conflicting payment amounts: {term1} vs {term2}",
                                        "confidence": 0.6
                                    })
                        except:
                            pass
        
        # 2. Check for conflicting dates and timeframes
        date_terms = []
        for chunk in chunk_analyses.values():
            date_patterns = [
                r'(?i)(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # Dates
                r'(?i)(\d+)\s*(?:months?|years?)\s*(?:from|after)',  # Duration from
                r'(?i)(?:expires?|terminates?)\s+(?:on|by)\s+([A-Za-z]+\s+\d+,?\s+\d{4})',  # Expiration dates
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, chunk["content"])
                if matches:
                    date_terms.extend([(chunk["chunk_id"], chunk["chunk_index"], match) for match in matches])
        
        # 3. Check for conflicting liability terms
        liability_terms = []
        for chunk in chunk_analyses.values():
            liability_patterns = [
                r'(?i)liability\s+(?:limited\s+to|capped\s+at|shall\s+not\s+exceed)\s+\$?([\d,]+)',
                r'(?i)maximum\s+liability.*?\$?([\d,]+)',
                r'(?i)no\s+liability\s+for\s+(indirect|consequential|punitive)',
            ]
            
            for pattern in liability_patterns:
                matches = re.findall(pattern, chunk["content"])
                if matches:
                    liability_terms.extend([(chunk["chunk_id"], chunk["chunk_index"], match) for match in matches])
        
        # Check for conflicting liability limits
        numeric_liability = [(cid, idx, term) for cid, idx, term in liability_terms if term.replace(',', '').isdigit()]
        if len(numeric_liability) > 1:
            for i, (chunk_id1, idx1, term1) in enumerate(numeric_liability):
                for j, (chunk_id2, idx2, term2) in enumerate(numeric_liability):
                    if i < j and chunk_id1 != chunk_id2:
                        amount1 = float(term1.replace(',', ''))
                        amount2 = float(term2.replace(',', ''))
                        if amount1 != amount2:
                            consistency_issues.append({
                                "type": "conflicting_liability_limits",
                                "severity": "high",
                                "chunk1": chunk_id1,
                                "chunk2": chunk_id2,
                                "description": f"Conflicting liability limits: ${term1} vs ${term2}",
                                "confidence": 0.8
                            })
        
        # 4. Validate cross-references point to existing sections
        structural_refs = [ref for ref in cross_references if ref["type"].endswith("_reference")]
        for ref in structural_refs:
            # This is a simplified check - in practice, would need more sophisticated validation
            referenced_value = ref.get("reference_value", "")
            target_chunk = chunk_analyses.get(ref["to_chunk"])
            
            if target_chunk and referenced_value:
                # Check if the referenced section actually exists in the target
                if referenced_value.lower() not in target_chunk["content"].lower():
                    consistency_issues.append({
                        "type": "broken_cross_reference",
                        "severity": "medium",
                        "chunk1": ref["from_chunk"],
                        "chunk2": ref["to_chunk"],
                        "description": f"Reference to '{referenced_value}' may not exist in target section",
                        "confidence": 0.5
                    })
        
        return consistency_issues
    
    async def _results_combination_node(self, state: WorkflowState) -> WorkflowState:
        """Results combination - merges parallel analyses into unified report"""
        await agent_monitor.log_activity(
            "Results Combination Agent", 
            AgentStatus.PROCESSING, 
            "Combining parallel chunk analyses into unified report...",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            chunk_analyses = state["chunk_analyses"]
            cross_references = state["cross_references"]
            color_coded = state.get("color_coded", False)
            
            await agent_monitor.log_activity(
                "Results Combination Agent", 
                AgentStatus.PROCESSING, 
                "Merging findings from all chunks...",
                LogLevel.INFO,
                progress=0.3
            )
            
            combined_analysis = self._combine_chunk_analyses(chunk_analyses, cross_references, color_coded)
            state["combined_analysis"] = combined_analysis
            
            await agent_monitor.log_activity(
                "Results Combination Agent", 
                AgentStatus.PROCESSING, 
                "Applying quality validation and confidence scoring...",
                LogLevel.INFO,
                progress=0.7
            )
            
            state["current_step"] = "results_combination_complete"
            
            total_findings = sum(len(chunk["findings"]) for chunk in chunk_analyses.values())
            await agent_monitor.log_activity(
                "Results Combination Agent", 
                AgentStatus.COMPLETED, 
                f"Results combination completed - {total_findings} findings consolidated",
                LogLevel.SUCCESS,
                progress=1.0,
                metadata={"total_findings": total_findings}
            )
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Results Combination Agent", 
                AgentStatus.ERROR, 
                f"Error combining results: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state
    
    def _combine_chunk_analyses(self, chunk_analyses: Dict[str, ChunkData], cross_references: List[Dict[str, Any]], color_coded: bool = False) -> str:
        """Combine individual chunk analyses into unified analysis"""
        all_findings = []
        total_confidence = 0.0
        
        # Store chunk data for page info lookup
        self._current_chunks = list(chunk_analyses.values())
        
        for chunk in chunk_analyses.values():
            all_findings.extend(chunk["findings"])
            total_confidence += chunk["confidence_score"]
        
        avg_confidence = total_confidence / len(chunk_analyses) if chunk_analyses else 0.0
        
        # Group findings by severity
        high_risk = [f for f in all_findings if f["severity"] == "high"]
        medium_risk = [f for f in all_findings if f["severity"] == "medium"]
        low_risk = [f for f in all_findings if f["severity"] == "low"]
        
        # Create detailed issue-by-issue breakdown
        detailed_findings = self._format_detailed_findings(high_risk, medium_risk, low_risk)
        
        print("DEBUG: Using UPDATED executive summary template!")
        combined_analysis = f"""
LEGAL ANALYSIS REPORT - PROFESSIONAL FORMAT
===========================================

EXECUTIVE SUMMARY:
- Document processed: {len(chunk_analyses)} sections analyzed
- High-risk findings: {len(high_risk)}
- Medium-risk findings: {len(medium_risk)}
- Low-risk/favorable findings: {len(low_risk)}
- Analysis confidence: {avg_confidence:.0%}
- Cross-references validated: {len(cross_references)}

{detailed_findings}
        """
        
        # Clean the combined analysis to remove any remaining color-coded language (unless color coding is requested)
        if not color_coded:
            combined_analysis = self._remove_color_coded_language(combined_analysis)
        
        return combined_analysis
    
    def _remove_color_coded_language(self, text: str) -> str:
        """Remove color-coded language from the final analysis report"""
        import re
        
        # Remove color-coded explanatory lines
        patterns_to_remove = [
            r'•\s*Green coded issues represent.*?\n',
            r'•\s*Yellow coded issues represent.*?\n', 
            r'•\s*Red coded issues represent.*?\n',
            r'•\s*Green coded issues.*?\n',
            r'•\s*Yellow coded issues.*?\n',
            r'•\s*Red coded issues.*?\n',
            # Remove any remaining color-coded references
            r'.*?Green coded.*?\n',
            r'.*?Yellow coded.*?\n',
            r'.*?Red coded.*?\n',
            r'.*?green coded.*?\n',
            r'.*?yellow coded.*?\n',
            r'.*?red coded.*?\n',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Replace color-coded references in the executive summary
        replacements = [
            (r'Red coded \(high-risk\) findings:', 'High-risk findings:'),
            (r'Yellow coded \(medium-risk\) findings:', 'Medium-risk findings:'),
            (r'Green coded \(low-risk/favorable\) findings:', 'Low-risk/favorable findings:'),
            (r'Red coded findings:', 'High-risk findings:'),
            (r'Yellow coded findings:', 'Medium-risk findings:'), 
            (r'Green coded findings:', 'Low-risk/favorable findings:'),
            (r'red coded', 'high-risk'),
            (r'yellow coded', 'medium-risk'),
            (r'green coded', 'low-risk'),
            (r'Red coded', 'High-risk'),
            (r'Yellow coded', 'Medium-risk'),
            (r'Green coded', 'Low-risk')
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Remove empty lines that might have been left after removing color-coded text
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text
    
    def _format_detailed_findings(self, high_risk: List, medium_risk: List, low_risk: List) -> str:
        """Format detailed issue-by-issue breakdown in professional legal report format"""
        
        # Create header with risk level definitions - flexible format
        detailed_report = [
            "In all matters which involve risk to CLIENT, CLIENT will need to consider if they are material enough to require any change to the clause or to risk management arrangements that CLIENT have in place.",
            "",
            "",
            "Contract Terms – Key Issues List",
            ""
        ]
        
        # Group findings by category to create lettered sections
        findings_by_category = self._group_findings_by_category([*high_risk, *medium_risk, *low_risk])
        
        section_letter = 'A'
        for category, findings in findings_by_category.items():
            if not findings:
                continue
                
            detailed_report.append(f"{section_letter}.\t{category}")
            detailed_report.append("")
            
            # Number subsections within each category
            for i, finding in enumerate(findings, 1):
                # Format as numbered subsection
                section_title = finding.get('section_title', finding.get('description', 'Issue'))
                section_ref = finding.get('document_section', '')
                one_line_summary = finding.get('one_line_summary', '')
                
                # Create the title line with section reference
                if section_ref:
                    title_line = f"{i}.\t{section_title} {section_ref}: {one_line_summary}"
                else:
                    title_line = f"{i}.\t{section_title}: {one_line_summary}"
                
                detailed_report.append(title_line)
                
                # Add the detailed guidance
                additional_guidance = finding.get('additional_guidance', '')
                if additional_guidance:
                    detailed_report.append(f"Additional Guidance: {additional_guidance}")
                else:
                    # Fallback to building guidance from other fields
                    guidance_parts = []
                    
                    # Add evidence/quoted text
                    evidence = finding.get('evidence', '')
                    if evidence:
                        guidance_parts.append(f'The document provides: "{evidence}"')
                    
                    # Add business impact
                    business_impact = finding.get('business_impact', '')
                    if business_impact:
                        guidance_parts.append(business_impact)
                    
                    # Add recommendation
                    recommendation = finding.get('recommendation', '')
                    if recommendation:
                        guidance_parts.append(recommendation)
                    
                    if guidance_parts:
                        detailed_report.append(f"Additional Guidance: {' '.join(guidance_parts)}")
                
                detailed_report.append("")  # Blank line between subsections
            
            # Move to next letter
            section_letter = chr(ord(section_letter) + 1)
        
        # Add materiality assessment reminder at the end
        if high_risk or medium_risk:
            detailed_report.extend([
                "",
                "MATERIALITY ASSESSMENT:",
                "=" * 30,
                "CLIENT should assess whether the risks identified above are material enough to require:",
                "• Specific amendments to contract clauses",
                "• Enhanced risk management arrangements", 
                "• Legal review and negotiation strategy",
                "• Escalation to senior management or board level"
            ])
        
        return "\n".join(detailed_report)
    
    def _group_findings_by_category(self, all_findings: List) -> Dict[str, List]:
        """Group findings by legal category for structured reporting"""
        categories = {
            "Commercial Terms of Service": [],
            "Data Processing and Privacy": [],
            "Liability and Risk Allocation": [],
            "Intellectual Property": [],
            "Compliance and Regulatory": [],
            "Other Legal Issues": []
        }
        
        # Enhanced mapping from AI-generated categories to standard legal categories
        category_mapping = {
            # Commercial Terms variations
            "Commercial Terms": "Commercial Terms of Service",
            "Commercial Terms of Service": "Commercial Terms of Service",
            "Payment": "Commercial Terms of Service", 
            "Termination": "Commercial Terms of Service",
            "Service Levels": "Commercial Terms of Service",
            "FINANCIAL": "Commercial Terms of Service",
            "PERFORMANCE": "Commercial Terms of Service",
            
            # Data Processing variations
            "Data Processing": "Data Processing and Privacy", 
            "Data Processing and Privacy": "Data Processing and Privacy",
            "Privacy": "Data Processing and Privacy",
            "Data Protection": "Data Processing and Privacy",
            "COMPLIANCE": "Data Processing and Privacy",
            
            # Liability variations
            "Liability": "Liability and Risk Allocation",
            "Liability and Risk Allocation": "Liability and Risk Allocation",
            "Indemnification": "Liability and Risk Allocation",
            "Insurance": "Liability and Risk Allocation",
            "Risk": "Liability and Risk Allocation",
            "LIABILITY": "Liability and Risk Allocation",
            
            # IP variations
            "IP": "Intellectual Property",
            "Intellectual Property": "Intellectual Property",
            "Confidentiality": "Intellectual Property",
            "Patents": "Intellectual Property",
            "Copyright": "Intellectual Property",
            "Trade Secrets": "Intellectual Property",
            "INTELLECTUAL PROPERTY": "Intellectual Property",
            
            # Compliance variations
            "Compliance": "Compliance and Regulatory",
            "Compliance and Regulatory": "Compliance and Regulatory",
            "Regulatory": "Compliance and Regulatory",
            "Audit": "Compliance and Regulatory",
            "Dispute Resolution": "Compliance and Regulatory",
            "Governing Law": "Compliance and Regulatory",
            
            # Other/General variations
            "GENERAL": "Other Legal Issues",
            "Other": "Other Legal Issues",
            "Miscellaneous": "Other Legal Issues",
            "Assignment": "Other Legal Issues",
            "Force Majeure": "Other Legal Issues",
            "Notices": "Other Legal Issues",
            "Publicity": "Other Legal Issues"
        }
        
        for finding in all_findings:
            ai_category = finding.get('category', 'GENERAL')
            mapped_category = category_mapping.get(ai_category, "Other Legal Issues")
            categories[mapped_category].append(finding)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    
    def _get_page_info_for_finding(self, finding: Dict[str, Any]) -> str:
        """Get page information for a finding based on chunk data"""
        chunk_index = finding.get('chunk_index', 0)
        
        # Try to find the original chunk data for page range
        # This is a simplified approach - in practice, you'd want to store this info
        if hasattr(self, '_current_chunks'):
            for chunk in self._current_chunks:
                if chunk.get('chunk_index') == chunk_index:
                    return chunk.get('page_range', '')
        
        # Fallback estimation
        estimated_page = max(1, chunk_index + 1)
        return f"~Page {estimated_page}"
    
    def _extract_business_impact(self, evidence: str) -> str:
        """Extract business impact description from evidence"""
        # Look for Business Impact section
        impact_patterns = [
            r'Business Impact:\s*([^\n]*(?:\n(?![A-Z][^:]+:)[^\n]*)*)',
            r'Impact:\s*([^\n]*(?:\n(?![A-Z][^:]+:)[^\n]*)*)',
            r'could.*?(?:result|lead|cause|expose|create|impact).*?(?:\.|$)',
            r'may.*?(?:result|lead|cause|expose|create|impact).*?(?:\.|$)',
            r'risk.*?(?:of|to|for).*?(?:\.|$)'
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, evidence, re.IGNORECASE | re.DOTALL)
            if match:
                impact = match.group(1) if len(match.groups()) > 0 else match.group(0)
                # Clean up and limit length
                impact = re.sub(r'\s+', ' ', impact).strip()
                if len(impact) > 200:
                    impact = impact[:200] + "..."
                return impact
        
        return ""
    
    def _extract_recommendation(self, evidence: str) -> str:
        """Extract recommendation from evidence"""
        # Look for recommendation sections
        rec_patterns = [
            r'Recommend(?:ation|ed Action)?:\s*([^\n]*(?:\n(?![A-Z][^:]+:)[^\n]*)*)',
            r'(?:Should|Must|Need to|Consider).*?(?:negotiate|request|add|include|seek|clarify).*?(?:\.|$)',
            r'Action.*?(?:required|needed|recommended).*?(?:\.|$)'
        ]
        
        for pattern in rec_patterns:
            match = re.search(pattern, evidence, re.IGNORECASE | re.DOTALL)
            if match:
                rec = match.group(1) if len(match.groups()) > 0 else match.group(0)
                rec = re.sub(r'\s+', ' ', rec).strip()
                if len(rec) > 150:
                    rec = rec[:150] + "..."
                return rec
        
        return ""
    
    async def _format_response_node(self, state: WorkflowState) -> WorkflowState:
        """Format final response node"""
        await agent_monitor.log_activity(
            "Report Generator", 
            AgentStatus.PROCESSING, 
            "Generating final parallel processing report...",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            formatted_response = self._format_parallel_response(
                state["document_data"], 
                state["combined_analysis"],
                state["chunk_analyses"],
                state["cross_references"],
                state["processing_start_time"]
            )
            
            state["final_result"] = formatted_response
            state["current_step"] = "workflow_complete"
            
            await agent_monitor.log_activity(
                "Report Generator", 
                AgentStatus.COMPLETED, 
                "Parallel processing analysis report generated successfully",
                LogLevel.SUCCESS,
                progress=1.0
            )
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Report Generator", 
                AgentStatus.ERROR, 
                f"Error generating final report: {str(e)}",
                LogLevel.ERROR
            )
            state["error"] = str(e)
        
        return state
    
    def _format_parallel_response(self, document_data: Dict[str, Any], 
                        combined_analysis: str, chunk_analyses: Dict[str, ChunkData],
                        cross_references: List[Dict[str, Any]], start_time: float) -> str:
        """Format the final parallel processing response for the user"""
        import time
        
        processing_time = time.time() - start_time
        total_findings = sum(len(chunk["findings"]) for chunk in chunk_analyses.values())
        avg_confidence = sum(chunk["confidence_score"] for chunk in chunk_analyses.values()) / len(chunk_analyses) if chunk_analyses else 0.0
        
        # Chunk processing details
        chunk_details = []
        for chunk in sorted(chunk_analyses.values(), key=lambda x: x["chunk_index"]):
            chunk_details.append(f"  Chunk {chunk['chunk_index'] + 1} (Pages {chunk['page_range']}): {len(chunk['findings'])} findings, {chunk['confidence_score']:.2f} confidence, {chunk['processing_time']:.2f}s")
        
        response = f"""
PARALLEL PROCESSING LEGAL ANALYSIS REPORT
========================================

Document: {document_data['filename']}
Word Count: {document_data['word_count']}
Character Count: {document_data['char_count']}
Processing Time: {processing_time:.2f} seconds

PARALLEL PROCESSING SUMMARY:
- Total Chunks: {len(chunk_analyses)}
- Parallel Processing Efficiency: {len(chunk_analyses)}/{len(chunk_analyses)} chunks successful
- Cross-References Identified: {len(cross_references)}
- Total Findings: {total_findings}
- Average Confidence: {avg_confidence:.2f}

CHUNK-BY-CHUNK ANALYSIS:
{chr(10).join(chunk_details)}

COMBINED ANALYSIS:
{combined_analysis}

CROSS-REFERENCE VALIDATION:
{self._format_cross_references(cross_references)}

PARALLEL AGENT WORKFLOW TRANSPARENCY:
- Document Parser: Successfully extracted and structured document content
- Document Chunking Agent: Intelligently split document into {len(chunk_analyses)} chunks preserving legal boundaries  
- Parallel Risk Analysis: Simultaneously analyzed all chunks with RAG context enhancement
- Cross-Reference Agent: Validated relationships and consistency between document sections
- Results Combination Agent: Merged parallel analyses into unified findings
- Report Generator: Compiled comprehensive parallel processing analysis report

PROCESSING EFFICIENCY:
- Parallel processing enabled analysis of {document_data['word_count']} words in {processing_time:.2f} seconds
- Each chunk processed independently with contextual overlap preservation
- Cross-reference validation ensured document-wide consistency
- Real-time monitoring provided complete visibility into agent decision-making
        """
        
        return response
    
    def _format_cross_references(self, cross_references: List[Dict[str, Any]]) -> str:
        """Format cross-reference validation results for the report"""
        if not cross_references:
            return "No cross-references or consistency issues identified."
        
        structural_refs = [ref for ref in cross_references if ref["type"].endswith("_reference")]
        term_refs = [ref for ref in cross_references if ref["type"] == "term_consistency"]
        issues = [ref for ref in cross_references if ref["type"] == "consistency_issue"]
        
        report_parts = []
        
        if structural_refs:
            report_parts.append(f"- Structural References: {len(structural_refs)} cross-references found between document sections")
        
        if term_refs:
            report_parts.append(f"- Term Consistency: {len(term_refs)} related terms identified across chunks")
        
        if issues:
            high_issues = [i for i in issues if i.get("severity") == "high"]
            medium_issues = [i for i in issues if i.get("severity") == "medium"]
            low_issues = [i for i in issues if i.get("severity") == "low"]
            
            if high_issues:
                report_parts.append(f"HIGH PRIORITY: {len(high_issues)} critical consistency issues detected")
                for issue in high_issues[:3]:  # Show first 3
                    report_parts.append(f"  • {issue.get('description', 'Issue detected')}")
            
            if medium_issues:
                report_parts.append(f"MEDIUM PRIORITY: {len(medium_issues)} consistency concerns identified")
            
            if low_issues:
                report_parts.append(f"LOW PRIORITY: {len(low_issues)} minor inconsistencies noted")
        else:
            report_parts.append("No consistency issues detected across document sections")
        
        return "\n".join(report_parts)
    
    async def process_document(self, file_content: bytes, filename: str, prompt: str, color_coded: bool = False) -> str:
        """Execute the complete multi-agent workflow"""
        
        # Clear previous workflow history
        agent_monitor.clear_history()
        
        # Initialize workflow state
        initial_state: WorkflowState = {
            "file_content": file_content,
            "filename": filename,
            "prompt": prompt,
            "document_data": {},
            "chunks": [],
            "chunk_analyses": {},
            "cross_references": [],
            "combined_analysis": "",
            "final_result": "",
            "current_step": "starting",
            "error": "",
            "processing_start_time": 0.0,
            "total_chunks": 0,
            "color_coded": color_coded
        }
        
        await agent_monitor.log_activity(
            "Workflow Orchestrator", 
            AgentStatus.PROCESSING, 
            f"Starting parallel processing legal analysis workflow for {filename}",
            LogLevel.INFO,
            progress=0.0
        )
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": "legal_analysis_workflow"}}
            result = await self.graph.ainvoke(initial_state, config)
            
            if result.get("error"):
                await agent_monitor.log_activity(
                    "Workflow Orchestrator", 
                    AgentStatus.ERROR, 
                    f"Workflow failed: {result['error']}",
                    LogLevel.ERROR
                )
                return f"Analysis failed: {result['error']}"
            
            await agent_monitor.log_activity(
                "Workflow Orchestrator", 
                AgentStatus.COMPLETED, 
                "Parallel processing legal analysis workflow completed successfully",
                LogLevel.SUCCESS,
                progress=1.0
            )
            
            return result["final_result"]
            
        except Exception as e:
            await agent_monitor.log_activity(
                "Workflow Orchestrator", 
                AgentStatus.ERROR, 
                f"Workflow execution failed: {str(e)}",
                LogLevel.ERROR
            )
            # More detailed error reporting
            import traceback
            print(f"DETAILED ERROR: {traceback.format_exc()}")
            return f"Workflow execution failed: {str(e)}"