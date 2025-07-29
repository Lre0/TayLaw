from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, Request
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import json
import io
import os
from dotenv import load_dotenv
from agents.document_processor import DocumentProcessor
from agents.risk_analyzer import RiskAnalyzer
from agents.orchestrator import Orchestrator
from agents.langgraph_orchestrator import LangGraphOrchestrator
from agents.unified_orchestrator import UnifiedDocumentOrchestrator
from agents.agent_monitor import agent_monitor

load_dotenv()

app = FastAPI(title="Legal AI Assistant API")

# Custom CORS middleware to ensure headers are added
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

app.add_middleware(CustomCORSMiddleware)

# Use unified orchestrator for both single and multiple documents
unified_orchestrator = UnifiedDocumentOrchestrator(max_concurrent_documents=5)
fallback_orchestrator = Orchestrator()

@app.get("/")
async def root():
    return {"message": "Legal AI Assistant API"}

@app.get("/test-cors")
async def test_cors():
    """Test endpoint to verify CORS headers"""
    return {"message": "CORS test", "timestamp": "2025-07-28"}

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}

@app.post("/api/analyze")
async def analyze_document(
    files: Union[UploadFile, list[UploadFile]] = File(...),
    prompt: str = Form(...),
    unified: bool = Form(True),
    color_coded: bool = Form(False)
):
    """Unified endpoint for single or multiple document analysis"""
    try:
        # Normalize files to list format
        if not isinstance(files, list):
            files = [files]
        
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
        
        # Prepare files data
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
        
        # Use unified orchestrator
        result = await unified_orchestrator.analyze_documents(files_data, prompt, unified, color_coded)
        
        return JSONResponse(content=result)
    
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False, log_level="warning")