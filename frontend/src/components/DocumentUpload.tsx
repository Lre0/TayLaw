'use client'

import { useState } from 'react'
import AgentMonitor from './AgentMonitor'

export default function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [prompt, setPrompt] = useState('Please perform a comprehensive red flags review on this contract, identifying potential legal risks, compliance issues, and problematic clauses.')
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [documentContent, setDocumentContent] = useState<string>('')
  const [loadingDocument, setLoadingDocument] = useState(false)

  // Client-side text cleaning for display
  const cleanTextForDisplay = (text: string): string => {
    if (!text) return ''
    
    // Additional client-side cleaning for any remaining issues
    let cleaned = text
    
    // Fix any remaining spaced-out words that weren't caught
    cleaned = cleaned.replace(/\b([A-Z])\s+([a-z])\s+([a-z])/g, '$1$2$3')
    
    // Clean up excessive whitespace
    cleaned = cleaned.replace(/\s{3,}/g, '  ')
    cleaned = cleaned.replace(/\n{4,}/g, '\n\n\n')
    
    return cleaned
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      // Reset previous content
      setDocumentContent('')
      setAnalysis(null)
    }
  }

  const loadDocumentContent = async (uploadedFile: File) => {
    setLoadingDocument(true)
    try {
      // For text files, read directly
      if (uploadedFile.type === 'text/plain') {
        const text = await uploadedFile.text()
        setDocumentContent(cleanTextForDisplay(text))
      } else {
        // For all other files (PDF, Word, etc.), use backend extraction
        const formData = new FormData()
        formData.append('file', uploadedFile)

        const response = await fetch('http://localhost:8000/api/extract-text', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`Failed to extract text: ${response.statusText}`)
        }

        const result = await response.json()
        
        if (result.error) {
          throw new Error(result.error)
        }

        const extractedText = result.text || 'No text content could be extracted from this document.'
        setDocumentContent(cleanTextForDisplay(extractedText))
      }
    } catch (err) {
      console.error('Error loading document:', err)
      setDocumentContent(`Error loading document: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoadingDocument(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !prompt) return

    setLoading(true)
    setAnalysis(null) // Clear previous results
    
    // Load document content for side-by-side view
    await loadDocumentContent(file)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('prompt', prompt)

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      })
      
      const result = await response.json()
      setAnalysis(result.analysis)
    } catch (error) {
      console.error('Error:', error)
      setAnalysis('Error occurred during analysis. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-[90rem] mx-auto px-4">
      {/* Upload Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Legal Document Analysis</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
              Upload Document (PDF, Word, or Text)
            </label>
            <input
              type="file"
              id="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {file && (
              <div className="mt-2 text-sm text-gray-600">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>
          
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Analysis Instructions
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>
          
          <button
            type="submit"
            disabled={!file || !prompt || loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Analyzing Document...' : 'Start Legal Analysis'}
          </button>
        </form>
      </div>

      {/* Agent Monitor - shows during and after analysis */}
      {(loading || analysis) && (
        <div className="mb-6">
          <AgentMonitor isActive={loading || !!analysis} />
        </div>
      )}

      {/* Side-by-Side Results Display */}
      {analysis && (
        <div className="space-y-6">
          {/* Document Info Header */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Analysis Complete: {file?.name}</h3>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                  <span>File Size: {file ? (file.size / 1024).toFixed(1) : 0} KB</span>
                  <span>Type: Red Flags Review</span>
                  <span className="text-green-600 font-medium">✓ Complete</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <button 
                  onClick={() => {
                    if (analysis) {
                      const blob = new Blob([analysis], { type: 'text/plain' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `${file?.name || 'document'}_analysis_report.txt`
                      a.click()
                      URL.revokeObjectURL(url)
                    }
                  }}
                  className="px-4 py-2 text-sm text-green-600 hover:bg-green-50 rounded-md border border-green-200 transition-colors"
                >
                  Export Report
                </button>
                <button className="px-4 py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-md border border-purple-200 transition-colors">
                  Compare with Template
                </button>
              </div>
            </div>
          </div>

          {/* Side-by-Side Document and Analysis */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-[700px]">
            {/* Original Document Panel */}
            <div className="bg-white rounded-lg shadow-md flex flex-col">
              <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                <h3 className="text-lg font-semibold text-gray-900">Original Document</h3>
                <p className="text-sm text-gray-600 mt-1">{file?.name}</p>
              </div>
              <div className="flex-1 overflow-hidden">
                {loadingDocument ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <p className="text-gray-600">Loading document content...</p>
                    </div>
                  </div>
                ) : (
                  <div className="h-full overflow-y-auto p-8">
                    <div className="bg-gray-50 rounded-lg p-6 h-full">
                      <div className="bg-white rounded border p-6 h-full shadow-sm">
                        <div className="text-sm leading-relaxed text-gray-800 h-full overflow-y-auto">
                          {documentContent ? (
                            <div className="space-y-3">
                              {documentContent.split(/\n\s*\n/).map((section, index) => {
                                const lines = section.split('\n').filter(line => line.trim())
                                if (lines.length === 0) return null
                                
                                return (
                                  <div key={index} className="mb-4">
                                    {lines.map((line, lineIndex) => {
                                      const trimmedLine = line.trim()
                                      
                                      // Detect different types of content for styling
                                      const isHeader = trimmedLine.match(/^(ARTICLE|SECTION|CLAUSE)\s+[IVX\d]+/i) ||
                                                      trimmedLine.match(/^\d+\.\s+[A-Z]/i) ||
                                                      trimmedLine.match(/^[A-Z\s]{10,}$/i)
                                      
                                      const isSubHeader = trimmedLine.match(/^[a-z]\)|^\([a-z]\)|^\d+\.\d+/i)
                                      
                                      const isListItem = trimmedLine.match(/^[-•]\s+|^\([a-z]\)|^[a-z]\)/i)
                                      
                                      return (
                                        <div 
                                          key={lineIndex} 
                                          className={`${
                                            isHeader 
                                              ? 'font-bold text-gray-900 mt-4 mb-2 text-base border-b border-gray-200 pb-1' 
                                              : isSubHeader
                                              ? 'font-semibold text-gray-800 mt-3 mb-1 ml-4'
                                              : isListItem
                                              ? 'text-gray-700 ml-6 mb-1'
                                              : 'text-gray-700 mb-1'
                                          }`}
                                        >
                                          {trimmedLine || '\u00A0'}
                                        </div>
                                      )
                                    })}
                                  </div>
                                )
                              })}
                            </div>
                          ) : (
                            <div className="text-gray-500 italic">No document content available</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Analysis Results Panel */}
            <div className="bg-white rounded-lg shadow-md flex flex-col">
              <div className="p-4 border-b border-gray-200 bg-red-50 rounded-t-lg">
                <h3 className="text-lg font-semibold text-gray-900">Legal Analysis Results</h3>
                <p className="text-sm text-gray-600 mt-1">Risk assessment and compliance review</p>
              </div>
              <div className="flex-1 overflow-y-auto p-8">
                <div className="prose prose-sm max-w-none h-full">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                    {analysis}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* How It Works Section - only show when no analysis results */}
      {!analysis && !loading && (
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Upload Document</h3>
              <p className="text-sm text-gray-600">Upload your legal document in PDF, Word, or text format</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">AI Agent Analysis</h3>
              <p className="text-sm text-gray-600">Watch our specialized agents analyze your document in real-time</p>
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
              <p className="text-sm text-gray-600">Receive a comprehensive analysis with categorized findings</p>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}