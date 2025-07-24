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
  metadata?: Record<string, any>
  chunk_id?: string
}

interface ParallelProcessingStatus {
  active: boolean
  total_chunks: number
  completed_chunks: number
  completion_percentage: number
}

interface AgentMonitorProps {
  isActive: boolean
}

export default function AgentMonitor({ isActive }: AgentMonitorProps) {
  const [activities, setActivities] = useState<AgentActivity[]>([])
  const [agentStates, setAgentStates] = useState<Record<string, string>>({})
  const [chunkStatuses, setChunkStatuses] = useState<Record<string, ChunkStatus>>({})
  const [parallelStatus, setParallelStatus] = useState<ParallelProcessingStatus>({ 
    active: false, 
    total_chunks: 0, 
    completed_chunks: 0, 
    completion_percentage: 0 
  })
  const [connected, setConnected] = useState(false)
  const [usePolling, setUsePolling] = useState(false)
  const websocketRef = useRef<WebSocket | null>(null)
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

  const checkScrollPosition = () => {
    if (activitiesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = activitiesContainerRef.current
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 10
      setIsUserScrolledUp(!isAtBottom)
    }
  }

  useEffect(() => {
    // Only auto-scroll if there are new activities and user hasn't scrolled up
    if (activities.length > lastActivityCount) {
      scrollToBottom()
      setLastActivityCount(activities.length)
    }
  }, [activities, lastActivityCount, isUserScrolledUp])

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

  const connectWebSocket = () => {
    // WebSocket implementation can be added later if needed
    // For now, use HTTP polling which is more reliable
    startPolling()
  }

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
          setParallelStatus(status.parallel_processing || { active: false, total_chunks: 0, completed_chunks: 0, completion_percentage: 0 })
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'text-blue-600 bg-blue-50'
      case 'completed': return 'text-green-600 bg-green-50'
      case 'error': return 'text-red-600 bg-red-50'
      case 'waiting': return 'text-yellow-600 bg-yellow-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-green-700 border-green-200 bg-green-50'
      case 'warning': return 'text-yellow-700 border-yellow-200 bg-yellow-50'
      case 'error': return 'text-red-700 border-red-200 bg-red-50'
      default: return 'text-blue-700 border-blue-200 bg-blue-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing': return '🔄'
      case 'completed': return '✅'
      case 'error': return '❌'
      case 'waiting': return '⏸️'
      default: return '⚪'
    }
  }

  const getMainAgents = () => {
    // Simplified workflow progress based on actual state
    const steps = [
      { name: 'Document Parser', progress: getStepProgress('parsing') },
      { name: 'Document Chunking', progress: getStepProgress('chunking') }, 
      { name: 'Parallel Analysis', progress: getStepProgress('analysis') },
      { name: 'Cross-Reference', progress: getStepProgress('cross_ref') },
      { name: 'Results Combination', progress: getStepProgress('combination') },
      { name: 'Report Generation', progress: getStepProgress('report') }
    ]

    return steps.map(step => {
      let color, icon, status
      
      if (step.progress === 100) {
        color = 'bg-green-500'
        icon = '✅'
        status = 'completed'
      } else if (step.progress > 0) {
        color = 'bg-blue-500'
        icon = '🔄'
        status = 'processing'
      } else {
        color = 'bg-gray-300'
        icon = '⚪'
        status = 'idle'
      }

      return {
        name: step.name,
        progress: step.progress,
        color,
        icon,
        status
      }
    })
  }

  const getStepProgress = (step: string): number => {
    const hasDocumentParser = agentStates['Document Parser'] === 'completed'
    const hasChunking = agentStates['Document Chunking Agent'] === 'completed'
    const parallelComplete = parallelStatus.completed_chunks >= parallelStatus.total_chunks && parallelStatus.total_chunks > 0
    const hasCrossRef = agentStates['Cross-Reference Agent'] === 'completed'
    const hasCombination = agentStates['Results Combination Agent'] === 'completed'
    const hasReport = agentStates['Report Generator'] === 'completed'
    
    // Determine progress based on actual workflow state
    switch (step) {
      case 'parsing':
        return hasDocumentParser ? 100 : (Object.keys(agentStates).length > 0 ? 50 : 0)
      
      case 'chunking':
        if (!hasDocumentParser) return 0
        return hasChunking ? 100 : (agentStates['Document Chunking Agent'] === 'processing' ? 50 : 10)
      
      case 'analysis':
        if (!hasChunking) return 0
        if (parallelStatus.total_chunks === 0) return 10
        return parallelComplete ? 100 : Math.max(10, parallelStatus.completion_percentage)
      
      case 'cross_ref':
        if (!parallelComplete) return 0
        return hasCrossRef ? 100 : (agentStates['Cross-Reference Agent'] === 'processing' ? 50 : 10)
      
      case 'combination':
        if (!hasCrossRef) return 0
        return hasCombination ? 100 : (agentStates['Results Combination Agent'] === 'processing' ? 50 : 10)
      
      case 'report':
        if (!hasCombination) return 0
        return hasReport ? 100 : (agentStates['Report Generator'] === 'processing' ? 50 : 10)
      
      default:
        return 0
    }
  }

  const getKeyMilestones = () => {
    // Filter activities to show only key milestones
    const keyMilestones = [
      { text: 'Document uploaded and parsed', agent: 'Document Parser', icon: '📄' },
      { text: 'Document split into chunks', agent: 'Document Chunking Agent', icon: '✂️' },
      { text: 'Parallel risk analysis completed', agent: 'Orchestrator Agent', icon: '🔍' },
      { text: 'Cross-reference validation done', agent: 'Cross-Reference Agent', icon: '🔗' },
      { text: 'Results combined and report generated', agent: 'Report Generator', icon: '📊' }
    ]

    return keyMilestones.map(milestone => {
      const agentStatus = agentStates[milestone.agent] || 'idle'
      const isCompleted = agentStatus === 'completed'
      const isProcessing = agentStatus === 'processing'
      
      // Find the most recent activity for this agent
      const agentActivities = activities.filter(a => a.agent_name === milestone.agent)
      const lastActivity = agentActivities[agentActivities.length - 1]
      
      return {
        ...milestone,
        completed: isCompleted,
        processing: isProcessing,
        time: isCompleted && lastActivity ? new Date(lastActivity.timestamp).toLocaleTimeString() : null,
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

      {/* Parallel Processing Status */}
      {parallelStatus.active && (
        <div className="p-4 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Document Analysis Progress</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Overall Progress</span>
              <span className="text-sm font-medium text-gray-900">
                {parallelStatus.completed_chunks} / {parallelStatus.total_chunks} chunks
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${parallelStatus.completion_percentage}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500">
              {parallelStatus.completion_percentage.toFixed(0)}% complete
            </div>
          </div>
        </div>
      )}

      {/* Agent Progress */}
      <div className="p-4 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Agent Progress</h4>
        <div className="space-y-3">
          {getMainAgents().map((agent) => (
            <div key={agent.name} className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 w-36">
                <span>{agent.icon}</span>
                <span className="text-sm font-medium text-gray-700">{agent.name}</span>
              </div>
              <div className="flex-1">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${agent.color}`}
                    style={{ width: `${agent.progress}%` }}
                  ></div>
                </div>
              </div>
              <div className="text-xs text-gray-500 w-12 text-right">
                {agent.progress}%
              </div>
            </div>
          ))}
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