'use client'

import { useState, useEffect, useCallback } from 'react'
import { API_BASE_URL } from '../lib/config'

interface DocumentViewerProps {
  file: File | null
  isOpen: boolean
  onClose: () => void
}

export default function DocumentViewer({ file, isOpen, onClose }: DocumentViewerProps) {
  const [documentContent, setDocumentContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const loadDocumentContent = useCallback(async () => {
    if (!file) return

    setLoading(true)
    setError('')

    try {
      // For text files, read directly
      if (file.type === 'text/plain') {
        const text = await file.text()
        setDocumentContent(text)
      } else {
        // For all other files (PDF, Word, etc.), use backend extraction
        const formData = new FormData()
        formData.append('file', file)

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

        setDocumentContent(result.text || 'No text content could be extracted from this document.')
      }
    } catch (err) {
      setError(`Unable to display document content: ${err instanceof Error ? err.message : 'Unknown error'}`)
      console.error('Error loading document:', err)
    } finally {
      setLoading(false)
    }
  }, [file])

  useEffect(() => {
    if (isOpen && file) {
      loadDocumentContent()
    }
  }, [isOpen, file, loadDocumentContent])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
      <div className="relative h-full flex">
        <div className="ml-auto h-full w-full max-w-4xl bg-white shadow-xl">
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Document Viewer</h2>
                <p className="text-sm text-gray-600">{file?.name}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
              {loading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading document...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-red-600">
                    <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <p className="font-medium">Unable to display document</p>
                    <p className="text-sm mt-2">{error}</p>
                  </div>
                </div>
              ) : (
                <div className="h-full overflow-auto p-6">
                  <div className="bg-gray-50 rounded-lg p-6 min-h-full">
                    <div className="bg-white rounded border p-6 shadow-sm">
                      <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed text-gray-800">
                        {documentContent || 'No content to display'}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <div>
                  File size: {file ? (file.size / 1024).toFixed(1) : 0} KB
                </div>
                <div className="flex space-x-4">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    onClick={() => {
                      if (file) {
                        const url = URL.createObjectURL(file)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = file.name
                        a.click()
                        URL.revokeObjectURL(url)
                      }
                    }}
                  >
                    Download
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}