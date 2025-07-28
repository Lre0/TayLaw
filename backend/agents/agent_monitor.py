import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel

class AgentStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"

class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class ChunkStatus(BaseModel):
    chunk_id: str
    chunk_index: int
    page_range: str
    status: AgentStatus
    progress: float = 0.0
    findings_count: int = 0
    confidence_score: float = 0.0
    processing_time: float = 0.0
    current_agent: str = ""

class AgentActivity(BaseModel):
    timestamp: datetime
    agent_name: str
    status: AgentStatus
    message: str
    level: LogLevel
    progress: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_id: Optional[str] = None

class AgentMonitor:
    """Real-time monitoring system for parallel multi-agent workflows"""
    
    def __init__(self):
        self.activities: List[AgentActivity] = []
        self.agent_states: Dict[str, AgentStatus] = {}
        self.chunk_statuses: Dict[str, ChunkStatus] = {}
        self.subscribers: List[asyncio.Queue] = []
        self.workflow_id: Optional[str] = None
        self.parallel_processing_active: bool = False
        self.total_chunks: int = 0
        self.completed_chunks: int = 0
    
    async def log_chunk_activity(self,
                                chunk_id: str,
                                chunk_index: int,
                                page_range: str,
                                agent_name: str,
                                status: AgentStatus,
                                message: str,
                                level: LogLevel = LogLevel.INFO,
                                progress: float = 0.0,
                                findings_count: int = 0,
                                confidence_score: float = 0.0,
                                processing_time: float = 0.0):
        """Log chunk-specific activity for parallel processing monitoring"""
        
        # Update or create chunk status
        self.chunk_statuses[chunk_id] = ChunkStatus(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            page_range=page_range,
            status=status,
            progress=progress,
            findings_count=findings_count,
            confidence_score=confidence_score,
            processing_time=processing_time,
            current_agent=agent_name
        )
        
        # Log the activity
        await self.log_activity(
            agent_name=f"Chunk {chunk_index + 1} ({agent_name})",
            status=status,
            message=message,
            level=level,
            progress=progress,
            metadata={
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "page_range": page_range,
                "findings_count": findings_count,
                "confidence_score": confidence_score,
                "processing_time": processing_time
            },
            chunk_id=chunk_id
        )
        
        # Update completion tracking
        if status == AgentStatus.COMPLETED:
            self.completed_chunks = sum(1 for chunk in self.chunk_statuses.values() 
                                      if chunk.status == AgentStatus.COMPLETED)
    
    async def log_activity(self, 
                          agent_name: str, 
                          status: AgentStatus, 
                          message: str, 
                          level: LogLevel = LogLevel.INFO,
                          progress: Optional[float] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          chunk_id: Optional[str] = None):
        """Log agent activity and notify subscribers"""
        
        activity = AgentActivity(
            timestamp=datetime.now(),
            agent_name=agent_name,
            status=status,
            message=message,
            level=level,
            progress=progress,
            metadata=metadata or {},
            chunk_id=chunk_id
        )
        
        self.activities.append(activity)
        self.agent_states[agent_name] = status
        
        # Notify all subscribers
        await self._notify_subscribers(activity)
    
    async def _notify_subscribers(self, activity: AgentActivity):
        """Send activity updates to all WebSocket subscribers"""
        if not self.subscribers:
            return
            
        activity_data = {
            "type": "agent_activity",
            "data": {
                "timestamp": activity.timestamp.isoformat(),
                "agent_name": activity.agent_name,
                "status": activity.status,
                "message": activity.message,
                "level": activity.level,
                "progress": activity.progress,
                "metadata": activity.metadata,
                "chunk_id": activity.chunk_id
            }
        }
        
        # Also send parallel processing status update
        if self.parallel_processing_active:
            parallel_status = {
                "type": "parallel_status",
                "data": {
                    "total_chunks": self.total_chunks,
                    "completed_chunks": self.completed_chunks,
                    "chunk_statuses": {
                        chunk_id: {
                            "chunk_index": chunk.chunk_index,
                            "page_range": chunk.page_range,
                            "status": chunk.status,
                            "progress": chunk.progress,
                            "findings_count": chunk.findings_count,
                            "confidence_score": chunk.confidence_score,
                            "processing_time": chunk.processing_time,
                            "current_agent": chunk.current_agent
                        } for chunk_id, chunk in self.chunk_statuses.items()
                    }
                }
            }
            
            # Send parallel status to all subscribers
            for queue in self.subscribers[:]:
                try:
                    await queue.put(parallel_status)
                except:
                    self.subscribers.remove(queue)
        
        # Send to all connected WebSocket clients
        for queue in self.subscribers[:]:  # Copy list to avoid modification during iteration
            try:
                await queue.put(activity_data)
            except:
                # Remove disconnected subscribers
                self.subscribers.remove(queue)
    
    def subscribe(self, queue: asyncio.Queue):
        """Subscribe to real-time agent updates"""
        self.subscribers.append(queue)
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from real-time agent updates"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
    
    def start_parallel_processing(self, total_chunks: int):
        """Initialize parallel processing monitoring"""
        self.parallel_processing_active = True
        self.total_chunks = total_chunks
        self.completed_chunks = 0
        self.chunk_statuses.clear()
    
    def end_parallel_processing(self):
        """Complete parallel processing monitoring"""
        self.parallel_processing_active = False
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current status of all agents and parallel processing"""
        return {
            "agents": self.agent_states,
            "total_activities": len(self.activities),
            "workflow_id": self.workflow_id,
            "last_update": self.activities[-1].timestamp.isoformat() if self.activities else None,
            "parallel_processing": {
                "active": self.parallel_processing_active,
                "total_chunks": self.total_chunks,
                "completed_chunks": self.completed_chunks,
                "completion_percentage": (self.completed_chunks / self.total_chunks * 100) if self.total_chunks > 0 else 0
            },
            "chunk_statuses": {
                chunk_id: {
                    "chunk_index": chunk.chunk_index,
                    "page_range": chunk.page_range,
                    "status": chunk.status,
                    "progress": chunk.progress,
                    "findings_count": chunk.findings_count,
                    "confidence_score": chunk.confidence_score,
                    "processing_time": chunk.processing_time,
                    "current_agent": chunk.current_agent
                } for chunk_id, chunk in self.chunk_statuses.items()
            }
        }
    
    def get_activity_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity history, ensuring milestone activities are always included"""
        if not self.activities:
            return []
        
        # Define milestone agents that should always be included
        milestone_agents = {
            "Document Parser", 
            "Document Chunking Agent", 
            "Orchestrator Agent", 
            "Cross-Reference Agent", 
            "Results Combination Agent", 
            "Report Generator",
            "Analysis Consolidation Agent"
        }
        
        # Get recent activities
        recent_activities = self.activities[-limit:]
        
        # Find any milestone completion activities that might have been excluded
        milestone_completions = []
        for activity in self.activities:
            if (activity.agent_name in milestone_agents and 
                activity.status == AgentStatus.COMPLETED and 
                activity not in recent_activities):
                milestone_completions.append(activity)
        
        # Combine milestone completions with recent activities, sorted by timestamp
        all_activities = milestone_completions + recent_activities
        all_activities.sort(key=lambda x: x.timestamp)
        
        # Remove duplicates while preserving order
        seen_activities = set()
        unique_activities = []
        for activity in all_activities:
            activity_key = (activity.timestamp, activity.agent_name, activity.status, activity.message)
            if activity_key not in seen_activities:
                seen_activities.add(activity_key)
                unique_activities.append(activity)
        
        return [
            {
                "timestamp": activity.timestamp.isoformat(),
                "agent_name": activity.agent_name,
                "status": activity.status,
                "message": activity.message,
                "level": activity.level,
                "progress": activity.progress,
                "metadata": activity.metadata,
                "chunk_id": activity.chunk_id
            }
            for activity in unique_activities
        ]
    
    def clear_history(self):
        """Clear activity history for new workflow"""
        self.activities.clear()
        self.agent_states.clear()
        self.chunk_statuses.clear()
        self.workflow_id = None
        self.parallel_processing_active = False
        self.total_chunks = 0
        self.completed_chunks = 0

# Global monitor instance
agent_monitor = AgentMonitor()