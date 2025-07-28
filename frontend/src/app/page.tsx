'use client'

import MultiDocumentUpload from '@/components/MultiDocumentUpload'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-6 max-w-[98vw]">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            TayLaw - Legal AI Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI-powered legal document analysis with full transparency into agent decision-making. 
            Upload one or more contracts for comprehensive red flags review and risk assessment.
          </p>
        </div>
        
        <MultiDocumentUpload />
      </div>
    </main>
  )
}
