import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

export default function EnrichmentAgent({ isOpen, onClose, campaigns, onLeadsEnriched }) {
  const { data: session } = useSession();
  const [leads, setLeads] = useState([]);
  const [enrichedLeads, setEnrichedLeads] = useState([]);
  const [enrichmentStats, setEnrichmentStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [csvContent, setCsvContent] = useState('');
  const [csvFilename, setCsvFilename] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [agentInfo, setAgentInfo] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchAgentInfo();
    }
  }, [isOpen]);

  const fetchAgentInfo = async () => {
    try {
      const response = await fetch('/api/enrichment/agent-info', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgentInfo(data.agent);
      }
    } catch (err) {
      console.error('Failed to fetch agent info:', err);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target.result;
        const lines = csv.split('\n');
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        
        const leadsData = lines.slice(1)
          .filter(line => line.trim())
          .map(line => {
            const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
            const lead = {};
            headers.forEach((header, index) => {
              lead[header] = values[index] || '';
            });
            return lead;
          });

        setLeads(leadsData);
        setError(null);
      } catch (err) {
        setError('Failed to parse CSV file. Please check the format.');
      }
    };
    reader.readAsText(file);
  };

  const handleManualInput = () => {
    const sampleLeads = [
      {
        name: "John Smith",
        company: "TechCorp",
        title: "CTO",
        email: "john@techcorp.com",
        phone: "555-123-4567",
        linkedin_url: "https://linkedin.com/in/john-smith-cto"
      },
      {
        name: "Jane Doe",
        company: "StartupXYZ",
        title: "VP Engineering",
        email: "jane@startupxyz.com",
        phone: "5559876543",
        linkedin_url: "https://linkedin.com/in/jane-doe"
      },
      {
        name: "Mike Johnson",
        company: "Enterprise Solutions",
        title: "Director of IT",
        email: "mike@enterprise.com",
        phone: "555-555-5555",
        linkedin_url: "https://linkedin.com/in/mike-johnson"
      }
    ];
    setLeads(sampleLeads);
    setError(null);
  };

  const handleEnrichLeads = async () => {
    if (leads.length === 0) {
      setError('Please upload leads or use sample data first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/enrichment/validate-leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({ leads })
      });

      const data = await response.json();

      if (data.success) {
        setEnrichedLeads(data.enriched_leads);
        setEnrichmentStats(data.stats);
        setCsvContent(data.csv_content);
        setCsvFilename(data.csv_filename);
        setShowResults(true);
      } else {
        setError(data.error || 'Failed to enrich leads');
      }
    } catch (err) {
      setError('Failed to enrich leads. Please try again.');
      console.error('Enrichment error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToCampaign = async () => {
    if (!selectedCampaign) {
      setError('Please select a campaign to save enriched leads');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/enrichment/save-enriched-leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          campaign_id: selectedCampaign,
          enriched_leads: enrichedLeads
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`Successfully saved ${data.leads_created} enriched leads to campaign!`);
        onLeadsEnriched && onLeadsEnriched();
        onClose();
      } else {
        setError(data.error || 'Failed to save enriched leads');
      }
    } catch (err) {
      setError('Failed to save enriched leads. Please try again.');
      console.error('Save error:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = csvFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const getScoreColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-600 bg-green-100';
      case 'B': return 'text-blue-600 bg-blue-100';
      case 'C': return 'text-yellow-600 bg-yellow-100';
      case 'D': return 'text-orange-600 bg-orange-100';
      case 'F': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getValidationIcon = (valid) => {
    return valid ? (
      <span className="text-green-500">✓</span>
    ) : (
      <span className="text-red-500">✗</span>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🔍 AI Enrichment Agent</h2>
            <p className="text-gray-600 mt-1">Validate, enrich, and score lead data quality</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {agentInfo && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">{agentInfo.name}</h3>
              <p className="text-blue-800 text-sm mb-2">{agentInfo.description}</p>
              <div className="text-blue-700 text-sm">
                <strong>Capabilities:</strong> {agentInfo.capabilities.join(', ')}
              </div>
            </div>
          )}

          {!showResults ? (
            <div className="space-y-6">
              {/* Input Section */}
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">📊 Lead Data Input</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Upload CSV File
                    </label>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileUpload}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>
                  
                  <div className="flex items-end">
                    <button
                      onClick={handleManualInput}
                      className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium"
                    >
                      Use Sample Data
                    </button>
                  </div>
                </div>

                {leads.length > 0 && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-green-800 text-sm">
                      ✓ Loaded {leads.length} leads for enrichment
                    </p>
                    <div className="mt-2 text-xs text-green-700">
                      Preview: {leads.slice(0, 2).map(lead => `${lead.name} (${lead.company})`).join(', ')}
                      {leads.length > 2 && ` and ${leads.length - 2} more...`}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center">
                <button
                  onClick={handleEnrichLeads}
                  disabled={loading || leads.length === 0}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-8 py-3 rounded-lg font-semibold text-lg"
                >
                  {loading ? 'Enriching Leads...' : '🔍 Enrich & Validate Leads'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Results Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">{enrichmentStats?.total_leads}</div>
                  <div className="text-sm text-blue-800">Total Leads</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">{enrichmentStats?.valid_emails}</div>
                  <div className="text-sm text-green-800">Valid Emails</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">{enrichmentStats?.valid_linkedin}</div>
                  <div className="text-sm text-purple-800">Valid LinkedIn</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-yellow-600">{enrichmentStats?.high_quality_leads}</div>
                  <div className="text-sm text-yellow-800">High Quality</div>
                </div>
              </div>

              {/* Quality Stats */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">📈 Quality Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Success Rate:</span> {enrichmentStats?.success_rate}%
                  </div>
                  <div>
                    <span className="font-medium">Email Validity:</span> {enrichmentStats?.email_validity_rate}%
                  </div>
                  <div>
                    <span className="font-medium">High Quality Rate:</span> {enrichmentStats?.high_quality_rate}%
                  </div>
                </div>
              </div>

              {/* Lead Results Table */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <h3 className="font-semibold">📋 Enriched Leads Preview</h3>
                </div>
                <div className="overflow-x-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-3 py-2 text-left">Name</th>
                        <th className="px-3 py-2 text-left">Company</th>
                        <th className="px-3 py-2 text-left">Email</th>
                        <th className="px-3 py-2 text-left">Score</th>
                        <th className="px-3 py-2 text-left">Validation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {enrichedLeads.slice(0, 10).map((lead, index) => (
                        <tr key={index} className="border-b hover:bg-gray-50">
                          <td className="px-3 py-2">{lead.name}</td>
                          <td className="px-3 py-2">{lead.company}</td>
                          <td className="px-3 py-2">{lead.email}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getScoreColor(lead.lead_score?.grade)}`}>
                              {lead.lead_score?.grade} ({lead.lead_score?.total_score})
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex space-x-2">
                              {getValidationIcon(lead.email_validation?.valid)}
                              {getValidationIcon(lead.phone_validation?.valid)}
                              {getValidationIcon(lead.linkedin_validation?.valid)}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {enrichedLeads.length > 10 && (
                    <div className="px-4 py-2 text-sm text-gray-500 text-center">
                      Showing 10 of {enrichedLeads.length} leads
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between items-center">
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowResults(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    ← Back to Input
                  </button>
                  <button
                    onClick={downloadCSV}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    📥 Download CSV
                  </button>
                </div>

                <div className="flex space-x-3">
                  <select
                    value={selectedCampaign}
                    onChange={(e) => setSelectedCampaign(e.target.value)}
                    className="border rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="">Select Campaign</option>
                    {campaigns.map(campaign => (
                      <option key={campaign.id} value={campaign.id}>
                        {campaign.name}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleSaveToCampaign}
                    disabled={loading || !selectedCampaign}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg text-sm font-medium"
                  >
                    {loading ? 'Saving...' : '💾 Save to Campaign'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


