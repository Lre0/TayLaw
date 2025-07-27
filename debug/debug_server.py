#!/usr/bin/env python3
"""
Debug server to identify endpoint registration issues
"""
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    print("Importing FastAPI components...")
    from fastapi import FastAPI, File, UploadFile, Form
    print("✅ FastAPI imported")
    
    print("Importing orchestrators...")
    from backend.agents.multi_document_orchestrator import MultiDocumentOrchestrator
    print("✅ MultiDocumentOrchestrator imported")
    
    print("Creating app...")
    app = FastAPI(title="Debug Legal AI Assistant API")
    
    print("Creating orchestrator...")
    multi_document_orchestrator = MultiDocumentOrchestrator(max_concurrent_documents=5)
    print("✅ MultiDocumentOrchestrator created")
    
    print("Registering routes...")
    
    @app.get("/")
    async def root():
        return {"message": "Debug Legal AI Assistant API"}
    
    @app.post("/api/analyze-multiple")
    async def analyze_multiple_documents(
        files: list[UploadFile] = File(...),
        prompt: str = Form(...)
    ):
        """Debug version of analyze multiple documents"""
        try:
            print(f"Received {len(files)} files for analysis")
            
            # Prepare files data
            files_data = []
            for i, file in enumerate(files):
                file_content = await file.read()
                filename = file.filename or f"document_{i+1}.txt"
                files_data.append({
                    'filename': filename,
                    'file_content': file_content
                })
            
            print(f"Files prepared: {[f['filename'] for f in files_data]}")
            
            # Simple mock response for debugging
            return {
                "batch_id": "debug-batch-123",
                "total_documents": len(files),
                "completed": len(files),
                "failed": 0,
                "results": [
                    {
                        "filename": file_data['filename'],
                        "status": "completed",
                        "analysis": f"Debug analysis for {file_data['filename']}: This is a mock analysis result for debugging purposes.",
                        "error": None
                    }
                    for file_data in files_data
                ]
            }
        except Exception as e:
            print(f"Error in analyze_multiple_documents: {e}")
            return {"error": str(e)}
    
    print("✅ Routes registered")
    
    if __name__ == "__main__":
        import uvicorn
        print("Starting debug server on port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001)
        
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()