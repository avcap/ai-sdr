import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

export default function ProspectorAgent({ campaigns, onLeadsGenerated }) {
  const { data: session } = useSession();
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  
  // Phase 3: Adaptive features
  const [useAdaptive, setUseAdaptive] = useState(true);
  const [adaptiveMetadata, setAdaptiveMetadata] = useState(null);

  const handleGenerateLeads = async () => {
    if (!prompt.trim()) {
      alert('Please enter a prospecting prompt');
      return;
    }

    setIsGenerating(true);
    setResult(null);
    setAdaptiveMetadata(null);

    try {
      const requestBody = { 
        prompt,
        use_adaptive: useAdaptive
      };

      const response = await fetch('/api/prospector/generate-leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        
        // Phase 3: Store adaptive metadata if available
        if (useAdaptive && data.adaptive_metadata) {
          setAdaptiveMetadata(data.adaptive_metadata);
        }
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to generate leads'}`);
      }
    } catch (err) {
      console.error('Error generating leads:', err);
      alert('Failed to generate leads');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveLeads = async () => {
    if (!selectedCampaign) {
      alert('Please select a campaign');
      return;
    }

    if (!result?.leads) {
      alert('No leads to save');
      return;
    }

    setIsSaving(true);

    try {
      const response = await fetch('/api/prospector/save-leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          campaign_id: selectedCampaign,
          leads: result.leads
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
        if (onLeadsGenerated) {
          onLeadsGenerated();
        }
        // Reset form
        setResult(null);
        setPrompt('');
        setSelectedCampaign('');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to save leads'}`);
      }
    } catch (err) {
      console.error('Error saving leads:', err);
      alert('Failed to save leads');
    } finally {
      setIsSaving(false);
    }
  };

  const downloadCSV = () => {
    if (!result?.csv_content) return;

    const blob = new Blob([result.csv_content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.csv_filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🤖 AI Prospector Agent (Scout)
        </h3>
        <p className="text-gray-600 text-sm">
          Generate targeted lead lists using natural language prompts. Scout will create realistic, 
          high-quality B2B leads based on your criteria.
        </p>
        <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Demo Data Warning
              </h3>
              <div className="mt-1 text-sm text-yellow-700">
                <p>
                  Generated leads are <strong>fictional and for demonstration purposes only</strong>. 
                  LinkedIn URLs, emails, and contact information are not real. 
                  Use this tool to test your campaign structure before importing real lead data.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Prompt Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe your ideal leads:
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Find me 50 SaaS CTOs in San Francisco with 50-200 employees"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
        />
        <div className="mt-2 text-xs text-gray-500">
          💡 Examples: "25 Fintech VPs in NYC", "100 Healthcare Directors in Austin", "50 Remote Startup Founders"
        </div>
      </div>

      {/* Phase 3: Adaptive Features Toggle */}
      <div className="mb-6 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">🧠 Phase 3: Adaptive Intelligence</h3>
            <p className="text-sm text-gray-600">Enable market-aware prospecting with knowledge fusion</p>
          </div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={useAdaptive}
              onChange={(e) => setUseAdaptive(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">Enable Adaptive Mode</span>
          </label>
        </div>
        
        {useAdaptive && (
          <div className="mt-3 text-sm text-gray-600">
            <p>✨ <strong>Enhanced Features:</strong></p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Market intelligence integration</li>
              <li>Knowledge fusion from documents and prompts</li>
              <li>Adaptive strategy selection</li>
              <li>Real-time market context</li>
            </ul>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <div className="mb-6">
        <button
          onClick={handleGenerateLeads}
          disabled={isGenerating || !prompt.trim()}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? '🔄 Generating Leads...' : '🚀 Generate Leads'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="border-t pt-6">
          <div className="mb-4">
            <h4 className="text-md font-semibold text-gray-900 mb-2">
              ✅ Generated {result.lead_count} leads
            </h4>
            <div className="bg-gray-50 p-3 rounded-md text-sm">
              <div><strong>Target Role:</strong> {result.criteria.target_role}</div>
              <div><strong>Industry:</strong> {result.criteria.industry}</div>
              <div><strong>Company Size:</strong> {result.criteria.company_size}</div>
              <div><strong>Location:</strong> {result.criteria.location}</div>
            </div>
          </div>

          {/* Phase 3: Adaptive Intelligence Results */}
          {useAdaptive && adaptiveMetadata && (
            <div className="mb-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
              <h4 className="text-md font-semibold text-purple-900 mb-3">🧠 Phase 3: Adaptive Intelligence Results</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <div className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🎯</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Strategy Used</p>
                      <p className="text-xs text-gray-600 capitalize">{result.strategy_used || 'hybrid'}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">📊</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Knowledge Level</p>
                      <p className="text-xs text-gray-600 capitalize">{result.knowledge_level || 'medium'}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🎯</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Confidence Score</p>
                      <p className="text-xs text-gray-600">{Math.round((result.confidence_score || 0.7) * 100)}%</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">📈</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Market Intelligence</p>
                      <p className="text-xs text-gray-600">Enhanced</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Market Intelligence Details */}
              {result.market_intelligence && (
                <div className="bg-white rounded-lg p-3 border border-purple-200 mb-3">
                  <h5 className="font-medium text-purple-800 mb-2">📊 Market Intelligence Applied</h5>
                  <div className="text-sm text-gray-700 space-y-1">
                    {result.market_intelligence.industry_trends && (
                      <p><strong>Industry Trends:</strong> {result.market_intelligence.industry_trends.trends?.join(', ') || 'Market analysis applied'}</p>
                    )}
                    {result.market_intelligence.market_sentiment && (
                      <p><strong>Market Sentiment:</strong> {result.market_intelligence.market_sentiment.sentiment || 'Neutral'} ({Math.round((result.market_intelligence.market_sentiment.confidence || 0.5) * 100)}% confidence)</p>
                    )}
                  </div>
                </div>
              )}

              {/* Adaptive Execution Details */}
              <div className="bg-white rounded-lg p-3 border border-purple-200">
                <h5 className="font-medium text-purple-800 mb-2">⚡ Adaptive Execution Details</h5>
                <div className="text-sm text-gray-700 space-y-1">
                  <p><strong>Assessment:</strong> {adaptiveMetadata.assessment?.level || 'Medium'} knowledge level detected</p>
                  <p><strong>Strategy Plan:</strong> {adaptiveMetadata.strategy_plan?.strategy || 'Hybrid'} approach selected</p>
                  <p><strong>Execution Result:</strong> {adaptiveMetadata.execution_result?.strategy_metadata?.strategy_used || 'Adaptive'} execution completed</p>
                  {adaptiveMetadata.pipeline_performance && (
                    <p><strong>Performance:</strong> {adaptiveMetadata.pipeline_performance.total_time || 0}s execution time</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Preview of leads */}
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Preview (first 5 leads):</h5>
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-3">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    ⚠️ Demo Data - Not Real Contacts
                  </h3>
                  <div className="mt-1 text-sm text-red-700">
                    <p>
                      These are fictional leads for testing purposes. LinkedIn URLs and contact information are not real.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded-md text-xs">
              {result.leads.slice(0, 5).map((lead, index) => (
                <div key={index} className="mb-1">
                  {lead.name} - {lead.title} at {lead.company} ({lead.email})
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={downloadCSV}
              className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 transition-colors"
            >
              📥 Download CSV
            </button>

            {campaigns.length > 0 && (
              <>
                <select
                  value={selectedCampaign}
                  onChange={(e) => setSelectedCampaign(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded text-sm"
                >
                  <option value="">Select Campaign</option>
                  {campaigns.map((campaign) => (
                    <option key={campaign.id} value={campaign.id}>
                      {campaign.name}
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleSaveLeads}
                  disabled={isSaving || !selectedCampaign}
                  className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? '💾 Saving...' : '💾 Save to Campaign'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
