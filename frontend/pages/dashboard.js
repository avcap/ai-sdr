import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/router';
import Head from 'next/head';
// import GoogleSheetsImport from '../components/GoogleSheetsImport'; // REMOVED
import ProspectorAgent from '../components/ProspectorAgent';
import EnrichmentAgent from '../components/EnrichmentAgent';
import SmartCampaign from '../components/SmartCampaign';
import CopywriterAgent from '../components/CopywriterAgent';
import SmartOutreachAgent from '../components/SmartOutreachAgent';
import TrainYourTeam from '../components/TrainYourTeam';

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [campaigns, setCampaigns] = useState([]);
  const [googleStatus, setGoogleStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showGoogleConnect, setShowGoogleConnect] = useState(false);
  const [showCreateCampaign, setShowCreateCampaign] = useState(false);
  const [showUploadLeads, setShowUploadLeads] = useState(false);
  // const [showSheetsImport, setShowSheetsImport] = useState(false); // REMOVED
  const [showProspectorAgent, setShowProspectorAgent] = useState(false);
  const [showEnrichmentAgent, setShowEnrichmentAgent] = useState(false);
  const [showSmartCampaign, setShowSmartCampaign] = useState(false);
  const [showCopywriterAgent, setShowCopywriterAgent] = useState(false);
  const [showSmartOutreachAgent, setShowSmartOutreachAgent] = useState(false);
  const [smartOutreachLeads, setSmartOutreachLeads] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [showTrainYourTeam, setShowTrainYourTeam] = useState(false);

  useEffect(() => {
    if (status === 'loading') return;
    if (!session) {
      router.push('/auth/signin');
      return;
    }
    
    fetchData();
  }, [session, status]);

  // Listen for custom events from Smart Campaign
  useEffect(() => {
    const handleOpenCopywriterAgent = (event) => {
      setShowCopywriterAgent(true);
      // Store leads for the copywriter agent
      if (event.detail?.leads) {
        // You can store leads in state or pass them to the component
        console.log('Opening Copywriter Agent with leads:', event.detail.leads);
      }
    };

    const handleOpenSmartOutreachAgent = (event) => {
      setShowSmartOutreachAgent(true);
      // Store leads for the smart outreach agent
      if (event.detail?.leads) {
        setSmartOutreachLeads(event.detail.leads);
        console.log('Opening Smart Outreach Agent with leads:', event.detail.leads);
      }
    };

    window.addEventListener('openCopywriterAgent', handleOpenCopywriterAgent);
    window.addEventListener('openSmartOutreachAgent', handleOpenSmartOutreachAgent);

    return () => {
      window.removeEventListener('openCopywriterAgent', handleOpenCopywriterAgent);
      window.removeEventListener('openSmartOutreachAgent', handleOpenSmartOutreachAgent);
    };
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Starting fetchData...');
      
      // Fetch campaigns
      console.log('📡 Fetching campaigns...');
      const campaignsResponse = await fetch('/api/campaigns', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      console.log('📊 Campaigns response status:', campaignsResponse.status);
      if (campaignsResponse.ok) {
        const campaignsData = await campaignsResponse.json();
        console.log('📊 Campaigns data:', campaignsData);
        // Handle both array response and object with campaigns property
        const campaignsList = Array.isArray(campaignsData) ? campaignsData : (campaignsData.campaigns || []);
        setCampaigns(campaignsList);
        console.log('✅ Campaigns set:', campaignsList.length);
      } else {
        console.error('❌ Campaigns response not ok:', campaignsResponse.status);
      }
      
      // Fetch Google status
      console.log('📡 Fetching Google status...');
      const googleResponse = await fetch('/api/auth/google/status', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      console.log('📊 Google response status:', googleResponse.status);
      if (googleResponse.ok) {
        const googleData = await googleResponse.json();
        setGoogleStatus(googleData);
        console.log('✅ Google status set:', googleData);
      } else {
        console.error('❌ Google response not ok:', googleResponse.status);
      }
      
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('❌ Dashboard error:', err);
    } finally {
      console.log('🏁 Setting loading to false');
      setLoading(false);
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Google account? This will remove access to Gmail and Google Sheets.')) {
      return;
    }
    
    try {
      const response = await fetch('/api/auth/google/disconnect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        setGoogleStatus(null);
        await fetchData();
      } else {
        console.error('Failed to disconnect Google account');
      }
    } catch (error) {
      console.error('Error disconnecting Google account:', error);
    }
  };

  const handleGoogleConnect = async () => {
    try {
      const response = await fetch('/api/auth/google/url', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        window.location.href = data.auth_url;
      }
    } catch (err) {
      setError('Failed to initiate Google connection');
      console.error('Google connect error:', err);
    }
  };

  const handleCampaignCreated = (campaignData) => {
    console.log('Campaign created:', campaignData);
    fetchData(); // Refresh campaigns list
  };

  const handleCreateCampaign = async (campaignData) => {
    try {
      const response = await fetch('/api/campaigns', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify(campaignData)
      });
      
      if (response.ok) {
        const newCampaignData = await response.json();
        const newCampaign = newCampaignData.campaign || newCampaignData;
        setCampaigns([...campaigns, newCampaign]);
        setShowCreateCampaign(false);
      }
    } catch (err) {
      setError('Failed to create campaign');
      console.error('Create campaign error:', err);
    }
  };

  const handleUploadLeads = async (campaignId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`/api/campaigns/${campaignId}/leads/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Successfully uploaded ${result.leads_created || result.leads_added} leads`);
        setShowUploadLeads(false);
        setSelectedCampaign(null);
        setUploadFile(null);
        fetchData(); // Refresh data
      }
    } catch (err) {
      setError('Failed to upload leads');
      console.error('Upload leads error:', err);
    }
  };

  const handleExecuteCampaign = async (campaignId) => {
    try {
      const response = await fetch(`/api/campaigns/${campaignId}/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Campaign executed successfully! ${result.results.messages_sent} emails sent.`);
        fetchData(); // Refresh data
      }
    } catch (err) {
      setError('Failed to execute campaign');
      console.error('Execute campaign error:', err);
    }
  };

  const handleCreateSpreadsheet = async (title) => {
    try {
      const response = await fetch('/api/google/sheets/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({ title })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Spreadsheet created: ${result.spreadsheet_url}`);
      }
    } catch (err) {
      setError('Failed to create spreadsheet');
      console.error('Create spreadsheet error:', err);
    }
  };

  // const handleSheetsImportComplete = (result) => { // REMOVED
  //   alert(`Successfully imported ${result.leads_added || result.leads_created} leads from Google Sheets`);
  //   setShowSheetsImport(false);
  //   setSelectedCampaign(null);
  //   fetchData(); // Refresh data
  // };

  // Temporarily disable loading check to debug
  // if (status === 'loading' || loading) {
  //   console.log('🔄 Dashboard loading state:', { status, loading });
  //   return (
  //     <div className="min-h-screen bg-gray-50 flex items-center justify-center">
  //       <div className="text-center">
  //         <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
  //         <p className="mt-4 text-gray-600">Loading dashboard...</p>
  //       </div>
  //     </div>
  //   );
  // }

  // Debug session and loading state
  console.log('🔍 Dashboard render state:', { 
    status, 
    loading, 
    session: !!session, 
    campaigns: campaigns.length,
    googleStatus: !!googleStatus 
  });

  return (
    <>
      <Head>
        <title>AI SDR Dashboard</title>
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI SDR Dashboard</h1>
                <p className="text-sm text-gray-600">Welcome back, {session?.user?.email}</p>
              </div>
              <div className="flex items-center space-x-4">
                {googleStatus?.connected ? (
                  <div className="flex items-center text-green-600">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Google Connected
                  </div>
                ) : (
                  <button
                    onClick={handleGoogleConnect}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Connect Google
                  </button>
                )}
                <button
                  onClick={() => setShowCreateCampaign(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  New Campaign
                </button>
                        <button
                          onClick={() => setShowSmartCampaign(true)}
                          className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-105 shadow-lg"
                        >
                          🚀 Smart Campaign
                        </button>
                        <button
                          onClick={() => setShowCopywriterAgent(true)}
                          className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-2 rounded-lg hover:from-green-700 hover:to-teal-700 transition-all transform hover:scale-105 shadow-lg"
                        >
                          ✍️ Manual Copywriter
                        </button>
                <button
                  onClick={() => setShowTrainYourTeam(true)}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg flex items-center space-x-2"
                >
                  <span>🎓</span>
                  <span>Train Your Team</span>
                </button>
                <button
                  onClick={() => router.push('/knowledge-bank')}
                  className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-6 py-2 rounded-lg hover:from-orange-700 hover:to-red-700 transition-all transform hover:scale-105 shadow-lg flex items-center space-x-2"
                >
                  <span>📚</span>
                  <span>Knowledge Bank</span>
                </button>
                <button
                  onClick={() => signOut({ callbackUrl: '/auth/signin' })}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Google Integration Status */}
          {googleStatus && (
            <div className="mb-8 bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Google Integration</h2>
              {googleStatus.connected ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Connected Accounts:</p>
                      {googleStatus.accounts.map((account, index) => (
                        <p key={index} className="text-sm font-medium text-gray-900">{account.google_email}</p>
                      ))}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleGoogleConnect()}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        Reconnect Google
                      </button>
                      <button
                        onClick={() => handleGoogleDisconnect()}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        Disconnect
                      </button>
                      <button
                        onClick={() => handleCreateSpreadsheet(`AI SDR Campaign - ${new Date().toLocaleDateString()}`)}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        Create Spreadsheet
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-gray-600 mb-4">Connect your Google account to enable Gmail and Google Sheets integration</p>
                  <button
                    onClick={handleGoogleConnect}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Connect Google Account
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Campaigns */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Campaigns</h2>
            </div>
            <div className="p-6">
              {campaigns.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p className="text-gray-600 mb-4">No campaigns yet. Create your first campaign to get started.</p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                      onClick={() => setShowCreateCampaign(true)}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Create Campaign
                    </button>
                    <button
                      onClick={() => setShowProspectorAgent(true)}
                      className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      🤖 AI Prospector
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4">
                  {campaigns.map((campaign) => (
                    <div key={campaign.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{campaign.name}</h3>
                          <p className="text-sm text-gray-600">{campaign.description}</p>
                          <div className="flex items-center mt-2 space-x-4">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              campaign.status === 'completed' ? 'bg-green-100 text-green-800' :
                              campaign.status === 'running' ? 'bg-blue-100 text-blue-800' :
                              campaign.status === 'failed' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {campaign.status}
                            </span>
                            <span className="text-xs text-gray-500">
                              Created: {new Date(campaign.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setSelectedCampaign(campaign);
                              setShowUploadLeads(true);
                            }}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                          >
                            Upload Leads
                          </button>
                          {/* Import from Sheets button removed */}
                          <button
                            onClick={() => handleExecuteCampaign(campaign.id)}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                          >
                            Execute
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Google Sheets Import Modal - REMOVED */}
        {/* {showSheetsImport && selectedCampaign && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-bold">Import Leads from Google Sheets</h2>
                <button
                  onClick={() => setShowSheetsImport(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <GoogleSheetsImport
                  campaignId={selectedCampaign.id}
                  onImportComplete={handleSheetsImportComplete}
                />
              </div>
            </div>
          </div>
        )} */}

        {/* Create Campaign Modal */}
        {showCreateCampaign && (
          <CreateCampaignModal
            onClose={() => setShowCreateCampaign(false)}
            onCreate={handleCreateCampaign}
          />
        )}

        {/* Upload Leads Modal */}
        {showUploadLeads && selectedCampaign && (
          <UploadLeadsModal
            campaign={selectedCampaign}
            onClose={() => {
              setShowUploadLeads(false);
              setSelectedCampaign(null);
            }}
            onUpload={handleUploadLeads}
          />
        )}

        {/* Prospector Agent Modal */}
        {showProspectorAgent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-bold">🤖 AI Prospector Agent (Scout)</h2>
                <button
                  onClick={() => setShowProspectorAgent(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <ProspectorAgent
                  campaigns={campaigns}
                  onLeadsGenerated={fetchData}
                />
              </div>
            </div>
          </div>
        )}

                {/* Enrichment Agent Modal */}
                {showEnrichmentAgent && (
                  <EnrichmentAgent
                    isOpen={showEnrichmentAgent}
                    onClose={() => setShowEnrichmentAgent(false)}
                    campaigns={campaigns}
                  />
                )}

                {/* Copywriter Agent Modal */}
                {showCopywriterAgent && (
                  <CopywriterAgent
                    isOpen={showCopywriterAgent}
                    onClose={() => setShowCopywriterAgent(false)}
                    onGoBack={() => {
                      setShowCopywriterAgent(false);
                      setShowSmartCampaign(true);
                    }}
                    campaigns={campaigns}
                  />
                )}

                {/* Smart Campaign Modal */}
                {showSmartCampaign && (
                  <SmartCampaign
                    isOpen={showSmartCampaign}
                    onClose={() => setShowSmartCampaign(false)}
                    onCampaignCreated={handleCampaignCreated}
                  />
                )}

                {/* Smart Outreach Agent Modal */}
                {showSmartOutreachAgent && (
                  <SmartOutreachAgent
                    isOpen={showSmartOutreachAgent}
                    onClose={() => setShowSmartOutreachAgent(false)}
                    leads={smartOutreachLeads}
                    campaignContext={{}}
                  />
                )}

                {/* Train Your Team Modal */}
                {showTrainYourTeam && (
                  <TrainYourTeam
                    isOpen={showTrainYourTeam}
                    onClose={() => setShowTrainYourTeam(false)}
                  />
                )}
      </div>
    </>
  );
}

// Create Campaign Modal Component
function CreateCampaignModal({ onClose, onCreate }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_audience: '',
    value_proposition: '',
    call_to_action: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Create New Campaign</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Audience</label>
            <input
              type="text"
              value={formData.target_audience}
              onChange={(e) => setFormData({...formData, target_audience: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Value Proposition</label>
            <textarea
              value={formData.value_proposition}
              onChange={(e) => setFormData({...formData, value_proposition: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Call to Action</label>
            <textarea
              value={formData.call_to_action}
              onChange={(e) => setFormData({...formData, call_to_action: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Campaign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Upload Leads Modal Component
function UploadLeadsModal({ campaign, onClose, onUpload }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    try {
      await onUpload(campaign.id, file);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Leads for {campaign.name}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CSV File</label>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Supported formats: CSV, Excel (.xlsx, .xls)
            </p>
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              disabled={!file || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload Leads'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}