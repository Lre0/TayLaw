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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)