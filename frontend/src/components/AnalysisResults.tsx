'use client'

import { useCallback } from 'react'

interface AnalysisResultsProps {
  analysis: string
  documents: Array<{
    id: string
    file: File
    status: string
  }>
  onDocumentReference: (documentName: string) => void
  className?: string
}

export default function AnalysisResults({ 
  analysis, 
  documents, 
  onDocumentReference, 
  className = '' 
}: AnalysisResultsProps) {
  
  const parseAnalysisWithReferences = useCallback((text: string) => {
    if (!text) return [{ type: 'text', content: text }]

    // Enhanced regex patterns to match document references
    const patterns = [
      /\[Document:\s*([^\]]+)\]/gi, // [Document: filename.pdf]
      /\(Document:\s*([^)]+)\)/gi,  // (Document: filename.pdf)
      /\bDocument:\s*"([^"]+)"/gi,  // Document: "filename.pdf"
      /\bDocument:\s*([^\s,.\n]+\.(pdf|docx?|txt))/gi, // Document: filename.pdf
      /\bin\s+([^\s,.\n]+\.(pdf|docx?|txt))\b/gi, // in filename.pdf
      /\bfrom\s+([^\s,.\n]+\.(pdf|docx?|txt))\b/gi, // from filename.pdf
    ]

    let parts: Array<{ type: string; content: string; documentName?: string }> = [{ type: 'text', content: text }]

    // Apply each pattern to find and mark document references
    patterns.forEach(pattern => {
      const newParts: Array<{ type: string; content: string; documentName?: string }> = []
      
      parts.forEach(part => {
        if (part.type !== 'text') {
          newParts.push(part)
          return
        }

        let lastIndex = 0
        let match

        while ((match = pattern.exec(part.content)) !== null) {
          // Add text before the match
          if (match.index > lastIndex) {
            newParts.push({
              type: 'text',
              content: part.content.slice(lastIndex, match.index)
            })
          }

          // Add the document reference
          const documentName = match[1]
          newParts.push({
            type: 'document-reference',
            content: match[0],
            documentName: documentName
          })

          lastIndex = match.index + match[0].length
        }

        // Add remaining text
        if (lastIndex < part.content.length) {
          newParts.push({
            type: 'text',
            content: part.content.slice(lastIndex)
          })
        }

        // Reset regex for next iteration
        pattern.lastIndex = 0
      })

      parts = newParts
    })

    return parts
  }, [])

  const handleDocumentClick = useCallback((documentName: string) => {
    // Find the document by name (case-insensitive)
    const matchedDoc = documents.find(doc => 
      doc.file.name.toLowerCase() === documentName.toLowerCase() ||
      doc.file.name.toLowerCase().includes(documentName.toLowerCase()) ||
      documentName.toLowerCase().includes(doc.file.name.toLowerCase().replace(/\.[^/.]+$/, ""))
    )

    if (matchedDoc) {
      onDocumentReference(matchedDoc.id)
    } else {
      console.warn(`Could not find document matching: ${documentName}`)
    }
  }, [documents, onDocumentReference])

  const renderParsedAnalysis = () => {
    const parts = parseAnalysisWithReferences(analysis)
    
    return parts.map((part, index) => {
      if (part.type === 'document-reference') {
        return (
          <button
            key={index}
            onClick={() => handleDocumentClick(part.documentName!)}
            className="inline text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-1 py-0.5 rounded transition-colors font-medium cursor-pointer border-b border-blue-300 hover:border-blue-500"
            title={`Click to view ${part.documentName}`}
          >
            {part.content}
          </button>
        )
      }
      
      return (
        <span key={index}>
          {part.content}
        </span>
      )
    })
  }

  return (
    <div className={`prose prose-sm max-w-none h-full ${className}`}>
      <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
        {renderParsedAnalysis()}
      </div>
    </div>
  )
}