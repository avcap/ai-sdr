import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

export default function SmartOutreachAgent({ isOpen, onClose, leads = [], campaignContext = {} }) {
  const { data: session } = useSession();
  const [outreachPlan, setOutreachPlan] = useState(null);
  const [executionResults, setExecutionResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState('plan'); // 'plan', 'execute', 'complete'

  useEffect(() => {
    if (isOpen && leads.length > 0) {
      createOutreachPlan();
    }
  }, [isOpen, leads]);

  const createOutreachPlan = async () => {
    setLoading(true);
    setError(null);
    setStep('plan');

    try {
      const response = await fetch('/api/smart-outreach/create-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          leads,
          campaign_context: campaignContext
        })
      });

      if (response.ok) {
        const data = await response.json();
        setOutreachPlan(data.outreach_plan);
        setStep('execute');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create outreach plan');
      }
    } catch (err) {
      setError('Failed to create outreach plan');
      console.error('Outreach plan error:', err);
    } finally {
      setLoading(false);
    }
  };

  const executeOutreach = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/smart-outreach/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          outreach_plan: outreachPlan,
          campaign_id: campaignContext?.campaign_id || null,
          user_preferences: {
            send_immediately: true,
            max_daily_emails: 50,
            preferred_channels: ['email', 'linkedin']
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setExecutionResults(data.execution_results);
        setStep('complete');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to execute outreach');
      }
    } catch (err) {
      setError('Failed to execute outreach');
      console.error('Outreach execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetAgent = () => {
    setOutreachPlan(null);
    setExecutionResults(null);
    setError(null);
    setStep('plan');
  };

  const handleClose = () => {
    resetAgent();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl">🤖</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Smart Outreach Agent</h2>
              <p className="text-sm text-gray-600">AI-powered automated multi-channel outreach</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {/* Step 1: Creating Plan */}
          {step === 'plan' && (
            <div className="text-center">
              <div className="mb-6">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-600 mx-auto"></div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Creating Smart Outreach Plan</h3>
              <p className="text-gray-600 mb-4">
                Analyzing {leads.length} leads to determine optimal channels, timing, and personalization strategies...
              </p>
              {loading && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-500">• Analyzing lead characteristics</div>
                  <div className="text-sm text-gray-500">• Determining best outreach channels</div>
                  <div className="text-sm text-gray-500">• Optimizing timing and frequency</div>
                  <div className="text-sm text-gray-500">• Creating personalized sequences</div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Plan Ready */}
          {step === 'execute' && outreachPlan && (
            <div>
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-green-800 font-medium">Outreach Plan Created Successfully!</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Plan Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Plan Summary</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Leads:</span>
                      <span className="font-medium">{outreachPlan.total_leads || leads.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Channels:</span>
                      <span className="font-medium">
                        {outreachPlan.channels && typeof outreachPlan.channels === 'object' 
                          ? Object.keys(outreachPlan.channels).map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')
                          : 'Email, LinkedIn'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sequence Length:</span>
                      <span className="font-medium">{outreachPlan.sequence_length || '3 touches'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated Duration:</span>
                      <span className="font-medium">{outreachPlan.duration || '2 weeks'}</span>
                    </div>
                  </div>
                </div>

                {/* Strategy */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">AI Strategy</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>• Personalized messaging per lead</div>
                    <div>• Optimal timing based on industry</div>
                    <div>• Multi-channel approach</div>
                    <div>• Automated follow-up sequences</div>
                  </div>
                </div>
              </div>

              {/* Execute Button */}
              <div className="text-center">
                <button
                  onClick={executeOutreach}
                  disabled={loading}
                  className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-8 py-3 rounded-lg hover:from-orange-700 hover:to-red-700 transition-all transform hover:scale-105 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Executing Outreach...</span>
                    </div>
                  ) : (
                    'Execute Smart Outreach'
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Execution Complete */}
          {step === 'complete' && executionResults && (
            <div>
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-green-800 font-medium">Smart Outreach Executed Successfully!</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">{executionResults.emails_sent || 0}</div>
                  <div className="text-sm text-blue-800">Emails Sent</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">{executionResults.linkedin_messages || 0}</div>
                  <div className="text-sm text-green-800">LinkedIn Messages</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-purple-600">{executionResults.sequences_created || 0}</div>
                  <div className="text-sm text-purple-800">Sequences Created</div>
                </div>
              </div>

              <div className="text-center">
                <button
                  onClick={handleClose}
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}