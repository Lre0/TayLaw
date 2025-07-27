'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import AgentMonitor from './AgentMonitor'

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
  results: Array<{
    filename: string
    status: 'completed' | 'failed'
    analysis?: string
    error?: string
  }>
}

export default function MultiDocumentUpload() {
  const [documents, setDocuments] = useState<DocumentFile[]>([])
  const [prompt, setPrompt] = useState('Please perform a comprehensive red flags review on this contract, identifying potential legal risks, compliance issues, and problematic clauses.')
  const [isProcessing, setIsProcessing] = useState(false)
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null)
  const [currentBatchId, setCurrentBatchId] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [realTimeProgress, setRealTimeProgress] = useState<Record<string, number>>({})

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
          // Fetch final results
          const resultsResponse = await fetch(`http://localhost:8000/api/batch-results/${batchId}`)
          if (resultsResponse.ok) {
            const results = await resultsResponse.json()
            setBatchResult(results)
            setIsProcessing(false)
            setCurrentBatchId(null)
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

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleSubmit = async () => {
    if (documents.length === 0 || !prompt) return

    setIsProcessing(true)
    setBatchResult(null)

    // Update all documents to uploading status
    setDocuments(prev => prev.map(doc => ({ ...doc, status: 'uploading' as const, progress: 10 })))

    try {
      const formData = new FormData()
      documents.forEach(doc => formData.append('files', doc.file))
      formData.append('prompt', prompt)

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
          const shouldContinue = await pollBatchStatus(result.batch_id!)
          if (!shouldContinue) {
            clearInterval(pollInterval)
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
        setDocuments(prev => prev.map(doc => {
          const analysis = result.results.find(r => r.filename === doc.file.name)
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

    const reportContent = `BATCH ANALYSIS REPORT
======================

Batch ID: ${batchResult.batch_id}
Total Documents: ${batchResult.total_documents}
Completed Successfully: ${batchResult.completed}
Failed: ${batchResult.failed}

INDIVIDUAL DOCUMENT ANALYSES:
${batchResult.results.map((result, index) => `
${index + 1}. ${result.filename}
Status: ${result.status.toUpperCase()}
${result.status === 'completed' ? result.analysis : `Error: ${result.error}`}

${'='.repeat(80)}
`).join('')}
`

    const blob = new Blob([reportContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch_analysis_report_${batchResult.batch_id.slice(0, 8)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
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

        {/* Analysis Instructions */}
        <div className="mt-6">
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
            Analysis Instructions
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
            placeholder="Specify what type of analysis you want performed on all documents..."
          />
        </div>
      </div>

      {/* Document List */}
      {documents.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Documents ({documents.length})
            </h3>
            <div className="flex space-x-2">
              <button
                onClick={clearAll}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear All
              </button>
              <button
                onClick={handleSubmit}
                disabled={isProcessing || documents.length === 0 || !prompt}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {isProcessing ? 'Analyzing...' : documents.length === 1 ? 'Analyze Document' : `Analyze ${documents.length} Documents`}
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">{getStatusIcon(doc.status)}</div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{doc.file.name}</h4>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          <span>{formatFileSize(doc.file.size)}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                            {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    {doc.status !== 'pending' && (
                      <div className="mt-3">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              doc.status === 'completed' ? 'bg-green-500' : 
                              doc.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                            }`}
                            style={{ width: `${doc.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Error Display */}
                    {doc.error && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        {doc.error}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => removeDocument(doc.id)}
                    className="ml-4 text-gray-400 hover:text-red-600"
                    disabled={isProcessing}
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Monitor */}
      {isProcessing && (
        <div className="mb-6">
          <AgentMonitor isActive={isProcessing} />
        </div>
      )}

      {/* Batch Results */}
      {batchResult && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                {batchResult.total_documents === 1 ? 'Document Analysis Complete' : 'Batch Analysis Complete'}
              </h3>
              <div className="flex items-center space-x-6 mt-2 text-sm text-gray-600">
                {batchResult.total_documents > 1 && <span>Total: {batchResult.total_documents}</span>}
                <span className="text-green-600">✓ Completed: {batchResult.completed}</span>
                {batchResult.failed > 0 && (
                  <span className="text-red-600">✗ Failed: {batchResult.failed}</span>
                )}
              </div>
            </div>
            <button
              onClick={downloadBatchReport}
              className="px-4 py-2 text-sm text-green-600 hover:bg-green-50 rounded-md border border-green-200 transition-colors"
            >
              {batchResult.total_documents === 1 ? 'Download Report' : 'Download Batch Report'}
            </button>
          </div>

          <div className="space-y-6">
            {batchResult.results.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{result.filename}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      result.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {result.status === 'completed' ? '✓ Complete' : '✗ Failed'}
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  {result.status === 'completed' ? (
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                        {result.analysis}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-red-700 bg-red-50 p-3 rounded">
                      <strong>Error:</strong> {result.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
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
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Upload Documents</h3>
              <p className="text-sm text-gray-600">Upload single documents or batches up to 10 for comprehensive analysis</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">AI Agent Analysis</h3>
              <p className="text-sm text-gray-600">Watch our specialized agents analyze your documents in real-time</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🔍</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Risk Identification</h3>
              <p className="text-sm text-gray-600">Identify legal risks, compliance issues, and problematic clauses</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Detailed Report</h3>
              <p className="text-sm text-gray-600">Receive comprehensive analysis with categorized findings</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}