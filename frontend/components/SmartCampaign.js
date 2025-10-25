import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

export default function SmartCampaign({ isOpen, onClose, onCampaignCreated }) {
  const { data: session } = useSession();
  const [prompt, setPrompt] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionProgress, setExecutionProgress] = useState({});
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Phase 3: Adaptive features
  const [useAdaptive, setUseAdaptive] = useState(true);
  const [knowledgeAssessment, setKnowledgeAssessment] = useState(null);
  const [marketIntelligence, setMarketIntelligence] = useState(null);
  const [adaptiveMetadata, setAdaptiveMetadata] = useState(null);

  const pipelineStages = [
    { id: 'prompt_analysis', name: 'Analyzing Prompt', icon: '📝' },
    { id: 'prospecting', name: 'Finding Prospects', icon: '🤖' },
    { id: 'enrichment', name: 'Enriching Data', icon: '🔍' },
    { id: 'quality_gates', name: 'Quality Gates', icon: '✅' },
    { id: 'campaign_creation', name: 'Creating Campaign', icon: '🎯' }
  ];

  // Phase 3: Get knowledge assessment on component mount
  useEffect(() => {
    if (isOpen && useAdaptive) {
      getKnowledgeAssessment();
    }
  }, [isOpen, useAdaptive]);

  const getKnowledgeAssessment = async () => {
    try {
      const response = await fetch('/api/phase3/knowledge-assessment', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setKnowledgeAssessment(data.assessment);
      }
    } catch (error) {
      console.error('Failed to get knowledge assessment:', error);
    }
  };

  const getMarketIntelligence = async (industry) => {
    try {
      const response = await fetch(`/api/phase3/market-intelligence/${industry}`, {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMarketIntelligence(data);
      }
    } catch (error) {
      console.error('Failed to get market intelligence:', error);
    }
  };

  const executeSmartCampaign = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setResults(null);
    setExecutionProgress({});
    setAdaptiveMetadata(null);

    try {
      const requestBody = { 
        prompt: prompt.trim(),
        use_adaptive: useAdaptive
      };

      const response = await fetch('/api/smart-campaign/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to execute Smart Campaign');
      }

      setResults(data);
      
      // Phase 3: Store adaptive metadata if available
      if (useAdaptive && data.adaptive_metadata) {
        setAdaptiveMetadata(data.adaptive_metadata);
      }
      
      // Simulate progress updates
      pipelineStages.forEach((stage, index) => {
        setTimeout(() => {
          setExecutionProgress(prev => ({
            ...prev,
            [stage.id]: { status: 'completed', timestamp: new Date() }
          }));
        }, (index + 1) * 1000);
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setIsExecuting(false);
    }
  };

  const saveCampaign = async () => {
    if (!results) return;

    setIsSaving(true);
    try {
      const response = await fetch('/api/smart-campaign/save-campaign', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          campaign_data: results.campaign_data,
          premium_leads: results.premium_leads,
          backup_leads: results.backup_leads,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to save campaign');
      }

      // Notify parent component
      if (onCampaignCreated) {
        onCampaignCreated(data);
      }

      // Close modal
      onClose();

    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const downloadCSV = () => {
    if (!results) return;

    const allLeads = [...results.premium_leads, ...results.backup_leads];
    
    // Create CSV headers
    const headers = [
      'Name', 'Company', 'Title', 'Email', 'Phone', 'LinkedIn URL', 
      'Industry', 'Company Size', 'Location', 'Grade', 'Score',
      'Email Valid', 'Phone Valid', 'LinkedIn Valid', 'Company Enriched',
      'Lead Status'
    ];

    // Create CSV rows
    const rows = allLeads.map(lead => [
      lead.name || '',
      lead.company || '',
      lead.title || '',
      lead.email || '',
      lead.phone || '',
      lead.linkedin_url || '',
      lead.industry || '',
      lead.company_size || '',
      lead.location || '',
      lead.lead_score?.grade || '',
      lead.lead_score?.total_score || 0,
      lead.email_validation?.valid ? 'Yes' : 'No',
      lead.phone_validation?.valid ? 'Yes' : 'No',
      lead.linkedin_validation?.valid ? 'Yes' : 'No',
      lead.company_enriched ? 'Yes' : 'No',
      lead.lead_score?.grade && ['A', 'B'].includes(lead.lead_score.grade) ? 'Premium' : 'Backup'
    ]);

    // Combine headers and rows
    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `smart_campaign_leads_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const resetForm = () => {
    setPrompt('');
    setResults(null);
    setError(null);
    setExecutionProgress({});
  };

  const getStageStatus = (stageId) => {
    if (isExecuting) {
      return executionProgress[stageId]?.status || 'pending';
    }
    return results?.stages?.[stageId]?.success ? 'completed' : 'pending';
  };

  const getStageIcon = (stage) => {
    const status = getStageStatus(stage.id);
    if (status === 'completed') return '✅';
    if (status === 'running') return '🔄';
    return stage.icon;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🚀 Smart Campaign</h2>
            <p className="text-sm text-gray-600">AI-powered prospecting pipeline</p>
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
          {!results ? (
            /* Input Phase */
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe your ideal prospects
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Find me 10 SaaS CTOs in San Francisco with 50-200 employees"
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isExecuting}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Be specific about role, industry, location, and company size for better results
                </p>
              </div>

              {/* Phase 3: Adaptive Features Toggle */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">🧠 Phase 3: Adaptive Intelligence</h3>
                    <p className="text-sm text-gray-600">Enable market-aware AI with knowledge fusion</p>
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
                
                {useAdaptive && knowledgeAssessment && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">📊</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Knowledge Level</p>
                          <p className="text-xs text-gray-600 capitalize">{knowledgeAssessment.level}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">📚</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Documents</p>
                          <p className="text-xs text-gray-600">{knowledgeAssessment.document_count}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">🎯</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Confidence</p>
                          <p className="text-xs text-gray-600">{Math.round(knowledgeAssessment.overall_confidence * 100)}%</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">{error}</p>
                </div>
              )}

              <div className="flex justify-end">
                <button
                  onClick={executeSmartCampaign}
                  disabled={isExecuting || !prompt.trim()}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isExecuting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Executing Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <span>🚀</span>
                      <span>Execute Smart Campaign</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Results Phase */
            <div className="space-y-6">
              {/* Pipeline Progress */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4">Pipeline Progress</h3>
                <div className="grid grid-cols-5 gap-4">
                  {pipelineStages.map((stage, index) => (
                    <div key={stage.id} className="text-center">
                      <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-lg ${
                        getStageStatus(stage.id) === 'completed' 
                          ? 'bg-green-100 text-green-600' 
                          : 'bg-gray-100 text-gray-400'
                      }`}>
                        {getStageIcon(stage)}
                      </div>
                      <p className="text-xs mt-2 text-gray-600">{stage.name}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Campaign Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  🎯 Campaign Ready: {results.campaign_data.name}
                </h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-800">Premium Leads:</span>
                    <span className="ml-2 text-blue-600">{results.premium_leads.length}</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-800">Backup Leads:</span>
                    <span className="ml-2 text-blue-600">{results.backup_leads.length}</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-800">Execution Time:</span>
                    <span className="ml-2 text-blue-600">{results.execution_time.toFixed(1)}s</span>
                  </div>
                </div>
              </div>

              {/* Detailed Enrichment Data */}
              {results.enrichment_stats && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">🔍 Enrichment Details</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-blue-800">Email Valid:</span>
                      <span className="ml-2 text-blue-600">{results.enrichment_stats.email_valid || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-800">Phone Valid:</span>
                      <span className="ml-2 text-blue-600">{results.enrichment_stats.phone_valid || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-800">LinkedIn Valid:</span>
                      <span className="ml-2 text-blue-600">{results.enrichment_stats.linkedin_valid || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-800">Company Enriched:</span>
                      <span className="ml-2 text-blue-600">{results.enrichment_stats.company_enriched || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Quality Gates Breakdown */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-900 mb-2">✅ Quality Gates Analysis</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-800">Premium Leads (A-B Grade):</span>
                    <span className="font-medium text-green-600">{results.premium_leads.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-800">Backup Leads (C-D Grade):</span>
                    <span className="font-medium text-green-600">{results.backup_leads.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-800">Excluded Leads (F Grade):</span>
                    <span className="font-medium text-green-600">{results.excluded_leads?.length || 0}</span>
                  </div>
                </div>
              </div>

              {/* Phase 3: Adaptive Intelligence Results */}
              {useAdaptive && adaptiveMetadata && (
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-purple-900 mb-4">🧠 Phase 3: Adaptive Intelligence Results</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="bg-white rounded-lg p-3 border border-purple-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">🎯</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Strategy Used</p>
                          <p className="text-xs text-gray-600 capitalize">{results.strategy_used || 'hybrid'}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-purple-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">📊</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Knowledge Level</p>
                          <p className="text-xs text-gray-600 capitalize">{results.knowledge_level || 'medium'}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-purple-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">🎯</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Confidence Score</p>
                          <p className="text-xs text-gray-600">{Math.round((results.confidence_score || 0.7) * 100)}%</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-purple-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">📈</span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">Market Intelligence</p>
                          <p className="text-xs text-gray-600">Enhanced</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Market Intelligence Details */}
                  {results.market_intelligence && (
                    <div className="bg-white rounded-lg p-4 border border-purple-200">
                      <h4 className="font-medium text-purple-800 mb-2">📊 Market Intelligence Applied</h4>
                      <div className="text-sm text-gray-700 space-y-1">
                        {results.market_intelligence.industry_trends && (
                          <p><strong>Industry Trends:</strong> {results.market_intelligence.industry_trends.trends?.join(', ') || 'Market analysis applied'}</p>
                        )}
                        {results.market_intelligence.market_sentiment && (
                          <p><strong>Market Sentiment:</strong> {results.market_intelligence.market_sentiment.sentiment || 'Neutral'} ({Math.round((results.market_intelligence.market_sentiment.confidence || 0.5) * 100)}% confidence)</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Adaptive Execution Details */}
                  <div className="bg-white rounded-lg p-4 border border-purple-200 mt-4">
                    <h4 className="font-medium text-purple-800 mb-2">⚡ Adaptive Execution Details</h4>
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

              {/* Detailed Lead Data Table */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold">📊 Detailed Lead Data</h3>
                  <button
                    onClick={() => downloadCSV()}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                  >
                    📥 Download CSV
                  </button>
                </div>
                
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LinkedIn</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {[...results.premium_leads, ...results.backup_leads].map((lead, index) => (
                          <tr key={index} className={index < results.premium_leads.length ? 'bg-green-50' : 'bg-orange-50'}>
                            <td className="px-4 py-3 text-sm font-medium text-gray-900">{lead.name}</td>
                            <td className="px-4 py-3 text-sm text-gray-900">{lead.company}</td>
                            <td className="px-4 py-3 text-sm text-gray-900">{lead.title}</td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <div className="flex items-center">
                                {lead.email}
                                {lead.email_validation?.valid ? (
                                  <span className="ml-1 text-green-500">✓</span>
                                ) : (
                                  <span className="ml-1 text-red-500">✗</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <div className="flex items-center">
                                {lead.phone || 'N/A'}
                                {lead.phone_validation?.valid ? (
                                  <span className="ml-1 text-green-500">✓</span>
                                ) : (
                                  <span className="ml-1 text-red-500">✗</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <div className="flex items-center">
                                {lead.linkedin_url ? (
                                  <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                                    LinkedIn
                                  </a>
                                ) : (
                                  'N/A'
                                )}
                                {lead.linkedin_validation?.valid ? (
                                  <span className="ml-1 text-green-500">✓</span>
                                ) : (
                                  <span className="ml-1 text-red-500">✗</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                lead.lead_score?.grade === 'A' ? 'bg-green-100 text-green-800' :
                                lead.lead_score?.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                                lead.lead_score?.grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                                lead.lead_score?.grade === 'D' ? 'bg-orange-100 text-orange-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {lead.lead_score?.grade || 'N/A'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">{lead.lead_score?.total_score || 0}/100</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Copywriter Integration */}
              <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">✍️ Ready for Personalized Outreach?</h3>
                  <p className="text-gray-600 mb-4">
                    Your leads are ready! Choose how you'd like to proceed with outreach:
                  </p>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={() => {
                        // This will be handled by the parent component
                        if (onClose) onClose();
                        // Trigger copywriter agent with these leads
                        window.dispatchEvent(new CustomEvent('openCopywriterAgent', {
                          detail: { leads: [...results.premium_leads, ...results.backup_leads] }
                        }));
                      }}
                      className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-teal-700 transition-all transform hover:scale-105 shadow-lg flex items-center space-x-2"
                    >
                      <span>✍️</span>
                      <span>Manual Copywriter</span>
                    </button>
                    <button
                      onClick={() => {
                        // This will be handled by the parent component
                        if (onClose) onClose();
                        // Trigger smart outreach agent with these leads
                        window.dispatchEvent(new CustomEvent('openSmartOutreachAgent', {
                          detail: { leads: [...results.premium_leads, ...results.backup_leads] }
                        }));
                      }}
                      className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-6 py-3 rounded-lg hover:from-orange-700 hover:to-red-700 transition-all transform hover:scale-105 shadow-lg flex items-center space-x-2"
                    >
                      <span>🤖</span>
                      <span>Smart Outreach</span>
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-3">
                    Manual Outreach: You provide templates, AI personalizes with names/companies<br/>
                    Smart Outreach: AI generates data-driven outreach automatically with proven strategies
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-between">
                <button
                  onClick={resetForm}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                >
                  Start New Campaign
                </button>
                <button
                  onClick={saveCampaign}
                  disabled={isSaving}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isSaving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span>💾</span>
                      <span>Save Campaign</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
