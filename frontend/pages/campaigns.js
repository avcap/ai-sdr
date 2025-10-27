import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

export default function CampaignsPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [sortBy, setSortBy] = useState('created_at')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null)

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/campaigns', {
        headers: {
          'Authorization': 'Bearer demo_token'
        }
      })
      const data = await response.json()
      setCampaigns(data)
    } catch (error) {
      console.error('Error fetching campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteCampaign = async (campaignId) => {
    try {
      const response = await fetch(`http://localhost:8000/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer demo_token'
        }
      })
      
      if (response.ok) {
        // Remove from local state
        setCampaigns(campaigns.filter(c => c.id !== campaignId))
        setShowDeleteConfirm(null)
      }
    } catch (error) {
      console.error('Error deleting campaign:', error)
      alert('Failed to delete campaign')
    }
  }

  // Filter and sort campaigns
  const filteredCampaigns = campaigns
    .filter(campaign => {
      // Status filter
      if (filterStatus !== 'all' && campaign.status !== filterStatus) return false
      
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        return (
          campaign.name.toLowerCase().includes(searchLower) ||
          campaign.description?.toLowerCase().includes(searchLower)
        )
      }
      
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'created_at') {
        return new Date(b.created_at) - new Date(a.created_at)
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name)
      } else if (sortBy === 'lead_count') {
        return (b.total_leads || 0) - (a.total_leads || 0)
      } else if (sortBy === 'reply_rate') {
        return (b.reply_rate || 0) - (a.reply_rate || 0)
      }
      return 0
    })

  // Calculate stats
  const totalCampaigns = campaigns.length
  const activeCampaigns = campaigns.filter(c => c.status === 'active').length
  const totalLeads = campaigns.reduce((sum, c) => sum + (c.total_leads || 0), 0)
  const avgReplyRate = campaigns.length > 0
    ? (campaigns.reduce((sum, c) => sum + (c.reply_rate || 0), 0) / campaigns.length).toFixed(1)
    : 0

  const getStatusBadge = (status) => {
    const badges = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800'
    }
    const icons = {
      active: '🟢',
      draft: '⚪',
      paused: '🟡',
      completed: '✅'
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badges[status] || badges.draft}`}>
        {icons[status]} {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📊 Campaigns</h1>
            <p className="text-gray-600 mt-1">Manage your outreach campaigns</p>
          </div>
          <Link href="/dashboard">
            <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition shadow-lg">
              + Create Campaign
            </button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">Total Campaigns</div>
            <div className="text-3xl font-bold text-gray-900">{totalCampaigns}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">Active</div>
            <div className="text-3xl font-bold text-green-600">{activeCampaigns}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">Total Leads</div>
            <div className="text-3xl font-bold text-blue-600">{totalLeads}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">Avg Reply Rate</div>
            <div className="text-3xl font-bold text-purple-600">{avgReplyRate}%</div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="🔍 Search campaigns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="created_at">Sort by Date</option>
              <option value="name">Sort by Name</option>
              <option value="lead_count">Sort by Lead Count</option>
              <option value="reply_rate">Sort by Reply Rate</option>
            </select>
          </div>
        </div>
      </div>

      {/* Campaigns Grid */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredCampaigns.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              {searchTerm || filterStatus !== 'all' ? 'No campaigns found' : 'No campaigns yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm || filterStatus !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first campaign to start reaching out to prospects'}
            </p>
            {!searchTerm && filterStatus === 'all' && (
              <Link href="/dashboard">
                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">
                  + Create Campaign
                </button>
              </Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCampaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer"
              >
                <div className="p-6">
                  {/* Campaign Header */}
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-bold text-gray-900 flex-1 mr-2">
                      {campaign.name}
                    </h3>
                    {getStatusBadge(campaign.status)}
                  </div>

                  {/* Campaign Description */}
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {campaign.description || 'No description'}
                  </p>

                  {/* Stats */}
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">📊 Leads</span>
                      <span className="font-semibold">{campaign.total_leads || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">📧 Contacted</span>
                      <span className="font-semibold">{campaign.contacted_leads || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">💬 Replies</span>
                      <span className="font-semibold">
                        {campaign.replied_leads || 0} ({campaign.reply_rate || 0}%)
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
                        style={{ width: `${campaign.progress_percentage || 0}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-600 mt-1 text-right">
                      {campaign.progress_percentage || 0}% complete
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="text-xs text-gray-500 mb-4">
                    Created: {formatDate(campaign.created_at)}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Link href={`/campaigns/${campaign.id}`} className="flex-1">
                      <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">
                        View
                      </button>
                    </Link>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setShowDeleteConfirm(campaign.id)
                      }}
                      className="px-4 py-2 bg-red-100 text-red-600 rounded-lg font-semibold hover:bg-red-200 transition"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Delete Campaign?</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this campaign? This will also delete all associated leads. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteCampaign(showDeleteConfirm)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

