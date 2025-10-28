import { useState } from 'react'

export default function ScheduleSequenceModal({ sequenceName, enrolledLeads, onConfirm, onCancel }) {
  const [scheduleType, setScheduleType] = useState('immediate')
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('09:00')

  const handleActivate = () => {
    if (scheduleType === 'immediate') {
      onConfirm(undefined) // No scheduled time - use undefined to not send the field
    } else {
      // Combine date and time into ISO timestamp
      const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`)
      onConfirm(scheduledDateTime.toISOString())
    }
  }

  const getMinDate = () => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }

  const isValid = scheduleType === 'immediate' || (scheduleType === 'scheduled' && scheduledDate && scheduledTime)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-2">🚀 Activate Sequence</h2>
        <p className="text-gray-600 mb-6">{sequenceName}</p>
        
        {/* Debug info - remove later */}
        {process.env.NODE_ENV === 'development' && (
          <div className="text-xs text-gray-500 mb-2">
            Debug: type={scheduleType}, date={scheduledDate}, time={scheduledTime}, valid={isValid ? 'yes' : 'no'}
          </div>
        )}

        <div className="space-y-4 mb-6">
          {/* Immediate Option */}
          <div
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              scheduleType === 'immediate'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
            onClick={() => setScheduleType('immediate')}
          >
            <div className="flex items-center gap-3">
              <input
                type="radio"
                name="scheduleType"
                value="immediate"
                checked={scheduleType === 'immediate'}
                onChange={() => setScheduleType('immediate')}
                className="w-4 h-4"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">⚡ Start Immediately</div>
                <div className="text-sm text-gray-600">
                  Begin sending emails right away
                </div>
              </div>
            </div>
          </div>

          {/* Scheduled Option */}
          <div
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              scheduleType === 'scheduled'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
            onClick={() => setScheduleType('scheduled')}
          >
            <div className="flex items-center gap-3">
              <input
                type="radio"
                name="scheduleType"
                value="scheduled"
                checked={scheduleType === 'scheduled'}
                onChange={() => setScheduleType('scheduled')}
                className="w-4 h-4"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">📅 Schedule for Later</div>
                <div className="text-sm text-gray-600 mb-3">
                  Choose when to start the sequence
                </div>

                {scheduleType === 'scheduled' && (
                  <div className="space-y-3 mt-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Date
                      </label>
                      <input
                        type="date"
                        value={scheduledDate}
                        onChange={(e) => setScheduledDate(e.target.value)}
                        min={getMinDate()}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Time
                      </label>
                      <input
                        type="time"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>

                    {scheduledDate && scheduledTime && (
                      <div className="text-sm text-gray-600 bg-blue-50 p-2 rounded">
                        ⏰ First emails will send on{' '}
                        <strong>
                          {new Date(`${scheduledDate}T${scheduledTime}`).toLocaleString(
                            'en-US',
                            {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                              hour: 'numeric',
                              minute: '2-digit',
                            }
                          )}
                        </strong>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gray-50 rounded-lg p-3 mb-6">
          <div className="text-sm text-gray-600">
            ✅ <strong>{enrolledLeads}</strong> leads will be enrolled
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleActivate}
            disabled={!isValid}
            className={`flex-1 px-4 py-2 rounded-lg font-medium ${
              isValid
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Activate Sequence →
          </button>
        </div>
      </div>
    </div>
  )
}

