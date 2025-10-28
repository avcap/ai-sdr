import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import ScheduleSequenceModal from '../../../components/ScheduleSequenceModal'
import SequenceExecutionDashboard from '../../../components/SequenceExecutionDashboard'

export default function SequenceEditorPage() {
  const router = useRouter()
  const { sequenceId } = router.query

  const [sequence, setSequence] = useState(null)
  const [steps, setSteps] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingStep, setEditingStep] = useState(null)
  const [showAddStep, setShowAddStep] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [enrolledLeads, setEnrolledLeads] = useState(0)
  const [showExecutionDashboard, setShowExecutionDashboard] = useState(false)

  useEffect(() => {
    if (sequenceId) {
      fetchSequence()
      fetchSteps()
    }
  }, [sequenceId])

  const fetchSequence = async () => {
    try {
      const response = await fetch(`/api/sequences/${sequenceId}`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const data = await response.json()
      setSequence(data)
      
      // Auto-show execution dashboard if sequence is active
      if (data.status === 'active') {
        setShowExecutionDashboard(true)
      }
      
      // Fetch enrollment count
      const enrollResponse = await fetch(`/api/sequences/${sequenceId}/enrollments`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      if (enrollResponse.ok) {
        const enrollData = await enrollResponse.json()
        setEnrolledLeads(enrollData.length || 0)
      }
    } catch (error) {
      console.error('Error fetching sequence:', error)
    }
  }

  const fetchSteps = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/sequences/${sequenceId}/steps`, {
        headers: { 'Authorization': 'Bearer demo_token' }
      })
      const data = await response.json()
      setSteps(data)
    } catch (error) {
      console.error('Error fetching steps:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateSequence = async (updates) => {
    try {
      const response = await fetch(`/api/sequences/${sequenceId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(updates)
      })

      if (response.ok) {
        const data = await response.json()
        setSequence(data)
        return true
      }
      return false
    } catch (error) {
      console.error('Error updating sequence:', error)
      return false
    }
  }

  const createStep = async (stepData) => {
    try {
      setSaving(true)
      const response = await fetch(`/api/sequences/${sequenceId}/steps`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(stepData)
      })

      if (response.ok) {
        await fetchSteps()
        setShowAddStep(false)
        return true
      }
      return false
    } catch (error) {
      console.error('Error creating step:', error)
      return false
    } finally {
      setSaving(false)
    }
  }

  const updateStep = async (stepId, stepData) => {
    try {
      setSaving(true)
      const response = await fetch(`/api/sequences/${sequenceId}/steps/${stepId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(stepData)
      })

      if (response.ok) {
        await fetchSteps()
        setEditingStep(null)
        return true
      }
      return false
    } catch (error) {
      console.error('Error updating step:', error)
      return false
    } finally {
      setSaving(false)
    }
  }

  const deleteStep = async (stepId) => {
    if (!confirm('Delete this step?')) return

    try {
      const response = await fetch(`/api/sequences/${sequenceId}/steps/${stepId}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer demo_token' }
      })

      if (response.ok) {
        await fetchSteps()
      }
    } catch (error) {
      console.error('Error deleting step:', error)
    }
  }

  const activateSequence = async () => {
    if (steps.length === 0) {
      alert('Add at least one step before activating')
      return
    }

    if (enrolledLeads === 0) {
      alert('No leads enrolled in this sequence')
      return
    }

    // Show scheduling modal
    setShowScheduleModal(true)
  }

  const handleScheduleConfirm = async (scheduledStartAt) => {
    try {
      setSaving(true)
      
      // Build request body - only include scheduled_start_at if it's defined
      const requestBody = {}
      if (scheduledStartAt) {
        requestBody.scheduled_start_at = scheduledStartAt
      }
      
      const response = await fetch(`/api/sequences/${sequenceId}/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo_token'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const data = await response.json()
        alert(data.message || 'Sequence activated successfully!')
        setShowScheduleModal(false)
        await fetchSequence() // Refresh sequence data
      } else {
        alert('Failed to activate sequence')
      }
    } catch (error) {
      console.error('Error activating sequence:', error)
      alert('Error activating sequence')
    } finally {
      setSaving(false)
    }
  }

  const pauseSequence = async () => {
    const success = await updateSequence({ status: 'paused' })
    if (success) {
      alert('Sequence paused')
    }
  }

  if (loading && !sequence) {
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
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <Link href="/sequences" className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block">
                ← Back to Sequences
              </Link>
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold text-gray-900">{sequence?.name || 'Loading...'}</h1>
                {sequence && (
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    sequence.status === 'active' ? 'bg-green-100 text-green-800' :
                    sequence.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {sequence.status.charAt(0).toUpperCase() + sequence.status.slice(1)}
                  </span>
                )}
              </div>
              {sequence?.description && (
                <p className="text-gray-600 text-sm mt-1">{sequence.description}</p>
              )}
              {sequence?.campaign_id && (
                <Link href={`/campaigns/${sequence.campaign_id}`} className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-flex items-center gap-1">
                  📊 View linked campaign →
                </Link>
              )}
            </div>
            <div className="flex gap-3">
              {sequence?.status === 'draft' && (
                <button
                  onClick={activateSequence}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
                >
                  ✅ Activate Sequence
                </button>
              )}
              {sequence?.status === 'active' && (
                <button
                  onClick={pauseSequence}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-lg font-semibold hover:bg-yellow-700"
                >
                  ⏸️ Pause Sequence
                </button>
              )}
              {sequence?.status === 'paused' && (
                <button
                  onClick={() => updateSequence({ status: 'active' })}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
                >
                  ▶️ Resume Sequence
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Execution Dashboard - Show when sequence is active */}
        {showExecutionDashboard && (
          <div className="mb-6">
            <SequenceExecutionDashboard 
              sequenceId={sequenceId} 
              isActive={sequence?.status === 'active'}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Column - Steps */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-gray-900">Sequence Steps</h2>
                  <button
                    onClick={() => setShowAddStep(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
                    disabled={sequence?.status === 'active'}
                  >
                    + Add Step
                  </button>
                </div>
              </div>

              <div className="p-6">
                {steps.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📧</div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">No Steps Yet</h3>
                    <p className="text-gray-600 mb-4">Add your first step to start building your sequence</p>
                    <button
                      onClick={() => setShowAddStep(true)}
                      className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
                    >
                      + Add First Step
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {steps.map((step, index) => (
                      <div key={step.id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors">
                        <div className="flex items-start gap-4">
                          {/* Step Number */}
                          <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                            {step.step_order}
                          </div>

                          {/* Step Content */}
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-semibold text-gray-500 uppercase">
                                {step.step_type === 'email' && '📧 Email'}
                                {step.step_type === 'delay' && '⏱️ Delay'}
                                {step.step_type === 'condition' && '🔀 Condition'}
                                {step.step_type === 'action' && '⚡ Action'}
                              </span>
                            </div>

                            <h4 className="font-semibold text-gray-900 mb-1">{step.name}</h4>

                            {step.step_type === 'email' && (
                              <div className="text-sm text-gray-600">
                                <p><strong>Subject:</strong> {step.subject_line || 'No subject'}</p>
                                <p className="line-clamp-2 mt-1">{step.body_text || 'No content'}</p>
                              </div>
                            )}

                            {step.step_type === 'delay' && (
                              <p className="text-sm text-gray-600">
                                Wait {step.delay_days || 0} days {step.delay_hours || 0} hours
                              </p>
                            )}

                            {step.step_type === 'condition' && (
                              <p className="text-sm text-gray-600">
                                If {step.condition_type?.replace('_', ' ') || 'condition'}
                              </p>
                            )}

                            {step.step_type === 'action' && (
                              <p className="text-sm text-gray-600">
                                {step.action_type?.replace('_', ' ') || 'action'}
                              </p>
                            )}

                            {(step.delay_days > 0 || step.delay_hours > 0) && step.step_type === 'email' && (
                              <p className="text-xs text-gray-500 mt-2">
                                ⏱️ Delay: {step.delay_days}d {step.delay_hours}h
                              </p>
                            )}
                          </div>

                          {/* Actions */}
                          <div className="flex gap-2">
                            <button
                              onClick={() => setEditingStep(step)}
                              className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                              disabled={sequence?.status === 'active'}
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => deleteStep(step.id)}
                              className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                              disabled={sequence?.status === 'active'}
                            >
                              Delete
                            </button>
                          </div>
                        </div>

                        {/* Connector */}
                        {index < steps.length - 1 && (
                          <div className="flex items-center justify-center mt-4">
                            <div className="w-px h-6 bg-gray-300"></div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - Info */}
          <div className="space-y-6">
            {/* Stats */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-bold text-gray-900 mb-4">Sequence Stats</h3>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Total Steps</div>
                  <div className="text-2xl font-bold text-gray-900">{steps.length}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Enrolled Leads</div>
                  <div className="text-2xl font-bold text-blue-600">{sequence?.total_enrolled || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Completed</div>
                  <div className="text-2xl font-bold text-green-600">{sequence?.total_completed || 0}</div>
                </div>
              </div>
            </div>

            {/* Help */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-bold text-blue-900 mb-2">💡 Tips</h3>
              <ul className="text-sm text-blue-800 space-y-2">
                <li>• Start with an email step</li>
                <li>• Add delays between emails</li>
                <li>• Use conditions to branch logic</li>
                <li>• Test before activating</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Add/Edit Step Modal */}
      {(showAddStep || editingStep) && (
        <StepEditorModal
          step={editingStep}
          stepOrder={steps.length + 1}
          onSave={(stepData) => {
            if (editingStep) {
              updateStep(editingStep.id, stepData)
            } else {
              createStep(stepData)
            }
          }}
          onClose={() => {
            setShowAddStep(false)
            setEditingStep(null)
          }}
          saving={saving}
        />
      )}

      {/* Scheduling Modal */}
      {showScheduleModal && (
        <ScheduleSequenceModal
          sequenceName={sequence?.name || ''}
          enrolledLeads={enrolledLeads}
          onConfirm={handleScheduleConfirm}
          onCancel={() => setShowScheduleModal(false)}
        />
      )}
    </div>
  )
}

// Step Editor Modal Component
function StepEditorModal({ step, stepOrder, onSave, onClose, saving }) {
  const [stepData, setStepData] = useState(step || {
    step_order: stepOrder,
    name: '',
    step_type: 'email',
    subject_line: '',
    body_text: '',
    delay_days: 0,
    delay_hours: 0,
    condition_type: 'if_replied',
    action_type: 'update_status'
  })

  const handleSave = () => {
    if (!stepData.name.trim()) {
      alert('Please enter a step name')
      return
    }

    if (stepData.step_type === 'email' && !stepData.subject_line.trim()) {
      alert('Please enter an email subject')
      return
    }

    onSave(stepData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b sticky top-0 bg-white">
          <h2 className="text-xl font-bold text-gray-900">
            {step ? 'Edit Step' : 'Add New Step'}
          </h2>
        </div>

        <div className="p-6 space-y-4">
          {/* Step Type */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Step Type *
            </label>
            <select
              value={stepData.step_type}
              onChange={(e) => setStepData({...stepData, step_type: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="email">📧 Email</option>
              <option value="delay">⏱️ Delay</option>
              <option value="condition">🔀 Condition</option>
              <option value="action">⚡ Action</option>
            </select>
          </div>

          {/* Step Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Step Name *
            </label>
            <input
              type="text"
              value={stepData.name}
              onChange={(e) => setStepData({...stepData, name: e.target.value})}
              placeholder="e.g., Initial Outreach Email"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Email Fields */}
          {stepData.step_type === 'email' && (
            <>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Subject Line *
                </label>
                <input
                  type="text"
                  value={stepData.subject_line}
                  onChange={(e) => setStepData({...stepData, subject_line: e.target.value})}
                  placeholder="Use {{name}}, {{company}} for personalization"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Body *
                </label>
                <textarea
                  value={stepData.body_text}
                  onChange={(e) => setStepData({...stepData, body_text: e.target.value})}
                  placeholder="Hi {{name}},&#10;&#10;I noticed that {{company}}..."
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use {`{{name}}, {{company}}, {{title}}`} for personalization
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Delay (Days)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={stepData.delay_days}
                    onChange={(e) => setStepData({...stepData, delay_days: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Delay (Hours)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={stepData.delay_hours}
                    onChange={(e) => setStepData({...stepData, delay_hours: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </>
          )}

          {/* Delay Fields */}
          {stepData.step_type === 'delay' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Days *
                </label>
                <input
                  type="number"
                  min="0"
                  value={stepData.delay_days}
                  onChange={(e) => setStepData({...stepData, delay_days: parseInt(e.target.value) || 0})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Hours
                </label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={stepData.delay_hours}
                  onChange={(e) => setStepData({...stepData, delay_hours: parseInt(e.target.value) || 0})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* Condition Fields */}
          {stepData.step_type === 'condition' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Condition Type *
              </label>
              <select
                value={stepData.condition_type}
                onChange={(e) => setStepData({...stepData, condition_type: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="if_replied">If Replied</option>
                <option value="if_not_replied">If Not Replied</option>
                <option value="if_opened">If Opened</option>
                <option value="if_not_opened">If Not Opened</option>
                <option value="if_clicked">If Clicked</option>
              </select>
            </div>
          )}

          {/* Action Fields */}
          {stepData.step_type === 'action' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Action Type *
              </label>
              <select
                value={stepData.action_type}
                onChange={(e) => setStepData({...stepData, action_type: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="update_status">Update Lead Status</option>
                <option value="mark_qualified">Mark as Qualified</option>
                <option value="tag_lead">Add Tag</option>
                <option value="notify_user">Notify User</option>
              </select>
            </div>
          )}
        </div>

        <div className="p-6 border-t flex gap-3 sticky bottom-0 bg-white">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
            disabled={saving}
          >
            {saving ? 'Saving...' : (step ? 'Update Step' : 'Add Step')}
          </button>
        </div>
      </div>
    </div>
  )
}

