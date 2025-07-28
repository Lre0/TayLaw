'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import AgentMonitor from './AgentMonitor'
import DocumentTabs from './DocumentTabs'
import AnalysisResults from './AnalysisResults'
import ScrollableIssuesList from './ScrollableIssuesList'

interface DocumentFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'analyzing' | 'completed' | 'failed'
  analysis?: string
  error?: string
  progress: number
}

interface BatchResult {
  batch_id: string
  total_documents: number
  completed: number
  failed: number
  analysis_type: 'unified' | 'individual'
  // For unified analysis
  unified_analysis?: string
  source_documents?: string[]
  // For individual analysis (fallback)
  results?: Array<{
    filename: string
    status: 'completed' | 'failed'
    analysis?: string
    error?: string
  }>
}

interface PredefinedPrompt {
  id: string
  name: string
  description: string
  template: string
  version: string
}

export default function MultiDocumentUpload() {
  const [documents, setDocuments] = useState<DocumentFile[]>([])
  const [selectedPromptId, setSelectedPromptId] = useState('red-flags-review')
  const [customPrompt, setCustomPrompt] = useState('')
  const [userContext, setUserContext] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null)
  const [currentBatchId, setCurrentBatchId] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [realTimeProgress, setRealTimeProgress] = useState<Record<string, number>>({})
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null)
  const [layoutMode, setLayoutMode] = useState<'split' | 'docs-full' | 'analysis-full'>('split')
  const [highlightClause, setHighlightClause] = useState<string | null>(null)
  const [showIssuesList, setShowIssuesList] = useState(false)

  // Predefined prompts with version control - Core TayLaw Use Cases
  const predefinedPrompts: PredefinedPrompt[] = [
    {
      id: 'red-flags-review',
      name: 'Red Flags Review',
      description: 'Automated contract risk assessment and compliance issue identification with evidence-based findings',
      template: 'Please perform a comprehensive red flags review on this contract, identifying potential legal risks, compliance issues, and problematic clauses. Focus on liability limitations, termination conditions, payment terms, intellectual property clauses, indemnification provisions, and any unusual or potentially problematic terms. Provide specific evidence from the contract text for each identified risk.',
      version: '1.0'
    },
    {
      id: 'review-against-base',
      name: 'Review Against Base & Summarize Changes',
      description: 'Compare contract versions and highlight modifications with impact analysis',
      template: 'Compare this contract against standard templates or previous versions to identify all changes and modifications. Highlight additions, deletions, and alterations. Assess the business impact and legal risk of each change. Summarize departures from standard terms and flag any modifications that require special attention during review.',
      version: '1.0'
    },
    {
      id: 'negotiation-support',
      name: 'Negotiation Support',
      description: 'Help draft responses, track departures from standard terms, and analyze negotiation positions',
      template: 'Analyze this contract for negotiation support. Identify unfavorable terms, track departures from standard positions, and suggest negotiation strategies. Highlight key terms that should be challenged, modified, or accepted. Provide recommendations for response drafting and position strength assessment on critical clauses.',
      version: '1.0'
    },
    {
      id: 'custom',
      name: 'Custom Analysis',
      description: 'Create your own analysis instructions for specialized use cases',
      template: '',
      version: '1.0'
    }
  ]

  // Get the final prompt combining predefined template with user context
  const getFinalPrompt = () => {
    const selectedPrompt = predefinedPrompts.find(p => p.id === selectedPromptId)
    const basePrompt = selectedPromptId === 'custom' ? customPrompt : selectedPrompt?.template || ''
    
    if (userContext.trim()) {
      return `${basePrompt}\n\nAdditional Context: ${userContext}`
    }
    return basePrompt
  }

  // Get context placeholder based on selected prompt
  const getContextPlaceholder = () => {
    switch (selectedPromptId) {
      case 'red-flags-review':
        return 'e.g., "This is a cloud services vendor agreement. We\'re particularly concerned about data privacy, service level guarantees, and liability limitations given our startup status."'
      case 'review-against-base':
        return 'e.g., "Compare against our standard vendor template. Focus on changes to payment terms, termination clauses, and any new liability provisions that weren\'t in our original draft."'
      case 'negotiation-support':
        return 'e.g., "We\'re a small company with limited insurance coverage. Looking to minimize liability exposure and secure favorable termination rights in this partnership deal."'
      case 'custom':
        return 'Provide specific context about your business situation, concerns, or requirements...'
      default:
        return 'Provide additional business context, specific concerns, or background information...'
    }
  }

  // Get example contexts based on selected prompt
  const getExampleContexts = () => {
    switch (selectedPromptId) {
      case 'red-flags-review':
        return [
          'This is a SaaS vendor agreement for our healthcare startup. We need HIPAA compliance and are concerned about data breach liability.',
          'Enterprise software license for a Fortune 500 company. Focus on intellectual property protection and indemnification clauses.',
          'Cloud hosting agreement for an e-commerce platform. Key concerns are uptime guarantees and data sovereignty requirements.'
        ]
      case 'review-against-base':
        return [
          'Compare against our standard MSA template from legal. Highlight any changes to payment terms, IP ownership, or limitation of liability.',
          'This is version 3 of negotiations. Focus on what changed from our last counteroffer, especially around termination and data retention.',
          'Client sent this redlined version. Need to understand impact of their changes on our standard risk allocation and pricing model.'
        ]
      case 'negotiation-support':
        return [
          'We\'re a startup with limited bargaining power but need to protect our core IP. Help identify which terms we should push back on vs. accept.',
          'Large enterprise client with significant leverage. Need strategy for negotiating more balanced liability terms without losing the deal.',
          'Partnership agreement where both parties contribute resources. Focus on exit rights and dispute resolution mechanisms.'
        ]
      case 'custom':
        return [
          'Industry-specific regulatory requirements we need to consider...',
          'Specific business model constraints or requirements...',
          'Prior experience or concerns from similar agreements...'
        ]
      default:
        return ['Add context about your specific situation...']
    }
  }

  const handleDocumentReference = useCallback((documentId: string) => {
    setActiveDocumentId(documentId)
    // Auto-switch to split view if currently in analysis-full mode
    if (layoutMode === 'analysis-full') {
      setLayoutMode('split')
    }
  }, [layoutMode])

  const handleClauseClick = useCallback((documentId: string, clause: string, lineNumber?: number) => {
    setActiveDocumentId(documentId)
    setHighlightClause(clause)
    // Auto-switch to split view to show both document and analysis
    if (layoutMode === 'analysis-full') {
      setLayoutMode('split')
    }
    // Clear highlight after a few seconds
    setTimeout(() => setHighlightClause(null), 5000)
  }, [layoutMode])

  // Auto-select first document when documents change
  const handleDocumentSelection = useCallback(() => {
    if (documents.length > 0 && !activeDocumentId) {
      setActiveDocumentId(documents[0].id)
    }
    // Reset to split mode for single documents
    if (documents.length === 1 && layoutMode !== 'split') {
      setLayoutMode('split')
    }
  }, [documents, activeDocumentId, layoutMode])

  // Effect to handle document selection
  React.useEffect(() => {
    handleDocumentSelection()
  }, [handleDocumentSelection])

  // Drag and drop handler
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newDocuments = acceptedFiles.map((file, index) => ({
      id: `doc_${Date.now()}_${index}`,
      file,
      status: 'pending' as const,
      progress: 0
    }))
    
    setDocuments(prev => [...prev, ...newDocuments])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxFiles: 10
  })

  const removeDocument = (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id))
  }

  const clearAll = () => {
    setDocuments([])
    setBatchResult(null)
    setCurrentBatchId(null)
    setRealTimeProgress({})
  }

  // Real-time progress tracking
  const pollBatchStatus = async (batchId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/batch-status/${batchId}`)
      if (response.ok) {
        const status = await response.json()
        
        // Update document statuses and progress
        setDocuments(prev => prev.map(doc => {
          const statusDoc = status.documents?.find((d: { filename: string }) => d.filename === doc.file.name)
          if (statusDoc) {
            return {
              ...doc,
              status: statusDoc.status as 'pending' | 'uploading' | 'analyzing' | 'completed' | 'failed',
              progress: statusDoc.progress || doc.progress
            }
          }
          return doc
        }))

        // Check if batch is complete
        const isComplete = status.documents?.every((d: { status: string }) => 
          d.status === 'completed' || d.status === 'failed'
        )
        
        if (isComplete) {
          console.log('🎯 Batch complete - fetching final results...')
          console.log(`📊 Fetching results from: /api/batch-results/${batchId}`)
          const resultsResponse = await fetch(`http://localhost:8000/api/batch-results/${batchId}`)
          if (resultsResponse.ok) {
            const results = await resultsResponse.json()
            console.log('✅ Final results received, stopping polling')
            setBatchResult(results)
            setIsProcessing(false)
            setCurrentBatchId(null)
            // Return false immediately to stop polling
            return false
          } else {
            console.error('❌ Failed to fetch results:', resultsResponse.status)
          }
        }
        
        return !isComplete
      }
    } catch (error) {
      console.error('Error polling batch status:', error)
      return false
    }
    return false
  }


  const handleSubmit = async () => {
    const finalPrompt = getFinalPrompt()
    if (documents.length === 0 || !finalPrompt.trim()) return

    // Debug: Log the final prompt being sent to API
    console.log('🔍 TayLaw Debug - Final Prompt Being Sent:', finalPrompt)
    console.log('📝 Selected Prompt ID:', selectedPromptId)
    console.log('💼 User Context:', userContext || '(none)')
    console.log('📄 Documents:', documents.map(d => d.file.name))

    setIsProcessing(true)
    setBatchResult(null)

    // Update all documents to uploading status
    setDocuments(prev => prev.map(doc => ({ ...doc, status: 'uploading' as const, progress: 10 })))

    try {
      const formData = new FormData()
      documents.forEach(doc => formData.append('files', doc.file))
      formData.append('prompt', finalPrompt)

      // Update to analyzing status
      setDocuments(prev => prev.map(doc => ({ ...doc, status: 'analyzing' as const, progress: 30 })))

      const response = await fetch('http://localhost:8000/api/analyze-multiple', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to analyze documents: ${response.statusText}`)
      }

      const result: BatchResult = await response.json()
      
      // If the new multi-document orchestrator returns a batch_id, use real-time tracking
      if (result.batch_id) {
        setCurrentBatchId(result.batch_id)
        
        // Start polling for status updates
        const pollInterval = setInterval(async () => {
          try {
            const shouldContinue = await pollBatchStatus(result.batch_id!)
            if (!shouldContinue) {
              console.log('🛑 Stopping polling interval')
              clearInterval(pollInterval)
            }
          } catch (error) {
            console.error('Polling error:', error)
            clearInterval(pollInterval)
            setIsProcessing(false)
          }
        }, 1000) // Poll every second
        
        // Set a maximum polling time
        setTimeout(() => {
          clearInterval(pollInterval)
          if (isProcessing) {
            setIsProcessing(false)
            console.error('Polling timeout reached')
          }
        }, 300000) // 5 minutes max
      } else {
        // Fallback to old behavior if batch_id not returned
        setBatchResult(result)
        
        // Update document statuses based on results
        if (result.analysis_type === 'individual' && result.results) {
          // Handle individual results
          setDocuments(prev => prev.map(doc => {
            const analysis = result.results!.find(r => r.filename === doc.file.name)
            if (analysis) {
              return {
                ...doc,
                status: analysis.status === 'completed' ? 'completed' : 'failed',
                analysis: analysis.analysis,
                error: analysis.error,
                progress: 100
              }
            }
            return { ...doc, status: 'failed' as const, error: 'No result found', progress: 100 }
          }))
        } else {
          // For unified analysis, mark all documents as completed
          setDocuments(prev => prev.map(doc => ({
            ...doc,
            status: 'completed' as const,
            analysis: 'See unified analysis below',
            progress: 100
          })))
        }
        
        setIsProcessing(false)
      }

    } catch (error) {
      console.error('Error:', error)
      setDocuments(prev => prev.map(doc => ({ 
        ...doc, 
        status: 'failed' as const, 
        error: error instanceof Error ? error.message : 'Unknown error',
        progress: 100
      })))
      setIsProcessing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800'
      case 'uploading': return 'bg-blue-100 text-blue-800'
      case 'analyzing': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'uploading': return '📤'
      case 'analyzing': return '🔍'
      case 'completed': return '✅'
      case 'failed': return '❌'
      default: return '❓'
    }
  }

  const downloadBatchReport = () => {
    if (!batchResult) return

    const analysisContent = batchResult.unified_analysis || batchResult.results?.[0]?.analysis || 'Analysis completed successfully.'
    
    // Generate report based on document count
    const reportTitle = batchResult.total_documents === 1 
      ? 'LEGAL DOCUMENT ANALYSIS REPORT'
      : 'MULTI-DOCUMENT LEGAL ANALYSIS REPORT'
    
    const reportContent = `${reportTitle}
${'='.repeat(reportTitle.length)}

Analysis Date: ${new Date().toLocaleDateString()}
${batchResult.total_documents > 1 ? `Total Documents Analyzed: ${batchResult.total_documents}` : ''}
${batchResult.completed > 0 ? `Successfully Processed: ${batchResult.completed}` : ''}
${batchResult.failed > 0 ? `Failed: ${batchResult.failed}` : ''}
${batchResult.source_documents && batchResult.source_documents.length > 1 ? `\nSource Documents: ${batchResult.source_documents.join(', ')}` : ''}

${analysisContent}

${'='.repeat(40)}
Generated by TayLaw Legal AI Assistant
`

    const blob = new Blob([reportContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const fileName = batchResult.total_documents === 1 
      ? `legal_analysis_${new Date().toISOString().split('T')[0]}.txt`
      : `multi_document_analysis_${new Date().toISOString().split('T')[0]}.txt`
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-[95vw] mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Legal Document Analysis</h1>
        <p className="text-gray-600">Upload one or more legal documents for comprehensive analysis</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          {isDragActive ? (
            <p className="text-blue-600 font-medium">Drop the documents here...</p>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">Drag and drop documents here, or <span className="text-blue-600 font-medium">click to browse</span></p>
              <p className="text-sm text-gray-500">Supports PDF, Word, and Text files • Upload single documents or batches up to 10</p>
            </div>
          )}
        </div>

        {/* Analysis Configuration */}
        <div className="mt-6 space-y-6">
          {/* Predefined Prompt Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Analysis Type
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {predefinedPrompts.map((promptOption) => (
                <div
                  key={promptOption.id}
                  onClick={() => setSelectedPromptId(promptOption.id)}
                  className={`cursor-pointer p-4 border-2 rounded-lg transition-all ${
                    selectedPromptId === promptOption.id
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 ${
                      selectedPromptId === promptOption.id
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {selectedPromptId === promptOption.id && (
                        <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-medium text-gray-900 mb-1">
                        {promptOption.name}
                      </h4>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {promptOption.description}
                      </p>
                      <div className="mt-2 text-xs text-gray-400">
                        v{promptOption.version}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Prompt Input (only shown when custom is selected) */}
          {selectedPromptId === 'custom' && (
            <div>
              <label htmlFor="customPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                Custom Analysis Instructions
              </label>
              <textarea
                id="customPrompt"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
                placeholder="Enter your custom analysis instructions..."
              />
            </div>
          )}

          {/* User Context Input */}
          <div>
            <label htmlFor="userContext" className="block text-sm font-medium text-gray-700 mb-2">
              Business Context <span className="text-gray-500 font-normal">(Optional)</span>
              <span className="ml-2 text-xs text-blue-600">
                {userContext.length}/500 characters
              </span>
            </label>
            <textarea
              id="userContext"
              value={userContext}
              onChange={(e) => setUserContext(e.target.value.slice(0, 500))}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder={getContextPlaceholder()}
            />
            <div className="mt-2 space-y-1">
              <p className="text-xs text-gray-500">
                This context will be combined with the selected analysis type to provide more targeted results.
              </p>
              {/* Example contexts based on selected prompt */}
              <details className="text-xs text-gray-500">
                <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                  💡 See example contexts for {predefinedPrompts.find(p => p.id === selectedPromptId)?.name}
                </summary>
                <div className="mt-2 pl-4 border-l-2 border-blue-200 space-y-1">
                  {getExampleContexts().map((example, index) => (
                    <div key={index} className="text-gray-600">
                      <span className="font-medium">Example {index + 1}:</span> "{example}"
                    </div>
                  ))}
                </div>
              </details>
            </div>
          </div>

          {/* Preview of Final Prompt */}
          {(selectedPromptId !== 'custom' || customPrompt.trim()) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-800 mb-3 flex items-center">
                <span className="mr-2">👁️</span>
                Analysis Preview - What Will Be Sent to AI:
              </h4>
              <div className="space-y-3">
                {/* Base Prompt */}
                <div>
                  <div className="text-xs font-medium text-blue-700 mb-1">Base Analysis Template:</div>
                  <div className="text-xs text-gray-700 bg-white rounded p-2 border">
                    {selectedPromptId === 'custom' ? customPrompt : predefinedPrompts.find(p => p.id === selectedPromptId)?.template || 'No template selected'}
                  </div>
                </div>
                
                {/* User Context (if provided) */}
                {userContext.trim() && (
                  <div>
                    <div className="text-xs font-medium text-green-700 mb-1 flex items-center">
                      <span className="mr-1">💼</span>
                      + Your Business Context:
                    </div>
                    <div className="text-xs text-gray-700 bg-green-50 rounded p-2 border border-green-200">
                      {userContext}
                    </div>
                  </div>
                )}
                
                {/* Character Count */}
                <div className="flex justify-between items-center text-xs text-gray-500 pt-2 border-t border-blue-200">
                  <span>Total prompt length: {getFinalPrompt().length} characters</span>
                  {userContext.trim() && (
                    <span className="text-green-600">✓ Context added</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Controls */}
      {documents.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Ready to Analyze ({documents.length} document{documents.length !== 1 ? 's' : ''})
              </h3>
              <span className="text-sm text-gray-600">
                {documents.map(doc => doc.file.name).join(', ')}
              </span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={clearAll}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear All
              </button>
              <button
                onClick={handleSubmit}
                disabled={isProcessing || documents.length === 0 || !getFinalPrompt().trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {isProcessing ? 'Analyzing...' : documents.length === 1 ? 'Analyze Document' : `Analyze ${documents.length} Documents`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agent Monitor */}
      {isProcessing && (
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Processing Analysis</h4>
                </div>
              </div>
            </div>
          </div>
          <AgentMonitor isActive={isProcessing} />
        </div>
      )}

      {/* Analysis Results - Side-by-Side Layout */}
      {batchResult && (
        <div className="space-y-6">
          {/* Results Header */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {batchResult.total_documents === 1 ? 'Document Analysis Complete' : 'Multi-Document Analysis Complete'}
                </h3>
                <div className="flex items-center space-x-6 mt-2 text-sm text-gray-600">
                  {batchResult.total_documents > 1 && <span>Total: {batchResult.total_documents} documents</span>}
                  <span className="text-green-600">✓ Completed: {batchResult.completed}</span>
                  {batchResult.failed > 0 && (
                    <span className="text-red-600">✗ Failed: {batchResult.failed}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {/* Layout Toggle Buttons - Only show if multiple documents or not in single doc mode */}
                {documents.length > 1 && (
                  <div className="flex bg-gray-100 rounded-md p-1">
                    <button
                      onClick={() => setLayoutMode('docs-full')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'docs-full' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="Documents Full Width"
                    >
                      📄
                    </button>
                    <button
                      onClick={() => setLayoutMode('split')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'split' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="Side by Side"
                    >
                      ⚖️
                    </button>
                    <button
                      onClick={() => setLayoutMode('analysis-full')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'analysis-full' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="Analysis Full Width"
                    >
                      📊
                    </button>
                  </div>
                )}
                
                {/* Single document layout toggle - simpler version */}
                {documents.length === 1 && (
                  <div className="flex bg-gray-100 rounded-md p-1">
                    <button
                      onClick={() => setLayoutMode('docs-full')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'docs-full' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="View Document"
                    >
                      📄 Document
                    </button>
                    <button
                      onClick={() => setLayoutMode('split')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'split' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="Side by Side View"
                    >
                      ⚖️ Side-by-Side
                    </button>
                    <button
                      onClick={() => setLayoutMode('analysis-full')}
                      className={`px-3 py-1 text-xs rounded ${layoutMode === 'analysis-full' ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                      title="View Analysis"
                    >
                      📊 Analysis
                    </button>
                  </div>
                )}

                {/* Analysis View Toggle */}
                <div className="flex bg-gray-100 rounded-md p-1">
                  <button
                    onClick={() => setShowIssuesList(false)}
                    className={`px-3 py-1 text-xs rounded ${!showIssuesList ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                    title="Full Analysis Text"
                  >
                    📝 Full Text
                  </button>
                  <button
                    onClick={() => setShowIssuesList(true)}
                    className={`px-3 py-1 text-xs rounded ${showIssuesList ? 'bg-white shadow-sm' : 'text-gray-600'}`}
                    title="Structured Issues List"
                  >
                    📋 Issues List
                  </button>
                </div>
                <button
                  onClick={downloadBatchReport}
                  className="px-4 py-2 text-sm text-green-600 hover:bg-green-50 rounded-md border border-green-200 transition-colors"
                >
                  {batchResult.total_documents === 1 ? 'Download Report' : 'Download Analysis Report'}
                </button>
              </div>
            </div>
          </div>

          {/* Side-by-Side Document and Analysis Layout */}
          <div className={`grid gap-6 h-[800px] ${
            layoutMode === 'docs-full' ? 'grid-cols-1' :
            layoutMode === 'analysis-full' ? 'grid-cols-1' :
            'grid-cols-1 lg:grid-cols-2'
          }`}>
            
            {/* Document Tabs Panel */}
            {layoutMode !== 'analysis-full' && (
              <DocumentTabs
                documents={documents}
                activeDocumentId={activeDocumentId}
                onDocumentChange={setActiveDocumentId}
                highlightClause={highlightClause}
                className="h-full"
              />
            )}

            {/* Analysis Results Panel */}
            {layoutMode !== 'docs-full' && (
              <div className="bg-white rounded-lg shadow-md flex flex-col h-full">
                {showIssuesList ? (
                  // Structured Issues List View
                  <ScrollableIssuesList
                    analysis={batchResult.unified_analysis || batchResult.results?.[0]?.analysis || 'Analysis completed successfully.'}
                    documents={documents}
                    onClauseClick={handleClauseClick}
                    className="h-full"
                  />
                ) : (
                  // Full Text Analysis View
                  <>
                    <div className="p-4 border-b border-gray-200 bg-red-50 rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">Legal Analysis Results</h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {batchResult.source_documents && batchResult.source_documents.length > 1
                              ? `Comprehensive analysis across ${batchResult.source_documents.length} documents`
                              : 'Risk assessment and compliance review'
                            }
                          </p>
                        </div>
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ Complete
                        </span>
                      </div>
                      {batchResult.source_documents && batchResult.source_documents.length > 1 && (
                        <div className="mt-2 text-sm text-gray-600">
                          <strong>Source Documents:</strong> {batchResult.source_documents.join(', ')}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 overflow-y-auto p-8">
                      <AnalysisResults
                        analysis={batchResult.unified_analysis || batchResult.results?.[0]?.analysis || 'Analysis completed successfully.'}
                        documents={documents}
                        onDocumentReference={handleDocumentReference}
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* How It Works - only show when no documents and not processing */}
      {documents.length === 0 && !isProcessing && (
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📤</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Upload Documents</h3>
              <p className="text-sm text-gray-600">Upload single documents or batches up to 10 for comprehensive analysis</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">⚙️</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Select Analysis Type</h3>
              <p className="text-sm text-gray-600">Choose from Red Flags Review, Review Against Base, or Negotiation Support</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">AI Agent Analysis</h3>
              <p className="text-sm text-gray-600">Watch our specialized agents analyze your documents in real-time</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📋</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Interactive Results</h3>
              <p className="text-sm text-gray-600">Review findings, navigate clauses, and download comprehensive reports</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}