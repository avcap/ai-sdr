import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

export default function SequenceAnalyticsPage() {
  const router = useRouter()
  const { sequenceId } = router.query

  const [sequence, setSequence] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (sequenceId) {
      fetchData()
    }
  }, [sequenceId])

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch sequence details
      const seqResponse = await fetch(`/api/sequences/${sequenceId}`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const seqData = await seqResponse.json()
      setSequence(seqData)

      // Fetch analytics
      const analyticsResponse = await fetch(`/api/sequences/${sequenceId}/analytics`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const analyticsData = await analyticsResponse.json()
      setAnalytics(analyticsData)
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link href="/sequences" className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block">
            ← Back to Sequences
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            {sequence?.name || 'Sequence'} - Analytics
          </h1>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Current Leads</div>
            <div className="text-3xl font-bold text-gray-900">{analytics?.current_leads || 0}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Active Leads</div>
            <div className="text-3xl font-bold text-blue-600">{analytics?.active_leads || 0}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-3xl font-bold text-green-600">{analytics?.completed_leads || 0}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Completion Rate</div>
            <div className="text-3xl font-bold text-gray-900">{analytics?.completion_rate || 0}%</div>
          </div>
        </div>

        {/* Email Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Emails Sent</div>
            <div className="text-3xl font-bold text-gray-900">{analytics?.total_emails_sent || 0}</div>
            <div className="text-xs text-gray-500 mt-2">Total emails delivered</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Open Rate</div>
            <div className="text-3xl font-bold text-blue-600">{analytics?.open_rate || 0}%</div>
            <div className="text-xs text-gray-500 mt-2">{analytics?.total_emails_opened || 0} opens</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Reply Rate</div>
            <div className="text-3xl font-bold text-green-600">{analytics?.reply_rate || 0}%</div>
            <div className="text-xs text-gray-500 mt-2">{analytics?.total_emails_replied || 0} replies</div>
          </div>
        </div>

        {/* Empty State */}
        {(!analytics || analytics.current_leads === 0) && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">No Data Yet</h3>
            <p className="text-gray-600 mb-6">
              Analytics will appear here once leads are enrolled in this sequence
            </p>
            <button
              onClick={() => router.push(`/sequences/${sequenceId}/edit`)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
            >
              Edit Sequence
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

