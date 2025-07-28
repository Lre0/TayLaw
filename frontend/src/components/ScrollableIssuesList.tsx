'use client'

import { useState, useCallback } from 'react'

interface Issue {
  id: string
  title: string
  description: string
  severity: 'high' | 'medium' | 'low'
  clause: string
  documentName?: string
  lineNumber?: number
  recommendation?: string
}

interface ScrollableIssuesListProps {
  analysis: string
  documents: Array<{
    id: string
    file: File
    status: string
  }>
  onClauseClick: (documentId: string, clause: string, lineNumber?: number) => void
  className?: string
}

export default function ScrollableIssuesList({ 
  analysis, 
  documents, 
  onClauseClick, 
  className = '' 
}: ScrollableIssuesListProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set())

  // Parse analysis text into structured issues
  const parseIssuesFromAnalysis = useCallback((text: string): Issue[] => {
    if (!text) return []

    const issues: Issue[] = []
    
    // Split analysis into sections that might represent individual issues
    const sections = text.split(/\n\s*(?=\d+\.|•|-)/).filter(section => section.trim())
    
    sections.forEach((section, index) => {
      const lines = section.split('\n').map(line => line.trim()).filter(line => line)
      if (lines.length === 0) return

      // Extract issue details
      const firstLine = lines[0]
      const restOfContent = lines.slice(1).join(' ')

      // Determine severity based on keywords
      const getSeverity = (content: string): 'high' | 'medium' | 'low' => {
        const highKeywords = ['critical', 'urgent', 'severe', 'major', 'high risk', 'dangerous', 'liability', 'terminate']
        const mediumKeywords = ['moderate', 'medium', 'concern', 'issue', 'problem', 'review']
        
        const lowerContent = content.toLowerCase()
        if (highKeywords.some(keyword => lowerContent.includes(keyword))) return 'high'
        if (mediumKeywords.some(keyword => lowerContent.includes(keyword))) return 'medium'
        return 'low'
      }

      // Extract clause reference
      const clauseMatch = section.match(/(?:clause|section|article|paragraph)\s*[:\-]?\s*([^.\n]+)/i)
      const documentMatch = section.match(/(?:in|from|document:?)\s*([^\s,.\n]+\.(pdf|docx?|txt))/i)

      // Clean up title by removing all leading numbers, bullets, and extra whitespace
      let cleanTitle = firstLine
        .replace(/^\d+\.\s*/, '') // Remove first number
        .replace(/^\d+\.\s*/, '') // Remove second number if it exists  
        .replace(/^[•\-]\s*/, '') // Remove bullets
        .replace(/^\s+/, '') // Remove leading whitespace
        .trim()

      // If title is still empty or very short, use a portion of the content
      if (cleanTitle.length < 3 && restOfContent) {
        cleanTitle = restOfContent.substring(0, 50).trim()
      }

      issues.push({
        id: `issue-${index}`,
        title: cleanTitle.substring(0, 100) + (cleanTitle.length > 100 ? '...' : ''),
        description: restOfContent || firstLine,
        severity: getSeverity(section),
        clause: clauseMatch ? clauseMatch[1].trim() : 'General',
        documentName: documentMatch ? documentMatch[1] : undefined,
        recommendation: section.includes('recommend') ? section.split(/recommend[s]?:?\s*/i)[1]?.split('.')[0] : undefined
      })
    })

    return issues
  }, [])

  const issues = parseIssuesFromAnalysis(analysis)

  const toggleIssueExpansion = (issueId: string) => {
    setExpandedIssues(prev => {
      const newSet = new Set(prev)
      if (newSet.has(issueId)) {
        newSet.delete(issueId)
      } else {
        newSet.add(issueId)
      }
      return newSet
    })
  }

  const handleClauseClick = (issue: Issue) => {
    // Find the document by name
    let targetDocumentId = documents[0]?.id // Default to first document
    
    if (issue.documentName) {
      const matchedDoc = documents.find(doc => 
        doc.file.name.toLowerCase().includes(issue.documentName!.toLowerCase()) ||
        issue.documentName!.toLowerCase().includes(doc.file.name.toLowerCase().replace(/\.[^/.]+$/, ""))
      )
      if (matchedDoc) {
        targetDocumentId = matchedDoc.id
      }
    }

    onClauseClick(targetDocumentId, issue.clause, issue.lineNumber)
  }

  const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
    }
  }

  const getSeverityIcon = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return '🚨'
      case 'medium': return '⚠️'
      case 'low': return 'ℹ️'
    }
  }

  if (issues.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No structured issues found in analysis</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-md flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-red-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-semibold text-gray-900">Legal Issues Found</h4>
            <p className="text-sm text-gray-600 mt-1">
              {issues.length} issue{issues.length !== 1 ? 's' : ''} identified • Click any issue to view relevant clause
            </p>
          </div>
          <div className="flex space-x-2">
            <div className="flex items-center space-x-1 text-xs">
              <span className="w-3 h-3 bg-red-500 rounded-full"></span>
              <span className="text-gray-600">{issues.filter(i => i.severity === 'high').length} High</span>
            </div>
            <div className="flex items-center space-x-1 text-xs">
              <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
              <span className="text-gray-600">{issues.filter(i => i.severity === 'medium').length} Medium</span>
            </div>
            <div className="flex items-center space-x-1 text-xs">
              <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
              <span className="text-gray-600">{issues.filter(i => i.severity === 'low').length} Low</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Issues List */}
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-gray-100">
          {issues.map((issue, index) => (
            <div key={issue.id} className="p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start space-x-3">
                {/* Severity Indicator */}
                <div className="flex-shrink-0 pt-1">
                  <span className="text-lg">{getSeverityIcon(issue.severity)}</span>
                </div>

                {/* Issue Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className="text-sm font-medium text-gray-900 mb-1">
                        {issue.title}
                      </h5>
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(issue.severity)}`}>
                          {issue.severity.toUpperCase()} RISK
                        </span>
                        <button
                          onClick={() => handleClauseClick(issue)}
                          className="text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded border border-blue-200 transition-colors"
                        >
                          📄 View Clause: {issue.clause}
                        </button>
                        {issue.documentName && (
                          <span className="text-xs text-gray-500">
                            in {issue.documentName}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Expand/Collapse Button */}
                    <button
                      onClick={() => toggleIssueExpansion(issue.id)}
                      className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <svg 
                        className={`w-4 h-4 transition-transform ${expandedIssues.has(issue.id) ? 'rotate-180' : ''}`} 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>

                  {/* Expanded Content */}
                  {expandedIssues.has(issue.id) && (
                    <div className="mt-3 pl-4 border-l-2 border-gray-200">
                      <div className="text-sm text-gray-700 leading-relaxed mb-3">
                        {issue.description}
                      </div>
                      {issue.recommendation && (
                        <div className="bg-blue-50 border border-blue-200 rounded p-3">
                          <h6 className="text-xs font-medium text-blue-900 mb-1">RECOMMENDATION:</h6>
                          <p className="text-sm text-blue-800">{issue.recommendation}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {issues.filter(i => i.severity === 'high').length > 0 && (
              <span className="text-red-600 font-medium">
                ⚠️ {issues.filter(i => i.severity === 'high').length} high-risk issue{issues.filter(i => i.severity === 'high').length !== 1 ? 's' : ''} require immediate attention
              </span>
            )}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setExpandedIssues(new Set(issues.map(i => i.id)))}
              className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded border border-gray-300 hover:bg-white transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={() => setExpandedIssues(new Set())}
              className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded border border-gray-300 hover:bg-white transition-colors"
            >
              Collapse All
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}