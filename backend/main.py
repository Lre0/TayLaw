from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import io
import os
from dotenv import load_dotenv
from agents.document_processor import DocumentProcessor
from agents.risk_analyzer import RiskAnalyzer
from agents.orchestrator import Orchestrator
from agents.langgraph_orchestrator import LangGraphOrchestrator
from agents.multi_document_orchestrator import MultiDocumentOrchestrator
from agents.agent_monitor import agent_monitor

load_dotenv()

app = FastAPI(title="Legal AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use LangGraph orchestrator for enhanced workflow management
langgraph_orchestrator = LangGraphOrchestrator()
multi_document_orchestrator = MultiDocumentOrchestrator(max_concurrent_documents=5)
fallback_orchestrator = Orchestrator()

@app.get("/")
async def root():
    return {"message": "Legal AI Assistant API"}

@app.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    try:
        file_content = await file.read()
        
        # Ensure filename is not None
        filename = file.filename or "document.txt"
        print(f"Processing file: {filename} ({len(file_content)} bytes)")
        
        # Use LangGraph orchestrator for enhanced agent visibility
        result = await langgraph_orchestrator.process_document(
            file_content=file_content,
            filename=filename,
            prompt=prompt
        )
        
        return JSONResponse(content={"analysis": result})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.websocket("/ws/agent-monitor")
async def websocket_agent_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time agent monitoring"""
    await websocket.accept()
    
    # Create a queue for this WebSocket connection
    queue = asyncio.Queue()
    agent_monitor.subscribe(queue)
    
    try:
        # Send current status immediately
        current_status = agent_monitor.get_current_status()
        await websocket.send_text(json.dumps({
            "type": "status",
            "data": current_status
        }))
        
        # Send recent activity history
        history = agent_monitor.get_activity_history()
        await websocket.send_text(json.dumps({
            "type": "history",
            "data": history
        }))
        
        # Listen for real-time updates
        while True:
            try:
                # Wait for new activity updates
                activity_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(json.dumps(activity_data))
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "data": {"timestamp": agent_monitor.get_current_status()}
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        agent_monitor.unsubscribe(queue)

@app.get("/api/agent-status")
async def get_agent_status():
    """Get current agent status (HTTP fallback)"""
    return JSONResponse(content=agent_monitor.get_current_status())

@app.get("/api/agent-history")
async def get_agent_history(limit: int = 50):
    """Get agent activity history (HTTP fallback)"""
    return JSONResponse(content=agent_monitor.get_activity_history(limit))

@app.post("/api/analyze-multiple")
async def analyze_multiple_documents(
    files: list[UploadFile] = File(...),
    prompt: str = Form(...)
):
    """Analyze multiple documents using the multi-document orchestrator"""
    try:
        if len(files) > 10:  # Security limit
            return JSONResponse(
                status_code=400,
                content={"error": "Maximum 10 documents allowed per batch"}
            )
        
        # Validate file types
        allowed_types = {'.pdf', '.doc', '.docx', '.txt'}
        for file in files:
            if file.filename:
                file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
                if file_ext not in allowed_types:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"File type {file_ext} not allowed. Supported: PDF, Word, Text"}
                    )
        
        print(f"Processing batch with {len(files)} documents")
        
        # Prepare files data for multi-document orchestrator
        files_data = []
        for i, file in enumerate(files):
            file_content = await file.read()
            filename = file.filename or f"document_{i+1}.txt"
            
            # File size validation (max 10MB per file)
            if len(file_content) > 10 * 1024 * 1024:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"File {filename} exceeds 10MB limit"}
                )
            
            files_data.append({
                'filename': filename,
                'file_content': file_content
            })
        
        # Use multi-document orchestrator for enhanced parallel processing
        result = await multi_document_orchestrator.analyze_multiple_documents(files_data, prompt)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/extract-text")
async def extract_document_text(file: UploadFile = File(...)):
    """Extract text from uploaded document for viewing"""
    try:
        file_content = await file.read()
        
        # Use the document processor to extract text
        processor = DocumentProcessor()
        document_data = await processor.process_document(file_content, file.filename)
        
        return JSONResponse(content={
            "text": document_data.get("text", ""),
            "filename": file.filename,
            "word_count": document_data.get("word_count", 0),
            "char_count": document_data.get("char_count", 0)
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract text: {str(e)}"}
        )

@app.post("/api/extract-multiple-text")
async def extract_multiple_document_text(files: list[UploadFile] = File(...)):
    """Extract text from multiple uploaded documents for viewing"""
    try:
        if len(files) > 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Maximum 10 documents allowed per batch"}
            )
        
        results = []
        processor = DocumentProcessor()
        
        for file in files:
            try:
                file_content = await file.read()
                document_data = await processor.process_document(file_content, file.filename)
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "text": document_data.get("text", ""),
                    "word_count": document_data.get("word_count", 0),
                    "char_count": document_data.get("char_count", 0),
                    "error": None
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "text": "",
                    "word_count": 0,
                    "char_count": 0,
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "total_documents": len(files),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract texts: {str(e)}"}
        )

@app.get("/api/batch-status/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get the current status of a batch processing job"""
    try:
        status = multi_document_orchestrator.queue.get_batch_status(batch_id)
        if status is None:
            return JSONResponse(
                status_code=404,
                content={"error": f"Batch {batch_id} not found"}
            )
        return JSONResponse(content=status)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/batch-results/{batch_id}")
async def get_batch_results(batch_id: str, unified: bool = True):
    """Get the final results of a completed batch"""
    try:
        results = multi_document_orchestrator.queue.get_batch_results(batch_id, unified=unified)
        if results is None:
            return JSONResponse(
                status_code=404,
                content={"error": f"Batch {batch_id} not found"}
            )
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/active-batches")
async def get_active_batches():
    """Get information about all active batch processing jobs"""
    try:
        batches = multi_document_orchestrator.get_active_batches()
        return JSONResponse(content=batches)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/compare-batch/{batch_id}")
async def compare_batch_documents(batch_id: str):
    """Compare documents within a completed batch (future enhancement)"""
    try:
        comparison = await multi_document_orchestrator.compare_documents(batch_id)
        return JSONResponse(content=comparison)
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)