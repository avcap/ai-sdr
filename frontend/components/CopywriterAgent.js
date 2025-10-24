import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

export default function CopywriterAgent({ isOpen, onClose, campaigns = [], onGoBack = null }) {
  const { data: session } = useSession();
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [messageType, setMessageType] = useState('cold_email');
  const [sequenceLength, setSequenceLength] = useState(3);
  const [numVariations, setNumVariations] = useState(3);
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('personalize');
  const [userTemplate, setUserTemplate] = useState('');

  // Sample lead data for testing (in real app, this would come from campaigns)
  const sampleLeads = [
    {
      name: "Sarah Johnson",
      title: "VP of Sales",
      company: "TechCorp Solutions",
      industry: "SaaS",
      company_size: "50-200",
      location: "San Francisco, CA",
      email: "sarah.johnson@techcorp.com",
      linkedin_url: "https://linkedin.com/in/sarahjohnson",
      lead_score: { grade: "A", total_score: 85 }
    },
    {
      name: "Mike Chen",
      title: "CTO",
      company: "DataFlow Inc",
      industry: "Technology",
      company_size: "100-500",
      location: "Austin, TX",
      email: "mike.chen@dataflow.com",
      linkedin_url: "https://linkedin.com/in/mikechen",
      lead_score: { grade: "B", total_score: 78 }
    },
    {
      name: "Emily Rodriguez",
      title: "Marketing Director",
      company: "GrowthCo",
      industry: "Marketing",
      company_size: "10-50",
      location: "New York, NY",
      email: "emily@growthco.com",
      linkedin_url: "https://linkedin.com/in/emilyrodriguez",
      lead_score: { grade: "A", total_score: 92 }
    }
  ];

  const personalizeMessage = async () => {
    if (!selectedLead) {
      setError('Please select a lead');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const campaignContext = selectedCampaign ? {
        value_proposition: selectedCampaign.value_proposition,
        call_to_action: selectedCampaign.call_to_action,
        target_audience: selectedCampaign.target_audience
      } : null;

      const response = await fetch('/api/copywriter/personalize-message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          lead_data: selectedLead,
          message_type: messageType,
          campaign_context: campaignContext,
          user_template: activeTab === 'template' ? userTemplate.trim() : null
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to personalize message');
      }

      setResults({ type: 'personalize', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const createSequence = async () => {
    if (!selectedLead) {
      setError('Please select a lead');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const campaignContext = selectedCampaign ? {
        value_proposition: selectedCampaign.value_proposition,
        call_to_action: selectedCampaign.call_to_action,
        target_audience: selectedCampaign.target_audience
      } : null;

      const response = await fetch('/api/copywriter/create-sequence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          lead_data: selectedLead,
          campaign_context: campaignContext,
          sequence_length: sequenceLength
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create email sequence');
      }

      setResults({ type: 'sequence', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateVariations = async () => {
    if (!selectedLead) {
      setError('Please select a lead');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const campaignContext = selectedCampaign ? {
        value_proposition: selectedCampaign.value_proposition,
        call_to_action: selectedCampaign.call_to_action,
        target_audience: selectedCampaign.target_audience
      } : null;

      const response = await fetch('/api/copywriter/generate-variations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          lead_data: selectedLead,
          message_type: messageType,
          num_variations: numVariations,
          campaign_context: campaignContext
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate variations');
      }

      setResults({ type: 'variations', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">✍️ Copywriter Agent</h2>
            <p className="text-sm text-gray-600">AI-powered personalization and sequence creation</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Tabs */}
          <div className="flex space-x-1 mb-6">
            <button
              onClick={() => setActiveTab('personalize')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'personalize'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📝 Personalize Message
            </button>
            <button
              onClick={() => setActiveTab('template')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'template'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📋 Template Personalization
            </button>
            <button
              onClick={() => setActiveTab('sequence')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'sequence'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📧 Email Sequence
            </button>
            <button
              onClick={() => setActiveTab('variations')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'variations'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🎯 A/B Variations
            </button>
          </div>

          {/* Lead Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Lead
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {sampleLeads.map((lead, index) => (
                <div
                  key={index}
                  onClick={() => setSelectedLead(lead)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedLead?.name === lead.name
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{lead.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      lead.lead_score.grade === 'A' ? 'bg-green-100 text-green-800' :
                      lead.lead_score.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {lead.lead_score.grade}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{lead.title}</p>
                  <p className="text-sm text-gray-500">{lead.company}</p>
                  <p className="text-xs text-gray-400">{lead.industry} • {lead.location}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Campaign Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Campaign Context (Optional)
            </label>
            <select
              value={selectedCampaign?.id || ''}
              onChange={(e) => {
                const campaign = campaigns.find(c => c.id === e.target.value);
                setSelectedCampaign(campaign || null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">No campaign context</option>
              {campaigns.map((campaign) => (
                <option key={campaign.id} value={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tab Content */}
          {activeTab === 'personalize' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message Type
                </label>
                <select
                  value={messageType}
                  onChange={(e) => setMessageType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="cold_email">Cold Email</option>
                  <option value="linkedin_message">LinkedIn Message</option>
                  <option value="follow_up">Follow-up Email</option>
                </select>
              </div>

              <button
                onClick={personalizeMessage}
                disabled={isGenerating || !selectedLead}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>✍️</span>
                    <span>Generate Personalized Message</span>
                  </>
                )}
              </button>
            </div>
          )}

          {activeTab === 'template' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Email Template
                </label>
                <textarea
                  value={userTemplate}
                  onChange={(e) => setUserTemplate(e.target.value)}
                  placeholder="Paste your email template here. Use placeholders like [NAME], [COMPANY], [TITLE] for personalization..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent h-32 resize-none"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use placeholders: [NAME], [COMPANY], [TITLE], [INDUSTRY], [LOCATION] for AI personalization
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message Type
                </label>
                <select
                  value={messageType}
                  onChange={(e) => setMessageType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="cold_email">Cold Email</option>
                  <option value="linkedin_message">LinkedIn Message</option>
                  <option value="follow_up">Follow-up Email</option>
                </select>
              </div>

              <button
                onClick={personalizeMessage}
                disabled={isGenerating || !selectedLead || !userTemplate.trim()}
                className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Personalizing Template...</span>
                  </>
                ) : (
                  <>
                    <span>🎯</span>
                    <span>Personalize Template</span>
                  </>
                )}
              </button>
            </div>
          )}

          {activeTab === 'sequence' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sequence Length
                </label>
                <select
                  value={sequenceLength}
                  onChange={(e) => setSequenceLength(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={3}>3 emails</option>
                  <option value={5}>5 emails</option>
                  <option value={7}>7 emails</option>
                </select>
              </div>

              <button
                onClick={createSequence}
                disabled={isGenerating || !selectedLead}
                className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <span>📧</span>
                    <span>Create Email Sequence</span>
                  </>
                )}
              </button>
            </div>
          )}

          {activeTab === 'variations' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message Type
                  </label>
                  <select
                    value={messageType}
                    onChange={(e) => setMessageType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="cold_email">Cold Email</option>
                    <option value="linkedin_message">LinkedIn Message</option>
                    <option value="follow_up">Follow-up Email</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Variations
                  </label>
                  <select
                    value={numVariations}
                    onChange={(e) => setNumVariations(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={3}>3 variations</option>
                    <option value={5}>5 variations</option>
                    <option value={7}>7 variations</option>
                  </select>
                </div>
              </div>

              <button
                onClick={generateVariations}
                disabled={isGenerating || !selectedLead}
                className="w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>🎯</span>
                    <span>Generate A/B Variations</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Results Display */}
          {results && (
            <div className="mt-6 space-y-4">
              {results.type === 'personalize' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">
                    ✍️ Personalized Message
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium text-blue-800">Personalization Score:</span>
                      <span className="ml-2 text-blue-600">{results.data.personalization_score}/100</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-800">Message Length:</span>
                      <span className="ml-2 text-blue-600">{results.data.message_length} characters</span>
                    </div>
                    <div className="bg-white p-4 rounded border">
                      <h4 className="font-medium mb-2">Subject: {results.data.personalized_message.subject}</h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {results.data.personalized_message.body}
                      </p>
                      <button
                        onClick={() => copyToClipboard(results.data.personalized_message.body)}
                        className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
                      >
                        📋 Copy to Clipboard
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {results.type === 'sequence' && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-green-900 mb-2">
                    📧 Email Sequence ({results.data.sequence_length} emails)
                  </h3>
                  <div className="space-y-4">
                    {results.data.email_sequence.map((email, index) => (
                      <div key={index} className="bg-white p-4 rounded border">
                        <h4 className="font-medium mb-2">Email {index + 1}: {email.subject}</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                          {email.body}
                        </p>
                        <button
                          onClick={() => copyToClipboard(email.body)}
                          className="text-green-600 hover:text-green-800 text-sm"
                        >
                          📋 Copy Email {index + 1}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {results.type === 'variations' && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-purple-900 mb-2">
                    🎯 A/B Test Variations ({results.data.num_variations} variations)
                  </h3>
                  <div className="space-y-4">
                    {results.data.variations.map((variation, index) => (
                      <div key={index} className="bg-white p-4 rounded border">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">Variation {variation.variation_id}: {variation.style}</h4>
                          <span className="text-sm text-gray-500">
                            Score: {variation.personalization_score}/100
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                          {variation.personalized_message.body}
                        </p>
                        <button
                          onClick={() => copyToClipboard(variation.personalized_message.body)}
                          className="text-purple-600 hover:text-purple-800 text-sm"
                        >
                          📋 Copy Variation {variation.variation_id}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer with Go Back Button */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onGoBack || onClose}
            className="w-full bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
          >
            <span>←</span>
            <span>Go Back</span>
          </button>
        </div>
      </div>
    </div>
  );
}
