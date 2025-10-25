import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/router'
import axios from 'axios'
import toast from 'react-hot-toast'
import GoogleSheetsImport from '../../components/GoogleSheetsImport'
import {
  DocumentArrowUpIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  CheckIcon,
  XMarkIcon,
  TableCellsIcon
} from '@heroicons/react/24/outline'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function CampaignDetail() {
  const { data: session } = useSession()
  const router = useRouter()
  const { campaignId } = router.query
  
  const [campaign, setCampaign] = useState(null)
  const [leads, setLeads] = useState([])
  const [outreachLogs, setOutreachLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showLeadModal, setShowLeadModal] = useState(false)
  const [showSheetsImport, setShowSheetsImport] = useState(false)
  const [editingLead, setEditingLead] = useState(null)

  useEffect(() => {
    if (campaignId) {
      fetchCampaignData()
    }
  }, [campaignId])

  const fetchCampaignData = async () => {
    try {
      const [campaignRes, leadsRes, logsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/campaigns/${campaignId}`, {
          headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
        }),
        axios.get(`${API_BASE_URL}/campaigns/${campaignId}/leads`, {
          headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
        }),
        axios.get(`${API_BASE_URL}/campaigns/${campaignId}/outreach-logs`, {
          headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
        })
      ])

      setCampaign(campaignRes.data)
      setLeads(leadsRes.data)
      setOutreachLogs(logsRes.data)
    } catch (error) {
      console.error('Error fetching campaign data:', error)
      toast.error('Failed to fetch campaign data')
    } finally {
      setLoading(false)
    }
  }

  const handleSheetsImportComplete = (result) => {
    toast.success(`Successfully imported ${result.leads_added || result.leads_created} leads from Google Sheets`)
    setShowSheetsImport(false)
    fetchCampaignData() // Refresh data
  }

  const handleFileUpload = async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        `${API_BASE_URL}/campaigns/${campaignId}/leads/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${session?.accessToken || 'demo_token'}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      toast.success(`Successfully uploaded ${response.data.leads_created} leads`);
      setShowUploadModal(false);
      fetchCampaignData(); // Refresh data
    } catch (error) {
      console.error('Error uploading leads:', error);
      toast.error('Failed to upload leads file');
    }
  }

  const handleCreateLead = async (leadData) => {
    try {
      await axios.post(`${API_BASE_URL}/campaigns/${campaignId}/leads`, leadData, {
        headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
      })
      
      toast.success('Lead created successfully')
      setShowLeadModal(false)
      fetchCampaignData()
    } catch (error) {
      console.error('Error creating lead:', error)
      toast.error('Failed to create lead')
    }
  }

  const handleUpdateLead = async (leadId, leadData) => {
    try {
      await axios.put(`${API_BASE_URL}/leads/${leadId}`, leadData, {
        headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
      })
      
      toast.success('Lead updated successfully')
      setEditingLead(null)
      fetchCampaignData()
    } catch (error) {
      console.error('Error updating lead:', error)
      toast.error('Failed to update lead')
    }
  }

  const handleDeleteLead = async (leadId) => {
    if (!confirm('Are you sure you want to delete this lead?')) return

    try {
      await axios.delete(`${API_BASE_URL}/leads/${leadId}`, {
        headers: { Authorization: `Bearer ${session?.accessToken || 'demo_token'}` }
      })
      
      toast.success('Lead deleted successfully')
      fetchCampaignData()
    } catch (error) {
      console.error('Error deleting lead:', error)
      toast.error('Failed to delete lead')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Campaign Not Found</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <button
                onClick={() => router.push('/dashboard')}
                className="text-blue-600 hover:text-blue-800 mb-2"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
              <p className="text-gray-600">{campaign.description}</p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowSheetsImport(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 flex items-center"
              >
                <TableCellsIcon className="h-5 w-5 mr-2" />
                Import from Sheets
              </button>
              <button
                onClick={() => setShowUploadModal(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center"
              >
                <DocumentArrowUpIcon className="h-5 w-5 mr-2" />
                Upload Leads
              </button>
              <button
                onClick={() => setShowLeadModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Lead
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Campaign Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-blue-600">{leads.length}</div>
            <div className="text-sm text-gray-600">Total Leads</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-green-600">
              {outreachLogs.filter(log => log.message_sent).length}
            </div>
            <div className="text-sm text-gray-600">Messages Sent</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-yellow-600">
              {outreachLogs.filter(log => log.response_received).length}
            </div>
            <div className="text-sm text-gray-600">Responses</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-purple-600">
              {outreachLogs.filter(log => log.meeting_scheduled).length}
            </div>
            <div className="text-sm text-gray-600">Meetings</div>
          </div>
        </div>

        {/* Leads Table */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Leads</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => (
                  <tr key={lead.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lead.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.company}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        lead.status === 'completed' ? 'bg-green-100 text-green-800' :
                        lead.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {lead.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setEditingLead(lead)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteLead(lead.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Outreach Logs */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Outreach Logs</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lead
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sent At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Response
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Meeting
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {outreachLogs.map((log) => {
                  const lead = leads.find(l => l.id === log.lead_id)
                  return (
                    <tr key={log.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {lead?.name || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {log.channel}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {log.sent_at ? new Date(log.sent_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {log.response_received ? (
                          <CheckIcon className="h-5 w-5 text-green-500" />
                        ) : (
                          <XMarkIcon className="h-5 w-5 text-gray-400" />
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {log.meeting_scheduled ? (
                          <CheckIcon className="h-5 w-5 text-green-500" />
                        ) : (
                          <XMarkIcon className="h-5 w-5 text-gray-400" />
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          log.status === 'completed' ? 'bg-green-100 text-green-800' :
                          log.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Google Sheets Import Modal */}
      {showSheetsImport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Import Leads from Google Sheets</h2>
              <button
                onClick={() => setShowSheetsImport(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <GoogleSheetsImport
              campaignId={campaignId}
              onImportComplete={handleSheetsImportComplete}
            />
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <FileUploadModal
          onClose={() => setShowUploadModal(false)}
          onUpload={handleFileUpload}
        />
      )}

      {/* Lead Modal */}
      {showLeadModal && (
        <LeadModal
          onClose={() => setShowLeadModal(false)}
          onSubmit={handleCreateLead}
        />
      )}

      {/* Edit Lead Modal */}
      {editingLead && (
        <LeadModal
          lead={editingLead}
          onClose={() => setEditingLead(null)}
          onSubmit={(data) => handleUpdateLead(editingLead.id, data)}
        />
      )}
    </div>
  )
}

// File Upload Modal Component
function FileUploadModal({ onClose, onUpload }) {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) {
      onUpload(file)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Upload Leads</h2>
        
        <form onSubmit={handleSubmit}>
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {file ? (
              <div>
                <p className="text-sm text-gray-600">{file.name}</p>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="text-red-600 text-sm mt-2"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div>
                <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm text-gray-600 mb-2">
                  Drag and drop your CSV/Excel file here, or click to select
                </p>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 cursor-pointer"
                >
                  Select File
                </label>
              </div>
            )}
          </div>

          <div className="mt-4 text-xs text-gray-500">
            <p>Required columns: name, company, title</p>
            <p>Optional columns: email, linkedin_url, phone, industry, company_size, location</p>
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              type="submit"
              disabled={!file}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Upload
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Lead Modal Component
function LeadModal({ lead, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: lead?.name || '',
    company: lead?.company || '',
    title: lead?.title || '',
    email: lead?.email || '',
    linkedin_url: lead?.linkedin_url || '',
    phone: lead?.phone || '',
    industry: lead?.industry || '',
    company_size: lead?.company_size || '',
    location: lead?.location || ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">
          {lead ? 'Edit Lead' : 'Add New Lead'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Company *</label>
            <input
              type="text"
              value={formData.company}
              onChange={(e) => setFormData({...formData, company: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">LinkedIn URL</label>
            <input
              type="url"
              value={formData.linkedin_url}
              onChange={(e) => setFormData({...formData, linkedin_url: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Industry</label>
            <input
              type="text"
              value={formData.industry}
              onChange={(e) => setFormData({...formData, industry: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Company Size</label>
            <input
              type="text"
              value={formData.company_size}
              onChange={(e) => setFormData({...formData, company_size: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              {lead ? 'Update Lead' : 'Create Lead'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
