# TayLaw - Legal AI Assistant Project

## Project Description
We are building an AI-powered SaaS platform to streamline legal workflows for in-house legal teams and smaller law firms. Our goal is to create a more affordable alternative to Harvey AI, focusing on core legal document analysis tasks with high accuracy and user-friendly interfaces.

## Team Structure
- **Legal Expert**: Handles business requirements, output validation, and legal accuracy assessment
- **Technical Lead 1**: Senior business analyst responsible for solution architecture and technical design  
- **Technical Lead 2**: Senior business analyst responsible for development and implementation
- **Development Tool**: Claude Code for primary development with focus on non-technical accessibility

## Core Features (Initial Scope)
1. **Red Flags Review** - Automated contract risk assessment and compliance issue identification
2. **Review Against Base & Summarize Changes** - Compare contract versions and highlight modifications with impact analysis
3. **Negotiation Support** - Help draft responses, track departures from standard terms, and summarize changes across negotiation rounds

## Technical Architecture

### Multi-Agent System Design with LangGraph

**Core Architecture Pattern:**
- **Parallel Processing**: Documents chunked and analyzed simultaneously for speed
- **Smart Chunking**: Preserves legal context by breaking at natural boundaries
- **Cross-Reference Validation**: Secondary pass to check relationships between chunks
- **Quality Control**: Multi-layer validation ensures consistent analysis

**Agent Definitions:**
- **Orchestrator Agent**: Manages overall workflow and coordinates all other agents using LangGraph
- **Document Chunking Agent**: Intelligently splits documents while preserving legal structure
- **RAG Search Agent**: Finds relevant legal knowledge and context for each chunk
- **Risk Analysis Agent**: Performs parallel red flag analysis on individual chunks
- **Cross-Reference Agent**: Validates relationships and consistency between chunks
- **Results Combination Agent**: Merges individual chunk analyses into final report
- **Comparison Agent**: Analyzes differences between document versions (Phase 2)
- **Negotiation Support Agent**: Assists with drafting and strategy (Phase 3)

### Technology Stack
- **Backend**: Python with FastAPI for AI processing microservice
- **Frontend**: Next.js for user interface and file management
- **AI Framework**: LangGraph for multi-agent orchestration and workflow management
- **LLM APIs**: Claude API (primary), with OpenAI GPT-4 as fallback
- **Knowledge Base**: RAG system using vector database (Pinecone/Chroma) for legal document retrieval
- **Database**: PostgreSQL for user data, vector DB for legal knowledge
- **Integration**: Model Context Protocol (MCP) for data source connections

### Agent Visibility and Debugging System
**Critical Requirement**: Full transparency into parallel processing for non-technical users
- **Real-time Parallel Monitoring**: Track progress of multiple chunks simultaneously
- **Chunk-Level Status**: Show individual chunk processing status and completion
- **Agent Activity Logging**: Record decisions made by each agent on each chunk
- **Cross-Reference Tracking**: Visualize relationships identified between document sections
- **Error Handling with Context**: Clear explanations when specific chunks fail analysis
- **Progress Aggregation**: Overall document analysis progress from parallel streams
- **Quality Metrics Dashboard**: Show confidence scores and validation results

### LangGraph Implementation Strategy
- **Parallel Workflow Management**: Orchestrate simultaneous chunk processing with proper state management
- **Conditional Routing**: Different agent sequences for different use cases (red flags vs comparison vs negotiation)
- **Error Recovery**: Graceful handling when individual chunks fail analysis
- **Progress Tracking**: Real-time monitoring of parallel processing status
- **State Coordination**: Manage data flow between parallel processes and final combination

### Document Processing Architecture
**Phase 1: Intelligent Chunking**
- **Clause-Aware Splitting**: Break documents at natural legal boundaries (sections, clauses)
- **Context Preservation**: 200-word overlap between chunks to maintain legal context
- **Dynamic Sizing**: Adjust chunk size based on content type (definitions, liability clauses, etc.)
- **Header Inclusion**: Preserve section titles and clause numbers with each chunk

**Phase 2: Parallel Analysis**
- **Simultaneous Processing**: All chunks analyzed concurrently for speed
- **RAG Enhancement**: Each chunk gets relevant legal knowledge context
- **Consistent Scoring**: Standardized risk assessment across all chunks
- **Evidence Validation**: Every finding requires supporting text quotes

**Phase 3: Cross-Reference Validation**
- **Dependency Checking**: Identify references between different document sections
- **Consistency Validation**: Flag conflicting terms or inconsistent requirements
- **Document-Wide Logic**: Ensure overall contract coherence

**Phase 4: Quality Control & Combination**
- **Multi-Layer Validation**: Verify completeness and accuracy of each finding
- **Results Merging**: Intelligent combination of chunk analyses into unified report
- **Confidence Scoring**: Rate reliability of findings for lawyer review

### AI Approach
- **RAG System**: Preferred over fine-tuning for flexibility and cost-effectiveness
- **Domain-Specific Prompting**: Specialized prompts for each agent type optimized for legal tasks
- **Iterative Improvement**: System learns from lawyer feedback to improve accuracy
- **Context Management**: Smart chunking to handle long legal documents within AI context limits

## Development Approach

### Phase 1: Core Red Flags with Parallel Processing (Weeks 1-4)
- **Week 1-2**: Implement LangGraph architecture with intelligent document chunking and parallel analysis
- **Week 3**: Add cross-reference validation and results combination system
- **Week 4**: Integrate agent visibility dashboard and legal expert validation framework

### Phase 2: Document Comparison Capability (Weeks 5-8)
- **Week 5-6**: Build comparison agent for version analysis
- **Week 7**: Integrate with red flags workflow
- **Week 8**: User testing and refinement

### Phase 3: Negotiation Support Features (Weeks 9-12)
- **Week 9-10**: Develop negotiation support agent
- **Week 11**: Complete workflow integration
- **Week 12**: Full system testing and optimization

### Non-Technical Developer Considerations
- **Claude Code Integration**: All development requests structured for Claude Code assistance
- **Visual Debugging Tools**: Frontend interfaces to monitor agent behavior without code inspection
- **Configuration Files**: JSON-based agent configuration for easy modification
- **Template System**: Predefined prompts and workflows that can be adjusted without programming
- **Evaluation Dashboard**: Simple metrics and comparison tools for measuring improvements

## Key Technical Considerations
- **Parallel Document Processing**: Handle complex legal documents through intelligent chunking while preserving context
- **Agent Coordination**: Ensure reliable parallel processing and proper state management between agents
- **Cross-Reference Intelligence**: Validate relationships and dependencies between different document sections
- **Quality Assurance**: Multi-layer validation system with evidence requirements and confidence scoring
- **User Interface**: Intuitive side-by-side interface with real-time parallel processing monitoring
- **Performance**: Efficient parallel processing of large legal documents within 2-minute target
- **Security**: Legal-grade security for sensitive document handling
- **Scalability**: Architecture supports adding new analysis types and document processing capabilities

## Success Metrics
- **Processing Speed**: Parallel analysis completes within 2 minutes for typical contracts
- **Analysis Consistency**: Same document produces same results across multiple runs (95% consistency)
- **Chunk Processing Reliability**: Individual chunk analysis success rate above 98%
- **Cross-Reference Accuracy**: Correct identification of document relationships and dependencies
- **Legal Expert Validation**: Lawyer-validated comparison against baseline performance
- **User Satisfaction**: Lawyer feedback scores on output quality and parallel processing transparency
- **System Reliability**: Successful completion rate of full document analysis workflows
- **Agent Transparency**: Non-technical users can understand parallel processing status and results

## Evaluation Framework
- **Baseline Testing**: Establish performance metrics before each major change
- **A/B Comparison**: Side-by-side testing of system improvements
- **Legal Expert Validation**: Continuous lawyer review of AI outputs
- **Consistency Testing**: Verify identical inputs produce identical results
- **Speed Benchmarking**: Track processing time improvements

## Risk Mitigation
- **Legal Accuracy**: Continuous lawyer validation and feedback loops
- **Data Security**: Implement legal-grade security and compliance measures
- **System Reliability**: Comprehensive error handling and recovery mechanisms
- **Performance Monitoring**: Real-time tracking of system performance and user satisfaction
- **Scalability Planning**: Architecture designed for growth in users and document volume

## Development Philosophy
- **Transparency First**: Every agent decision must be visible and explainable
- **Non-Technical Friendly**: System designed for business analysts to modify and improve
- **Lawyer-Centric**: All features validated by legal expert before implementation
- **Iterative Improvement**: Continuous refinement based on real-world usage
- **Commercial Focus**: Built for business value, not academic research

## Development Environment
- **Operating System**: Windows-based development environment
- **Command Line**: Use Windows-compatible commands (PowerShell/Command Prompt)
- **File Paths**: Use Windows path format with backslashes (C:\path\to\file)
- **Path Separators**: Use backslashes (\) not forward slashes (/) for file operations
- **Shell Commands**: Prefer Windows native commands or cross-platform tools
- **File Operations**: Use Windows-compatible file manipulation commands

## File Organization Rules
- **Debug Files**: All test, debug, and temporary files MUST be saved to the `debug\` folder
- **Test Scripts**: Any .py files for testing, debugging, or experimentation go in `debug\`
- **Temporary Files**: Log files, sample outputs, and temporary data files go in `debug\`
- **Keep Root Clean**: Only production code, documentation, and essential config files in project root