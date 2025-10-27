import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import LeadDetailModal from '../../components/LeadDetailModal'

export default function CampaignDetailPage() {
  const router = useRouter()
  const { campaignId } = router.query

  const [campaign, setCampaign] = useState(null)
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedLead, setSelectedLead] = useState(null)
  const [activeTab, setActiveTab] = useState('leads')
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedLeads, setSelectedLeads] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [showBulkActions, setShowBulkActions] = useState(false)
  const [editingName, setEditingName] = useState(false)
  const [newName, setNewName] = useState('')

  const leadsPerPage = 50

  useEffect(() => {
    if (campaignId) {
      fetchCampaign()
      fetchLeads()
      fetchStats()
    }
  }, [campaignId, filterStatus, searchTerm, currentPage])

  const fetchCampaign = async () => {
    try {
      const response = await fetch(`/api/campaigns/${campaignId}`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const data = await response.json()
      setCampaign(data)
      setNewName(data.name)
    } catch (error) {
      console.error('Error fetching campaign:', error)
    }
  }

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: currentPage,
        limit: leadsPerPage,
        ...(filterStatus !== 'all' && { status: filterStatus }),
        ...(searchTerm && { search: searchTerm })
      })
      
      const response = await fetch(
        `/api/campaigns/${campaignId}/leads?${params}`,
        { headers: { 'Authorization': 'Bearer demo_token' } }
      )
      const data = await response.json()
      setLeads(data)
    } catch (error) {
      console.error('Error fetching leads:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/campaigns/${campaignId}/stats`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const updateCampaign = async (updates) => {
    try {
      const response = await fetch(`/api/campaigns/${campaignId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(updates)
      })
      const data = await response.json()
      setCampaign(data)
      setEditingName(false)
      return true
    } catch (error) {
      console.error('Error updating campaign:', error)
      return false
    }
  }

  const deleteLead = async (leadId) => {
    if (!confirm('Are you sure you want to delete this lead?')) return
    
    try {
      const response = await fetch(`/api/leads/${leadId}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      
      if (response.ok) {
        setLeads(leads.filter(l => l.id !== leadId))
        fetchStats() // Refresh stats
      }
    } catch (error) {
      console.error('Error deleting lead:', error)
    }
  }

  const bulkUpdateLeads = async (updates) => {
    if (selectedLeads.length === 0) return
    
    try {
      const response = await fetch(`/api/campaigns/${campaignId}/leads/bulk-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify({
          lead_ids: selectedLeads,
          updates
        })
      })
      
      if (response.ok) {
        fetchLeads()
        fetchStats()
        setSelectedLeads([])
        setShowBulkActions(false)
      }
    } catch (error) {
      console.error('Error bulk updating leads:', error)
    }
  }

  const toggleSelectAll = () => {
    if (selectedLeads.length === leads.length) {
      setSelectedLeads([])
    } else {
      setSelectedLeads(leads.map(l => l.id))
    }
  }

  const toggleSelectLead = (leadId) => {
    if (selectedLeads.includes(leadId)) {
      setSelectedLeads(selectedLeads.filter(id => id !== leadId))
    } else {
      setSelectedLeads([...selectedLeads, leadId])
    }
  }

  const exportLeads = () => {
    const csv = [
      ['Name', 'Company', 'Title', 'Email', 'LinkedIn', 'Phone', 'Status', 'Score'].join(','),
      ...leads.map(lead => [
        lead.name,
        lead.company,
        lead.title,
        lead.email || '',
        lead.linkedin_url || '',
        lead.phone || '',
        lead.status,
        lead.score || 0
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${campaign?.name || 'campaign'}_leads.csv`
    a.click()
  }

  const getStatusBadge = (status) => {
    const badges = {
      new: 'bg-gray-100 text-gray-800',
      contacted: 'bg-blue-100 text-blue-800',
      responded: 'bg-green-100 text-green-800',
      qualified: 'bg-purple-100 text-purple-800',
      unqualified: 'bg-red-100 text-red-800'
    }
    const icons = {
      new: '⚪',
      contacted: '🟢',
      responded: '💬',
      qualified: '✅',
      unqualified: '❌'
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badges[status] || badges.new}`}>
        {icons[status]} {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    const now = new Date()
    const diff = now - date
    
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`
    return date.toLocaleDateString()
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <Link href="/campaigns">
          <button className="text-blue-600 hover:text-blue-700 mb-4 flex items-center">
            ← Back to Campaigns
          </button>
        </Link>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              {editingName ? (
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="text-2xl font-bold border-b-2 border-blue-600 focus:outline-none"
                    autoFocus
                  />
                  <button
                    onClick={() => updateCampaign({ name: newName })}
                    className="text-green-600 hover:text-green-700"
                  >
                    ✓
                  </button>
                  <button
                    onClick={() => {
                      setEditingName(false)
                      setNewName(campaign.name)
                    }}
                    className="text-red-600 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <h1
                  className="text-2xl font-bold text-gray-900 mb-2 cursor-pointer hover:text-blue-600"
                  onClick={() => setEditingName(true)}
                >
                  📊 {campaign.name}
                </h1>
              )}
              <p className="text-gray-600">{campaign.description || 'No description'}</p>
            </div>
            <div className="flex gap-2 ml-4">
              <select
                value={campaign.status}
                onChange={(e) => updateCampaign({ status: e.target.value })}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-gray-500 mt-2">
            Created: {formatDate(campaign.created_at)}
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Total Leads</div>
              <div className="text-3xl font-bold text-gray-900">{stats.total_leads}</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.new_leads} new
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Contacted</div>
              <div className="text-3xl font-bold text-blue-600">{stats.contacted_leads}</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.contact_rate}% of total
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Replies</div>
              <div className="text-3xl font-bold text-green-600">{stats.replied_leads}</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.reply_rate}% reply rate
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Qualified</div>
              <div className="text-3xl font-bold text-purple-600">{stats.qualified_leads}</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.qualification_rate}% of replies
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            <button
              className={`px-6 py-3 font-semibold ${
                activeTab === 'leads'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('leads')}
            >
              Leads ({stats?.total_leads || 0})
            </button>
            <button
              className={`px-6 py-3 font-semibold ${
                activeTab === 'activity'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('activity')}
            >
              Activity
            </button>
          </div>
        </div>
      </div>

      {/* Leads Tab */}
      {activeTab === 'leads' && (
        <div className="max-w-7xl mx-auto">
          {/* Search and Filters */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4 mb-4">
              <input
                type="text"
                placeholder="🔍 Search leads..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="responded">Responded</option>
                <option value="qualified">Qualified</option>
                <option value="unqualified">Unqualified</option>
              </select>
              <button
                onClick={exportLeads}
                className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
              >
                📥 Export CSV
              </button>
            </div>

            {selectedLeads.length > 0 && (
              <div className="flex items-center gap-4 py-2 px-4 bg-blue-50 rounded-lg">
                <span className="text-sm font-semibold">{selectedLeads.length} selected</span>
                <div className="relative">
                  <button
                    onClick={() => setShowBulkActions(!showBulkActions)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
                  >
                    Bulk Actions ▼
                  </button>
                  {showBulkActions && (
                    <div className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-lg border z-10 min-w-[200px]">
                      <button
                        onClick={() => bulkUpdateLeads({ status: 'contacted' })}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100"
                      >
                        Mark as Contacted
                      </button>
                      <button
                        onClick={() => bulkUpdateLeads({ status: 'qualified' })}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100"
                      >
                        Mark as Qualified
                      </button>
                      <button
                        onClick={() => bulkUpdateLeads({ status: 'unqualified' })}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100"
                      >
                        Mark as Unqualified
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete ${selectedLeads.length} leads?`)) {
                            Promise.all(selectedLeads.map(id => deleteLead(id)))
                            setSelectedLeads([])
                            setShowBulkActions(false)
                          }
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-red-50 text-red-600"
                      >
                        Delete Selected
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Leads Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : leads.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">👤</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">No leads found</h3>
                <p className="text-gray-600">
                  {searchTerm || filterStatus !== 'all' ? 'Try adjusting your filters' : 'Add leads to this campaign to get started'}
                </p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-6 py-3 text-left">
                          <input
                            type="checkbox"
                            checked={selectedLeads.length === leads.length && leads.length > 0}
                            onChange={toggleSelectAll}
                            className="rounded"
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {leads.map((lead) => (
                        <tr
                          key={lead.id}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => setSelectedLead(lead)}
                        >
                          <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="checkbox"
                              checked={selectedLeads.includes(lead.id)}
                              onChange={() => toggleSelectLead(lead.id)}
                              className="rounded"
                            />
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {lead.name}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {lead.company}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {lead.title}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {lead.email || '-'}
                          </td>
                          <td className="px-6 py-4">
                            {getStatusBadge(lead.status)}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`text-sm font-semibold ${getScoreColor(lead.score || 0)}`}>
                              {lead.score || 0}
                            </span>
                          </td>
                          <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => deleteLead(lead.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="px-6 py-4 border-t flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    Showing {((currentPage - 1) * leadsPerPage) + 1} - {Math.min(currentPage * leadsPerPage, stats?.total_leads || 0)} of {stats?.total_leads || 0}
                  </div>
                  <div className="flex gap-2">
                    <button
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(currentPage - 1)}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      ← Previous
                    </button>
                    <button
                      disabled={currentPage * leadsPerPage >= (stats?.total_leads || 0)}
                      onClick={() => setCurrentPage(currentPage + 1)}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Next →
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === 'activity' && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center py-12 text-gray-500">
              Activity timeline coming soon...
            </div>
          </div>
        </div>
      )}

      {/* Lead Detail Modal */}
      {selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onUpdate={(updatedLead) => {
            setLeads(leads.map(l => l.id === updatedLead.id ? updatedLead : l))
            setSelectedLead(null)
            fetchStats()
          }}
        />
      )}
    </div>
  )
}
