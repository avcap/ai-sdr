import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

export default function SequencesPage() {
  const router = useRouter()
  
  const [sequences, setSequences] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newSequence, setNewSequence] = useState({
    name: '',
    description: ''
  })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    fetchSequences()
  }, [filterStatus])

  const fetchSequences = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filterStatus !== 'all') {
        params.append('status', filterStatus)
      }
      
      const response = await fetch(`/api/sequences?${params}`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const data = await response.json()
      setSequences(data)
    } catch (error) {
      console.error('Error fetching sequences:', error)
    } finally {
      setLoading(false)
    }
  }

  const createSequence = async () => {
    if (!newSequence.name.trim()) {
      alert('Please enter a sequence name')
      return
    }

    try {
      setCreating(true)
      const response = await fetch('/api/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(newSequence)
      })

      if (response.ok) {
        const sequence = await response.json()
        setShowCreateModal(false)
        setNewSequence({ name: '', description: '' })
        router.push(`/sequences/${sequence.id}/edit`)
      } else {
        alert('Failed to create sequence')
      }
    } catch (error) {
      console.error('Error creating sequence:', error)
      alert('Error creating sequence')
    } finally {
      setCreating(false)
    }
  }

  const deleteSequence = async (id, name) => {
    if (!confirm(`Delete "${name}"? This action cannot be undone.`)) {
      return
    }

    try {
      const response = await fetch(`/api/sequences/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer demo_token' }
      })

      if (response.ok) {
        fetchSequences()
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to delete sequence')
      }
    } catch (error) {
      console.error('Error deleting sequence:', error)
      alert('Error deleting sequence')
    }
  }

  const duplicateSequence = async (id, name) => {
    try {
      const response = await fetch(`/api/sequences/${id}/duplicate`, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer demo_token' }
      })

      if (response.ok) {
        const newSeq = await response.json()
        fetchSequences()
        alert(`Duplicated as "${newSeq.name}"`)
      } else {
        alert('Failed to duplicate sequence')
      }
    } catch (error) {
      console.error('Error duplicating sequence:', error)
      alert('Error duplicating sequence')
    }
  }

  const filteredSequences = sequences.filter(seq => 
    seq.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (seq.description && seq.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-100 text-gray-800',
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      archived: 'bg-gray-100 text-gray-600'
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badges[status] || badges.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/dashboard" className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block">
                ← Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">📧 Email Sequences</h1>
              <p className="text-gray-600 text-sm">Automate multi-touch email campaigns</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
            >
              + Create Sequence
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Total Sequences</div>
            <div className="text-3xl font-bold text-gray-900">{sequences.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Active</div>
            <div className="text-3xl font-bold text-green-600">
              {sequences.filter(s => s.status === 'active').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Total Enrolled</div>
            <div className="text-3xl font-bold text-blue-600">
              {sequences.reduce((sum, s) => sum + (s.total_enrolled || 0), 0)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-3xl font-bold text-gray-900">
              {sequences.reduce((sum, s) => sum + (s.total_completed || 0), 0)}
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="🔍 Search sequences..."
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
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        {/* Sequences List */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredSequences.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📧</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              {sequences.length === 0 ? 'No Sequences Yet' : 'No Sequences Found'}
            </h3>
            <p className="text-gray-600 mb-6">
              {sequences.length === 0 
                ? 'Create your first email sequence to start automating outreach'
                : 'Try adjusting your search or filters'}
            </p>
            {sequences.length === 0 && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
              >
                + Create Your First Sequence
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSequences.map((sequence) => (
              <div key={sequence.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900 mb-1">{sequence.name}</h3>
                      {sequence.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">{sequence.description}</p>
                      )}
                    </div>
                    {getStatusBadge(sequence.status)}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b">
                    <div>
                      <div className="text-xs text-gray-600">Steps</div>
                      <div className="text-lg font-bold text-gray-900">{sequence.steps_count || 0}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-600">Enrolled</div>
                      <div className="text-lg font-bold text-blue-600">{sequence.total_enrolled || 0}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-600">Completed</div>
                      <div className="text-lg font-bold text-green-600">{sequence.total_completed || 0}</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => router.push(`/sequences/${sequence.id}/edit`)}
                      className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => router.push(`/sequences/${sequence.id}/analytics`)}
                      className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-200"
                    >
                      Analytics
                    </button>
                    <div className="relative group">
                      <button className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-200">
                        ⋮
                      </button>
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                        <button
                          onClick={() => duplicateSequence(sequence.id, sequence.name)}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 rounded-t-lg"
                        >
                          📋 Duplicate
                        </button>
                        <button
                          onClick={() => deleteSequence(sequence.id, sequence.name)}
                          className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-b-lg"
                          disabled={sequence.status === 'active'}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Created Date */}
                  <div className="text-xs text-gray-500 mt-4">
                    Created {new Date(sequence.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-gray-900">Create New Sequence</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Sequence Name *
                </label>
                <input
                  type="text"
                  value={newSequence.name}
                  onChange={(e) => setNewSequence({...newSequence, name: e.target.value})}
                  placeholder="e.g., Cold Outreach Sequence"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newSequence.description}
                  onChange={(e) => setNewSequence({...newSequence, description: e.target.value})}
                  placeholder="Describe what this sequence does..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="p-6 border-t flex gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setNewSequence({ name: '', description: '' })
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={createSequence}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                disabled={creating}
              >
                {creating ? 'Creating...' : 'Create & Edit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

