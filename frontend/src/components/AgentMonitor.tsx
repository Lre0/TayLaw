'use client'

import { useState, useEffect, useRef } from 'react'

interface ChunkStatus {
  chunk_index: number
  page_range: string
  status: 'idle' | 'processing' | 'completed' | 'error' | 'waiting'
  progress: number
  findings_count: number
  confidence_score: number
  processing_time: number
  current_agent: string
}

interface AgentActivity {
  timestamp: string
  agent_name: string
  status: 'idle' | 'processing' | 'completed' | 'error' | 'waiting'
  message: string
  level: 'info' | 'warning' | 'error' | 'success'
  progress?: number
  metadata?: Record<string, unknown>
  chunk_id?: string
}


interface AgentMonitorProps {
  isActive: boolean
}

export default function AgentMonitor({ isActive }: AgentMonitorProps) {
  const [activities, setActivities] = useState<AgentActivity[]>([])
  const [agentStates, setAgentStates] = useState<Record<string, string>>({})
  const [, setChunkStatuses] = useState<Record<string, ChunkStatus>>({})
  const [connected, setConnected] = useState(false)
  // Removed unused variables
  // Removed unused ref
  const activitiesEndRef = useRef<HTMLDivElement>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const activitiesContainerRef = useRef<HTMLDivElement>(null)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [lastActivityCount, setLastActivityCount] = useState(0)

  const scrollToBottom = () => {
    if (!isUserScrolledUp && activitiesEndRef.current) {
      activitiesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }


  useEffect(() => {
    // Only auto-scroll if there are new activities and user hasn't scrolled up
    if (activities.length > lastActivityCount) {
      scrollToBottom()
      setLastActivityCount(activities.length)
    }
  }, [activities, lastActivityCount, isUserScrolledUp, scrollToBottom])

  useEffect(() => {
    if (!isActive) return

    // Start with HTTP polling for now - more reliable
    startPolling()

    return () => {
      setConnected(false)
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [isActive])


  const startPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }

    const pollAgentStatus = async () => {
      try {
        // Fetch both activity history and current status for parallel processing info
        const [historyResponse, statusResponse] = await Promise.all([
          fetch('http://localhost:8000/api/agent-history?limit=20'),
          fetch('http://localhost:8000/api/agent-status')
        ])
        
        if (historyResponse.ok && statusResponse.ok) {
          const activities = await historyResponse.json()
          const status = await statusResponse.json()
          
          setActivities(activities)
          setAgentStates(status.agents || {})
          setChunkStatuses(status.chunk_statuses || {})
          setConnected(true)
        }
      } catch (err) {
        console.error('Polling error:', err)
        setConnected(false)
      }
    }

    // Initial poll
    pollAgentStatus()

    // Set up polling interval - much faster for real-time monitoring
    pollingIntervalRef.current = setInterval(pollAgentStatus, 250)
  }

  const getKeyMilestones = () => {
    // Filter activities to show only key milestones
    const keyMilestones = [
      { text: 'Document uploaded and parsed', agent: 'Document Parser', icon: '📄' },
      { text: 'Document split into chunks', agent: 'Document Chunking Agent', icon: '✂️' },
      { text: 'Parallel risk analysis completed', agent: 'Orchestrator Agent', icon: '🔍' },
      { text: 'Cross-reference validation done', agent: 'Cross-Reference Agent', icon: '🔗' },
      { text: 'Analysis consolidated across documents', agent: 'Analysis Consolidation Agent', icon: '🔄' },
      { text: 'Results combined and report generated', agent: 'Report Generator', icon: '📊' }
    ]

    return keyMilestones.map(milestone => {
      const agentStatus = agentStates[milestone.agent] || 'idle'
      const isCompleted = agentStatus === 'completed'
      const isProcessing = agentStatus === 'processing'
      
      // Find the completion activity for this agent (when status changed to completed)
      const agentActivities = activities.filter(a => a.agent_name === milestone.agent)
      const completionActivity = agentActivities.find(a => a.status === 'completed') || agentActivities[agentActivities.length - 1]
      
      return {
        ...milestone,
        completed: isCompleted,
        processing: isProcessing,
        time: isCompleted && completionActivity ? new Date(completionActivity.timestamp).toLocaleTimeString() : null,
        icon: isCompleted ? '✅' : isProcessing ? '🔄' : milestone.icon
      }
    })
  }

  if (!isActive) {
    return (
      <div className="bg-gray-100 rounded-lg p-6 text-center">
        <p className="text-gray-500">Agent monitoring will appear here during document analysis</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Processing Monitor
          </h3>
          <div className="flex items-center space-x-3">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-500">
              {connected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      {/* Key Milestones */}
      <div className="p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Key Milestones</h4>
        <div className="space-y-2">
          {getKeyMilestones().map((milestone, index) => (
            <div key={index} className="flex items-center space-x-3 text-sm">
              <span>{milestone.icon}</span>
              <span className={`${milestone.completed ? 'text-gray-900' : 'text-gray-400'}`}>
                {milestone.text}
              </span>
              {milestone.time && (
                <span className="text-xs text-gray-500 ml-auto">
                  {milestone.time}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}