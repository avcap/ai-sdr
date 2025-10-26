import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function KnowledgeBank() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [documents, setDocuments] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAddWebsiteModal, setShowAddWebsiteModal] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const categories = [
    { id: 'all', name: 'All Documents', icon: '📚' },
    { id: 'company_info', name: 'Company Info', icon: '🏢' },
    { id: 'sales_training', name: 'Sales Training', icon: '🎓' },
    { id: 'products', name: 'Products', icon: '📦' },
    { id: 'industry_knowledge', name: 'Industry Knowledge', icon: '🏭' },
    { id: 'websites', name: 'Websites', icon: '🌐' }
  ];

  useEffect(() => {
    if (status === 'loading') return;
    if (!session) {
      router.push('/auth/signin');
      return;
    }
    
    fetchKnowledgeBank();
  }, [session, status]);

  const fetchKnowledgeBank = async () => {
    try {
      setLoading(true);
      
      // Fetch documents and knowledge
      const [documentsResponse, knowledgeResponse] = await Promise.all([
        fetch('/api/knowledge-bank/documents', {
          headers: {
            'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
          }
        }),
        fetch('/api/knowledge-bank/knowledge', {
          headers: {
            'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
          }
        })
      ]);

      if (documentsResponse.ok) {
        const documentsData = await documentsResponse.json();
        setDocuments(documentsData.documents || []);
      }

      if (knowledgeResponse.ok) {
        const knowledgeData = await knowledgeResponse.json();
        setKnowledge(knowledgeData.knowledge || []);
      }
      
    } catch (err) {
      setError('Failed to load knowledge bank');
      console.error('Knowledge bank error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId, documentType) => {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      return;
    }

    try {
      setDeletingId(documentId);
      
      // Use the correct endpoint based on document type
      const endpoint = documentType === 'document' 
        ? `/api/knowledge-bank/documents/${documentId}`
        : `/api/knowledge-bank/knowledge/${documentId}`;
      
      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });

      if (response.ok) {
        // Remove from state
        if (documentType === 'document') {
          setDocuments(docs => docs.filter(doc => doc.id !== documentId));
        } else {
          setKnowledge(knowledge => knowledge.filter(k => k.id !== documentId));
        }
      } else {
        const errorData = await response.json();
        alert(`Failed to delete document: ${errorData.error}`);
      }
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete document');
    } finally {
      setDeletingId(null);
    }
  };

  const handleUploadComplete = () => {
    setShowUploadModal(false);
    fetchKnowledgeBank(); // Refresh data
    
    // Trigger campaign suggestion regeneration
    regenerateCampaignSuggestions();
  };

  const regenerateCampaignSuggestions = async () => {
    try {
      await fetch('/api/campaign-intelligence/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({})
      });
      
      // Show notification
      setError('✅ New campaign suggestions generated based on your uploaded documents!');
      setTimeout(() => setError(null), 5000);
    } catch (error) {
      console.error('Failed to regenerate suggestions:', error);
    }
  };

  const handleWebsiteAddComplete = () => {
    setShowAddWebsiteModal(false);
    fetchKnowledgeBank(); // Refresh data
  };

  const getDocumentIcon = (fileType, documentType) => {
    if (documentType === 'website') return '🌐';
    if (fileType === 'pdf') return '📄';
    if (fileType === 'doc' || fileType === 'docx') return '📝';
    if (fileType === 'txt') return '📄';
    return '📄';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getCategoryCount = (categoryId) => {
    if (categoryId === 'all') {
      return documents.length + knowledge.length;
    }
    
    const docCount = documents.filter(doc => {
      // Use document_type field directly, fallback to extracted_content for backward compatibility
      if (doc.document_type) {
        return doc.document_type === categoryId;
      }
      
      try {
        const content = JSON.parse(doc.extracted_content || '{}');
        return content.document_type === categoryId;
      } catch {
        return false;
      }
    }).length;
    
    const knowledgeCount = knowledge.filter(k => k.source_type === categoryId).length;
    
    return docCount + knowledgeCount;
  };

  const filteredDocuments = documents.filter(doc => {
    if (selectedCategory === 'all') return true;
    if (selectedCategory === 'websites') return false;

    // Use document_type field directly, fallback to extracted_content for backward compatibility
    if (doc.document_type) {
      return doc.document_type === selectedCategory;
    }
    
    try {
      const content = JSON.parse(doc.extracted_content || '{}');
      return content.document_type === selectedCategory;
    } catch {
      return false;
    }
  });

  const filteredKnowledge = knowledge.filter(k => {
    if (selectedCategory === 'all') return true;
    if (selectedCategory === 'websites') return k.source_type === 'website';
    return k.source_type === selectedCategory;
  });

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading knowledge bank...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Knowledge Bank - AI SDR</title>
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Knowledge Bank</h1>
                  <p className="text-sm text-gray-600">Manage your training documents and knowledge base</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowAddWebsiteModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                >
                  <span>🌐</span>
                  <span>Add Website</span>
                </button>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                  <span>📄</span>
                  <span>Upload Document</span>
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

          {/* Category Filter */}
          <div className="mb-8">
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                    selectedCategory === category.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
                  }`}
                >
                  <span>{category.icon}</span>
                  <span>{category.name}</span>
                  <span className="ml-1 text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                    {getCategoryCount(category.id)}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Documents Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Training Documents */}
            {filteredDocuments.map((document) => {
              // Use the document_type field directly from the database
              let documentType = document.document_type || 'general';
              
              // Fallback to extracted_content for backward compatibility
              if (!document.document_type) {
                try {
                  const content = JSON.parse(document.extracted_content || '{}');
                  documentType = content.document_type || 'general';
                } catch (e) {
                  console.warn('Failed to parse document content:', e);
                  documentType = 'general';
                }
              }

              return (
                <div key={document.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getDocumentIcon(document.file_type, documentType)}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900 truncate">{document.filename}</h3>
                        <p className="text-sm text-gray-500 capitalize">{documentType.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(document.id, 'document')}
                      disabled={deletingId === document.id}
                      className="text-red-500 hover:text-red-700 disabled:opacity-50"
                    >
                      {deletingId === document.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500"></div>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      )}
                    </button>
                  </div>
                  
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Size:</span>
                      <span>{formatFileSize(document.file_size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        document.status === 'processed' ? 'bg-green-100 text-green-800' :
                        document.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                        document.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {document.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Uploaded:</span>
                      <span>{new Date(document.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Content Preview */}
                  {(() => {
                    try {
                      const content = JSON.parse(document.extracted_content || '{}');
                      return content.company_info && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Content Preview:</h4>
                          <div className="text-xs text-gray-600 space-y-1">
                            {content.company_info.name && (
                              <p><strong>Company:</strong> {content.company_info.name}</p>
                            )}
                            {content.company_info.industry && (
                              <p><strong>Industry:</strong> {content.company_info.industry}</p>
                            )}
                            {content.sales_approach && (
                              <p><strong>Sales Approach:</strong> {content.sales_approach.substring(0, 100)}...</p>
                            )}
                          </div>
                        </div>
                      );
                    } catch (e) {
                      return null;
                    }
                  })()}
                </div>
              );
            })}

            {/* Knowledge Items */}
            {filteredKnowledge.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getDocumentIcon('', item.source_type)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 truncate">{item.subject}</h3>
                      <p className="text-sm text-gray-500 capitalize">{item.source_type.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteDocument(item.id, 'knowledge')}
                    disabled={deletingId === item.id}
                    className="text-red-500 hover:text-red-700 disabled:opacity-50"
                  >
                    {deletingId === item.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500"></div>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      item.confidence_score > 0.8 ? 'bg-green-100 text-green-800' :
                      item.confidence_score > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(item.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Created:</span>
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Content Preview */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Content Preview:</h4>
                  <p className="text-xs text-gray-600 line-clamp-3">
                    {item.content.substring(0, 150)}...
                  </p>
                </div>

                {/* Tags */}
                {item.tags && item.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {item.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {tag}
                      </span>
                    ))}
                    {item.tags.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        +{item.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Empty State */}
          {filteredDocuments.length === 0 && filteredKnowledge.length === 0 && (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
              <p className="text-gray-600 mb-6">
                {selectedCategory === 'all' 
                  ? "You haven't uploaded any documents yet. Start building your knowledge base!"
                  : `No ${categories.find(c => c.id === selectedCategory)?.name.toLowerCase()} documents found.`
                }
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Upload Document
                </button>
                <button
                  onClick={() => setShowAddWebsiteModal(true)}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Add Website
                </button>
              </div>
            </div>
          )}
        </main>

        {/* Upload Document Modal */}
        {showUploadModal && (
          <UploadDocumentModal
            onClose={() => setShowUploadModal(false)}
            onUploadComplete={handleUploadComplete}
          />
        )}

        {/* Add Website Modal */}
        {showAddWebsiteModal && (
          <AddWebsiteModal
            onClose={() => setShowAddWebsiteModal(false)}
            onAddComplete={handleWebsiteAddComplete}
          />
        )}
      </div>
    </>
  );
}

// Upload Document Modal Component
function UploadDocumentModal({ onClose, onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState('company_info');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const documentTypes = [
    { id: 'company_info', name: 'Company Information', description: 'Company overview, mission, values' },
    { id: 'sales_training', name: 'Sales Training', description: 'Sales methodologies, best practices' },
    { id: 'products', name: 'Products/Services', description: 'Product catalogs, service descriptions' },
    { id: 'industry_knowledge', name: 'Industry Knowledge', description: 'Market research, industry insights' }
  ];

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', documentType);
      
      const response = await fetch('/api/train-your-team/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        onUploadComplete();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Upload failed');
      }
    } catch (err) {
      setError('Upload failed. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h2>
        
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {documentTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {documentTypes.find(t => t.id === documentType)?.description}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt,.ppt,.pptx"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Supported formats: PDF, DOC, DOCX, TXT, PPT, PPTX
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
              {uploading ? 'Uploading...' : 'Upload Document'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Add Website Modal Component
function AddWebsiteModal({ onClose, onAddComplete }) {
  const [url, setUrl] = useState('');
  const [documentType, setDocumentType] = useState('company_info');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);

  const documentTypes = [
    { id: 'company_info', name: 'Company Information', description: 'Company website, about page' },
    { id: 'sales_training', name: 'Sales Training', description: 'Sales resources, training materials' },
    { id: 'products', name: 'Products/Services', description: 'Product pages, service descriptions' },
    { id: 'industry_knowledge', name: 'Industry Knowledge', description: 'Industry reports, market research' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;
    
    setAdding(true);
    setError(null);
    
    try {
      const response = await fetch('/api/train-your-team/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: url,
          document_type: documentType
        })
      });

      if (response.ok) {
        onAddComplete();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to add website');
      }
    } catch (err) {
      setError('Failed to add website. Please try again.');
      console.error('Add website error:', err);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Website</h2>
        
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {documentTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {documentTypes.find(t => t.id === documentType)?.description}
            </p>
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={adding}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              disabled={!url || adding}
            >
              {adding ? 'Adding...' : 'Add Website'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
