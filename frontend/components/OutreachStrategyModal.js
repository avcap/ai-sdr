import { useState } from 'react'
import { useRouter } from 'next/router'

export default function OutreachStrategyModal({ isOpen, onClose, campaignData }) {
  const router = useRouter()
  const [selectedStrategy, setSelectedStrategy] = useState('sequence')
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleContinue = async () => {
    if (selectedStrategy === 'burst') {
      // Close modal and let parent handle Smart Outreach
      onClose({ strategy: 'burst' })
    } else {
      // Create sequence from campaign
      setLoading(true)
      try {
        const response = await fetch(`/api/campaigns/${campaignData.id}/create-sequence`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer demo_token'
          }
        })

        if (response.ok) {
          const data = await response.json()
          // Redirect to sequence builder
          router.push(`/sequences/${data.sequence_id}/edit`)
        } else {
          alert('Failed to create sequence. Please try again.')
          setLoading(false)
        }
      } catch (error) {
        console.error('Error creating sequence:', error)
        alert('Error creating sequence')
        setLoading(false)
      }
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">🎉 Campaign Created Successfully!</h2>
          <p className="text-gray-600 mt-1">
            {campaignData.leads_count || 0} leads generated and ready for outreach
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Choose Your Outreach Strategy:</h3>

          {/* Option 1: Burst Email */}
          <div
            onClick={() => setSelectedStrategy('burst')}
            className={`border-2 rounded-lg p-6 mb-4 cursor-pointer transition-all ${
              selectedStrategy === 'burst'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mt-1 ${
                  selectedStrategy === 'burst'
                    ? 'border-blue-500 bg-blue-500'
                    : 'border-gray-300'
                }`}>
                  {selectedStrategy === 'burst' && (
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                  )}
                </div>
              </div>
              <div className="ml-4 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">⚡</span>
                  <h4 className="text-lg font-bold text-gray-900">One-Time Email Blast</h4>
                </div>
                <p className="text-gray-600 text-sm mb-2">
                  Send a single personalized email to all leads immediately
                </p>
                <div className="flex gap-4 text-xs text-gray-500">
                  <span>✓ Quick setup</span>
                  <span>✓ Immediate send</span>
                  <span>✓ No follow-ups</span>
                </div>
              </div>
            </div>
          </div>

          {/* Option 2: Multi-Touch Sequence */}
          <div
            onClick={() => setSelectedStrategy('sequence')}
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
              selectedStrategy === 'sequence'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mt-1 ${
                  selectedStrategy === 'sequence'
                    ? 'border-blue-500 bg-blue-500'
                    : 'border-gray-300'
                }`}>
                  {selectedStrategy === 'sequence' && (
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                  )}
                </div>
              </div>
              <div className="ml-4 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">📧</span>
                  <h4 className="text-lg font-bold text-gray-900">Multi-Touch Sequence</h4>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                    Recommended
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-2">
                  Automated follow-up emails over time with smart conditional logic
                </p>
                <div className="flex gap-4 text-xs text-gray-500 mb-3">
                  <span>✓ 3-5x higher reply rates</span>
                  <span>✓ Auto follow-ups</span>
                  <span>✓ Stop if replied</span>
                </div>
                <div className="bg-white rounded border border-blue-200 p-3">
                  <p className="text-xs text-gray-700 font-semibold mb-2">Pre-built template includes:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Day 0: Initial outreach email</li>
                    <li>• Day 2: Follow-up #1 (if no reply)</li>
                    <li>• Day 5: Follow-up #2 (if no reply)</li>
                  </ul>
                  <p className="text-xs text-blue-600 mt-2">
                    ✨ You can edit or use as-is
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div>
                <p className="text-sm text-blue-900 font-semibold mb-1">Pro Tip</p>
                <p className="text-sm text-blue-800">
                  {selectedStrategy === 'burst'
                    ? 'Burst emails are great for time-sensitive offers or one-time announcements.'
                    : 'Sequences increase reply rates by 3-5x by following up with non-responders automatically.'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t flex gap-3">
          <button
            onClick={() => onClose({ strategy: null })}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleContinue}
            className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Creating Sequence...' : 'Continue →'}
          </button>
        </div>
      </div>
    </div>
  )
}

