import { useState, useEffect } from 'react'

export default function SequenceExecutionDashboard({ sequenceId, isActive }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    if (!sequenceId) return

    // Initial fetch
    fetchStats()

    // Set up polling interval (every 5 seconds if active)
    let interval
    if (isActive) {
      interval = setInterval(() => {
        fetchStats()
      }, 5000) // Poll every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [sequenceId, isActive])

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/sequences/${sequenceId}/execution-stats`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('📊 Execution Stats:', data)
        console.log('📊 Recent Activity:', data.recent_activity)
        setStats(data)
        setLastUpdated(new Date())
      }
    } catch (error) {
      console.error('Error fetching execution stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white border rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const { sequence, stats: execStats, recent_activity } = stats
  const totalEnrolled = execStats.total_enrolled
  const inProgress = execStats.active + execStats.scheduled
  const completed = execStats.completed
  const progress = totalEnrolled > 0 ? (completed / totalEnrolled) * 100 : 0

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'text-green-600'
      case 'failed': return 'text-red-600'
      case 'skipped': return 'text-yellow-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent': return '✅'
      case 'failed': return '❌'
      case 'skipped': return '⏭️'
      default: return '⏳'
    }
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    // Parse the UTC timestamp and convert to local time
    const date = new Date(timestamp)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)

    if (diff < 10) return 'Just now'
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    // Display in local timezone with time and date
    return date.toLocaleString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    })
  }

  return (
    <div className="bg-white border rounded-lg">
      {/* Header */}
      <div className="border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            🚀 Execution Dashboard
          </h3>
          <p className="text-sm text-gray-500">Real-time sequence progress</p>
        </div>
        {isActive && lastUpdated && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-500">
              Updated {formatTime(lastUpdated)}
            </span>
          </div>
        )}
      </div>

      {/* Main Stats */}
      <div className="px-6 py-4 border-b">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{totalEnrolled}</div>
            <div className="text-sm text-gray-500">Total Enrolled</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{inProgress}</div>
            <div className="text-sm text-gray-500">In Progress</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{completed}</div>
            <div className="text-sm text-gray-500">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{execStats.failed}</div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium text-gray-700">Overall Progress</span>
            <span className="font-semibold text-gray-900">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{completed} of {totalEnrolled} leads completed</span>
            {inProgress > 0 && <span>{inProgress} active</span>}
          </div>
        </div>
      </div>

      {/* Step Distribution */}
      {Object.keys(execStats.step_distribution).length > 0 && (
        <div className="px-6 py-4 border-b">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Current Step Distribution</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(execStats.step_distribution).map(([step, count]) => (
              <div key={step} className="bg-blue-50 px-3 py-2 rounded-lg">
                <span className="text-xs font-medium text-blue-700">
                  Step {step}: <span className="font-bold">{count}</span> leads
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">📋 Recent Activity</h4>
        {recent_activity && recent_activity.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {recent_activity.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 text-sm py-2 border-b last:border-0">
                <span className="text-lg">{getStatusIcon(activity.status)}</span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {activity.step_name}
                    {activity.step_type === 'email' && activity.email_sent && (
                      <span className="ml-2 text-xs text-green-600">(Email sent)</span>
                    )}
                  </div>
                  {activity.error_message && (
                    <div className="text-xs text-red-600 mt-1">{activity.error_message}</div>
                  )}
                </div>
                <span className="text-xs text-gray-500">{formatTime(activity.executed_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No activity yet</p>
            <p className="text-xs mt-1">Activity will appear here once the sequence starts executing</p>
          </div>
        )}
      </div>
    </div>
  )
}

