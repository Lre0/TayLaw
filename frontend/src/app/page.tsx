'use client'

import MultiDocumentUpload from '@/components/MultiDocumentUpload'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-6 max-w-[98vw]">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            TayLaw
          </h1>
        </div>
        
        <MultiDocumentUpload />
      </div>
    </main>
  )
}
