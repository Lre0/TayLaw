#!/usr/bin/env python3
"""
Simplified backend to test multi-document upload functionality
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json

app = FastAPI(title="Simple Legal AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Simple Legal AI Assistant API"}

@app.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """Single document analysis endpoint"""
    try:
        file_content = await file.read()
        filename = file.filename or "document.txt"
        
        # Simple mock analysis
        analysis = f"""LEGAL DOCUMENT ANALYSIS - {filename}

SUMMARY:
This is a simplified analysis for testing purposes.

RED FLAGS IDENTIFIED:
1. Test Risk Item 1: Standard contract language
2. Test Risk Item 2: Typical commercial terms
3. Test Risk Item 3: Sample regulatory compliance

RECOMMENDATIONS:
- Review standard clauses
- Consider legal consultation
- Verify compliance requirements

ANALYSIS COMPLETED: {len(file_content)} bytes processed
PROMPT USED: {prompt}
"""
        
        return JSONResponse(content={"analysis": analysis})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/analyze-multiple")
async def analyze_multiple_documents(
    files: list[UploadFile] = File(...),
    prompt: str = Form(...)
):
    """Multi-document analysis endpoint"""
    try:
        print(f"Received {len(files)} files for analysis")
        
        if len(files) > 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Maximum 10 documents allowed per batch"}
            )
        
        results = []
        for i, file in enumerate(files):
            try:
                file_content = await file.read()
                filename = file.filename or f"document_{i+1}.txt"
                
                print(f"Processing {filename}: {len(file_content)} bytes")
                
                # Simple mock analysis for each file
                analysis = f"""LEGAL DOCUMENT ANALYSIS - {filename}

SUMMARY:
Document {i+1} of {len(files)} in batch analysis.

RED FLAGS IDENTIFIED:
1. Test Risk Item A: Contract structure review needed
2. Test Risk Item B: Standard commercial terms present
3. Test Risk Item C: Compliance verification required

RECOMMENDATIONS:
- Detailed legal review recommended
- Cross-reference with other documents in batch
- Ensure consistency across all documents

DOCUMENT STATS:
- Size: {len(file_content)} bytes
- Position in batch: {i+1}/{len(files)}
- Analysis prompt: {prompt[:100]}...
"""
                
                results.append({
                    "filename": filename,
                    "status": "completed", 
                    "analysis": analysis,
                    "error": None
                })
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                results.append({
                    "filename": filename,
                    "status": "failed",
                    "analysis": None,
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "batch_id": f"simple-batch-{len(files)}-files",
            "total_documents": len(files),
            "completed": len([r for r in results if r["status"] == "completed"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        })
    
    except Exception as e:
        print(f"Error in analyze_multiple_documents: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/extract-text")
async def extract_document_text(file: UploadFile = File(...)):
    """Extract text from uploaded document for viewing"""
    try:
        file_content = await file.read()
        
        # Simple text extraction (just return the content as text)
        if file.content_type == "text/plain":
            text = file_content.decode('utf-8', errors='ignore')
        else:
            # For other file types, return a placeholder
            text = f"[Binary file content - {len(file_content)} bytes]\n\nThis is a simplified backend for testing. In the full version, this would extract text from PDF, Word, etc."
        
        return JSONResponse(content={
            "text": text,
            "filename": file.filename,
            "word_count": len(text.split()),
            "char_count": len(text)
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract text: {str(e)}"}
        )

@app.get("/api/agent-status")
async def get_agent_status():
    """Get current agent status"""
    return JSONResponse(content={
        "status": "active",
        "agents": {
            "document_processor": "ready",
            "risk_analyzer": "ready", 
            "orchestrator": "ready"
        },
        "message": "Simple backend - all agents ready"
    })

@app.get("/api/agent-history")
async def get_agent_history(limit: int = 50):
    """Get agent activity history"""
    return JSONResponse(content={
        "activities": [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "agent": "Simple Backend",
                "action": "Ready for document analysis",
                "status": "success"
            }
        ],
        "total": 1
    })

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Legal AI Assistant API on port 8002...")
    print("This is a simplified backend for testing multi-document upload.")
    print("Access at: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)