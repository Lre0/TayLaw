'use client'

import { useState, useEffect, useCallback } from 'react'
import { API_BASE_URL } from '../lib/config'

interface DocumentFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'analyzing' | 'completed' | 'failed'
  analysis?: string
  error?: string
  progress: number
}

interface DocumentTabsProps {
  documents: DocumentFile[]
  activeDocumentId: string | null
  onDocumentChange: (documentId: string) => void
  highlightClause?: string | null
  className?: string
}

interface DocumentContent {
  [documentId: string]: {
    content: string
    loading: boolean
    error: string | null
  }
}

export default function DocumentTabs({ 
  documents, 
  activeDocumentId, 
  onDocumentChange, 
  highlightClause = null,
  className = '' 
}: DocumentTabsProps) {
  const [documentContents, setDocumentContents] = useState<DocumentContent>({})

  // Client-side text cleaning for display (from original DocumentUpload)
  const cleanTextForDisplay = useCallback((text: string): string => {
    if (!text) return ''
    
    let cleaned = text
    
    // Fix any remaining spaced-out words that weren't caught
    cleaned = cleaned.replace(/\b([A-Z])\s+([a-z])\s+([a-z])/g, '$1$2$3')
    
    // Clean up excessive whitespace
    cleaned = cleaned.replace(/\s{3,}/g, '  ')
    cleaned = cleaned.replace(/\n{4,}/g, '\n\n\n')
    
    return cleaned
  }, [])

  const loadDocumentContent = useCallback(async (doc: DocumentFile) => {
    if (documentContents[doc.id]) return // Already loaded or loading

    setDocumentContents(prev => ({
      ...prev,
      [doc.id]: { content: '', loading: true, error: null }
    }))

    try {
      // For text files, read directly
      if (doc.file.type === 'text/plain') {
        const text = await doc.file.text()
        setDocumentContents(prev => ({
          ...prev,
          [doc.id]: { 
            content: cleanTextForDisplay(text), 
            loading: false, 
            error: null 
          }
        }))
      } else {
        // For all other files (PDF, Word, etc.), use backend extraction
        const formData = new FormData()
        formData.append('file', doc.file)

        const response = await fetch(`${API_BASE_URL}/api/extract-text`, {
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
        setDocumentContents(prev => ({
          ...prev,
          [doc.id]: { 
            content: cleanTextForDisplay(extractedText), 
            loading: false, 
            error: null 
          }
        }))
      }
    } catch (err) {
      console.error('Error loading document:', err)
      setDocumentContents(prev => ({
        ...prev,
        [doc.id]: { 
          content: '', 
          loading: false, 
          error: `Error loading document: ${err instanceof Error ? err.message : 'Unknown error'}` 
        }
      }))
    }
  }, [documentContents, cleanTextForDisplay])

  // Load content for active document
  useEffect(() => {
    if (activeDocumentId) {
      const activeDoc = documents.find(doc => doc.id === activeDocumentId)
      if (activeDoc) {
        loadDocumentContent(activeDoc)
      }
    }
  }, [activeDocumentId, documents, loadDocumentContent])

  // Auto-select first document if none selected
  useEffect(() => {
    if (!activeDocumentId && documents.length > 0) {
      onDocumentChange(documents[0].id)
    }
  }, [activeDocumentId, documents, onDocumentChange])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'uploading': return '📤'
      case 'analyzing': return '🔍'
      case 'completed': return '✅'
      case 'failed': return '❌'
      default: return '📄'
    }
  }

  const getStatusColor = (status: string, isActive: boolean) => {
    const baseClasses = 'px-4 py-3 cursor-pointer transition-colors border-b-2 flex items-center space-x-2 min-w-0'
    
    if (isActive) {
      switch (status) {
        case 'completed': return `${baseClasses} bg-green-50 border-green-500 text-green-800`
        case 'failed': return `${baseClasses} bg-red-50 border-red-500 text-red-800`
        case 'analyzing': return `${baseClasses} bg-yellow-50 border-yellow-500 text-yellow-800`
        default: return `${baseClasses} bg-blue-50 border-blue-500 text-blue-800`
      }
    } else {
      return `${baseClasses} bg-gray-50 border-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-800`
    }
  }

  const activeDocument = documents.find(doc => doc.id === activeDocumentId)
  const activeContent = activeDocumentId ? documentContents[activeDocumentId] : null

  const renderDocumentContent = (content: string) => {
    if (!content) return <div className="text-gray-500 italic">No document content available</div>

    return (
      <div className="space-y-3">
        {content.split(/\n\s*\n/).map((section, index) => {
          const lines = section.split('\n').filter(line => line.trim())
          if (lines.length === 0) return null
          
          // Check if this section contains the highlighted clause
          const containsHighlight = highlightClause && 
            section.toLowerCase().includes(highlightClause.toLowerCase())
          
          return (
            <div key={index} className={`mb-4 ${containsHighlight ? 'bg-yellow-100 border-l-4 border-yellow-500 pl-4 py-2 rounded-r animate-pulse' : ''}`}>
              {lines.map((line, lineIndex) => {
                const trimmedLine = line.trim()
                
                // Detect different types of content for styling (from original DocumentUpload)
                const isHeader = trimmedLine.match(/^(ARTICLE|SECTION|CLAUSE)\s+[IVX\d]+/i) ||
                                trimmedLine.match(/^\d+\.\s+[A-Z]/i) ||
                                trimmedLine.match(/^[A-Z\s]{10,}$/i)
                
                const isSubHeader = trimmedLine.match(/^[a-z]\)|^\([a-z]\)|^\d+\.\d+/i)
                
                const isListItem = trimmedLine.match(/^[-•]\s+|^\([a-z]\)|^[a-z]\)/i)
                
                // Check if this specific line contains the highlighted clause
                const lineContainsHighlight = highlightClause && 
                  trimmedLine.toLowerCase().includes(highlightClause.toLowerCase())
                
                return (
                  <div 
                    key={lineIndex} 
                    className={`${
                      isHeader 
                        ? 'text-gray-900 mt-4 mb-2 text-base border-b border-gray-200 pb-1' 
                        : isSubHeader
                        ? 'text-gray-800 mt-3 mb-1 ml-4'
                        : isListItem
                        ? 'text-gray-700 ml-6 mb-1'
                        : 'text-gray-700 mb-1'
                    } ${lineContainsHighlight ? 'bg-yellow-200' : ''}`}
                  >
                    {trimmedLine || '\u00A0'}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-md flex flex-col ${className}`}>
        <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <h3 className="text-lg font-semibold text-gray-900">Documents</h3>
          <p className="text-sm text-gray-600 mt-1">No documents uploaded</p>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>Upload documents to view them here</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-md flex flex-col ${className}`}>
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="px-4 py-2">
          <h3 className="text-lg font-semibold text-gray-900">Source Documents ({documents.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <div className="flex min-w-max">
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => onDocumentChange(doc.id)}
                className={getStatusColor(doc.status, doc.id === activeDocumentId)}
              >
                <span className="text-lg">{getStatusIcon(doc.status)}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate" title={doc.file.name}>
                    {doc.file.name}
                  </div>
                  <div className="text-xs opacity-75 capitalize">
                    {doc.status} • {(doc.file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Document Content */}
      <div className="flex-1 overflow-hidden">
        {activeDocument ? (
          activeContent?.loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading document content...</p>
              </div>
            </div>
          ) : activeContent?.error ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center text-red-600">
                <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="font-medium">Unable to display document</p>
                <p className="text-sm mt-2">{activeContent.error}</p>
              </div>
            </div>
          ) : (
            <div className="h-full overflow-y-auto p-8">
              <div className="bg-gray-50 rounded-lg p-6 h-full">
                <div className="bg-white rounded border p-6 h-full shadow-sm">
                  <div className="text-sm leading-relaxed text-gray-800 h-full overflow-y-auto">
                    {renderDocumentContent(activeContent?.content || '')}
                  </div>
                </div>
              </div>
            </div>
          )
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>Select a document to view its content</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}