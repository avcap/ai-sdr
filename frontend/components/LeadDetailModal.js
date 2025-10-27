import { useState } from 'react'

export default function LeadDetailModal({ lead, onClose, onUpdate }) {
  const [editedLead, setEditedLead] = useState({ ...lead })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    try {
      setSaving(true)
      const response = await fetch(`/api/leads/${lead.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(editedLead)
      })

      if (response.ok) {
        const updatedLead = await response.json()
        onUpdate(updatedLead)
      } else {
        alert('Failed to update lead')
      }
    } catch (error) {
      console.error('Error updating lead:', error)
      alert('Error updating lead')
    } finally {
      setSaving(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600 bg-green-100'
    if (score >= 40) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getScoreLabel = (score) => {
    if (score >= 70) return 'High Quality'
    if (score >= 40) return 'Medium Quality'
    return 'Low Quality'
  }

  const getOutreachHistory = () => {
    // Extract outreach history from lead.data if it exists
    if (lead.data && typeof lead.data === 'object' && lead.data.outreach_log) {
      return lead.data.outreach_log
    }
    return []
  }

  const outreachHistory = getOutreachHistory()

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Lead Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left Column - Profile */}
            <div className="md:col-span-2 space-y-6">
              {/* Profile Information */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">👤 Profile</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={editedLead.name}
                      onChange={(e) => setEditedLead({ ...editedLead, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                    <input
                      type="text"
                      value={editedLead.company}
                      onChange={(e) => setEditedLead({ ...editedLead, company: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                    <input
                      type="text"
                      value={editedLead.title}
                      onChange={(e) => setEditedLead({ ...editedLead, title: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={editedLead.email || ''}
                      onChange={(e) => setEditedLead({ ...editedLead, email: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="email@example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn URL</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={editedLead.linkedin_url || ''}
                        onChange={(e) => setEditedLead({ ...editedLead, linkedin_url: e.target.value })}
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="https://linkedin.com/in/..."
                      />
                      {editedLead.linkedin_url && (
                        <a
                          href={editedLead.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          🔗
                        </a>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={editedLead.phone || ''}
                      onChange={(e) => setEditedLead({ ...editedLead, phone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                      <input
                        type="text"
                        value={editedLead.industry || ''}
                        onChange={(e) => setEditedLead({ ...editedLead, industry: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Technology"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Company Size</label>
                      <input
                        type="text"
                        value={editedLead.company_size || ''}
                        onChange={(e) => setEditedLead({ ...editedLead, company_size: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="50-200"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={editedLead.location || ''}
                      onChange={(e) => setEditedLead({ ...editedLead, location: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="San Francisco, CA"
                    />
                  </div>
                </div>
              </div>

              {/* Outreach History */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📧 Outreach History</h3>
                
                {outreachHistory.length > 0 ? (
                  <div className="space-y-3">
                    {outreachHistory.map((activity, index) => (
                      <div key={index} className="bg-white rounded-lg p-4 border">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-semibold text-gray-900">
                            {activity.action === 'email_sent' ? '📧 Email Sent' : 
                             activity.action === 'email_opened' ? '👁️ Email Opened' :
                             activity.action === 'link_clicked' ? '🔗 Link Clicked' :
                             activity.action === 'reply_received' ? '💬 Reply Received' :
                             activity.action}
                          </div>
                          <div className="text-sm text-gray-500">
                            {new Date(activity.timestamp).toLocaleString()}
                          </div>
                        </div>
                        {activity.subject && (
                          <div className="text-sm text-gray-600 mb-1">
                            <strong>Subject:</strong> {activity.subject}
                          </div>
                        )}
                        {activity.message && (
                          <div className="text-sm text-gray-600">
                            {activity.message.substring(0, 150)}...
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No outreach activity yet
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Status & Actions */}
            <div className="space-y-6">
              {/* Score Card */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Lead Score</h3>
                <div className={`text-4xl font-bold mb-2 ${getScoreColor(editedLead.score || 0)}`}>
                  {editedLead.score || 0}
                  <span className="text-lg">/100</span>
                </div>
                <div className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${getScoreColor(editedLead.score || 0)}`}>
                  {getScoreLabel(editedLead.score || 0)}
                </div>
              </div>

              {/* Status */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Status</h3>
                <select
                  value={editedLead.status}
                  onChange={(e) => setEditedLead({ ...editedLead, status: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="new">⚪ New</option>
                  <option value="contacted">🟢 Contacted</option>
                  <option value="responded">💬 Responded</option>
                  <option value="qualified">✅ Qualified</option>
                  <option value="unqualified">❌ Unqualified</option>
                </select>
              </div>

              {/* Quick Actions */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => setEditedLead({ ...editedLead, status: 'qualified' })}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
                  >
                    ✅ Mark as Qualified
                  </button>
                  <button
                    onClick={() => setEditedLead({ ...editedLead, status: 'unqualified' })}
                    className="w-full px-4 py-2 bg-red-100 text-red-600 rounded-lg font-semibold hover:bg-red-200"
                  >
                    ❌ Mark as Unqualified
                  </button>
                  <button
                    onClick={() => setEditedLead({ ...editedLead, status: 'contacted' })}
                    className="w-full px-4 py-2 bg-blue-100 text-blue-600 rounded-lg font-semibold hover:bg-blue-200"
                  >
                    📧 Mark as Contacted
                  </button>
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-gray-50 rounded-lg p-6 text-sm text-gray-600">
                <div className="space-y-2">
                  <div>
                    <strong>Lead ID:</strong><br/>
                    <span className="text-xs font-mono">{lead.id}</span>
                  </div>
                  <div>
                    <strong>Created:</strong><br/>
                    {new Date(lead.created_at).toLocaleString()}
                  </div>
                  {lead.updated_at && (
                    <div>
                      <strong>Last Updated:</strong><br/>
                      {new Date(lead.updated_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

