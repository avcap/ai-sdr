import { useState, useRef } from 'react';
import { useSession } from 'next-auth/react';

export default function TrainYourTeam({ isOpen, onClose }) {
  const { data: session } = useSession();
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [extractedKnowledge, setExtractedKnowledge] = useState(null);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setProcessingStatus('uploading');
    setTrainingProgress(10);

    try {
      // Upload files to backend
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch('/api/train-your-team/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setUploadedFiles(result.files || []);
        setProcessingStatus('processing');
        setTrainingProgress(30);
        
        // Start knowledge extraction
        await extractKnowledge(result.files || []);
      } else {
        throw new Error('Failed to upload files');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setProcessingStatus('error');
    }
  };

  const extractKnowledge = async (files) => {
    try {
      setTrainingProgress(50);
      
      // Convert files to file paths for the backend
      const filePaths = files.map(file => file.file_path || file.path || `/tmp/${file.filename}`);
      const subject = files[0]?.subject || 'Uploaded Document';
      
      const response = await fetch('/api/train-your-team/extract-knowledge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({ 
          file_paths: filePaths,
          subject: subject
        })
      });

      if (response.ok) {
        const result = await response.json();
        setExtractedKnowledge(result.knowledge);
        setProcessingStatus('completed');
        setTrainingProgress(100);
      } else {
        throw new Error('Failed to extract knowledge');
      }
    } catch (error) {
      console.error('Knowledge extraction error:', error);
      setProcessingStatus('error');
    }
  };

  const saveKnowledge = async () => {
    try {
      const response = await fetch('/api/train-your-team/save-knowledge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({ knowledge: extractedKnowledge })
      });

      if (response.ok) {
        alert('Knowledge saved successfully! Your AI agents are now trained.');
        onClose();
      } else {
        throw new Error('Failed to save knowledge');
      }
    } catch (error) {
      console.error('Save knowledge error:', error);
      alert('Failed to save knowledge. Please try again.');
    }
  };

  const resetTraining = () => {
    setUploadedFiles([]);
    setProcessingStatus('idle');
    setExtractedKnowledge(null);
    setTrainingProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">🎓 Train Your Team</h2>
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
          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📁 Upload Documents
            </button>
            <button
              onClick={() => setActiveTab('knowledge')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'knowledge'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🧠 Extracted Knowledge
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'preview'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              👁️ Preview Training
            </button>
          </div>

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Upload Company Documents
                </h3>
                <p className="text-gray-600 mb-6">
                  Upload PDFs, Word docs, or PowerPoint presentations to train your AI agents on your company's approach, products, and sales methodology.
                </p>
              </div>

              {/* File Upload Area */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors mb-4"
                >
                  Choose Files
                </button>
                <p className="text-sm text-gray-500">
                  Supported formats: PDF, Word, PowerPoint, Text files
                </p>
              </div>

              {/* Processing Status */}
              {processingStatus !== 'idle' && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-gray-900">Training Progress</h4>
                    <span className="text-sm text-gray-600">{trainingProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${trainingProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600">
                    {processingStatus === 'uploading' && 'Uploading files...'}
                    {processingStatus === 'processing' && 'Analyzing documents with Claude AI...'}
                    {processingStatus === 'completed' && 'Knowledge extraction completed!'}
                    {processingStatus === 'error' && 'Error occurred during processing'}
                  </p>
                </div>
              )}

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-900 mb-2">Uploaded Files</h4>
                  <ul className="space-y-2">
                    {uploadedFiles.map((file, index) => (
                      <li key={index} className="flex items-center text-sm text-green-800">
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                        </svg>
                        {file.name} ({file.size})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Knowledge Tab */}
          {activeTab === 'knowledge' && (
            <div className="space-y-6">
              {extractedKnowledge ? (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Extracted Knowledge</h3>
                  
                  {/* Company Information */}
                  {extractedKnowledge.company_info && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-semibold text-blue-900 mb-2">Company Information</h4>
                      <div className="text-sm text-blue-800 space-y-1">
                        {Object.entries(extractedKnowledge.company_info).map(([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key}:</span> {value}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sales Approach */}
                  {extractedKnowledge.sales_approach && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-semibold text-green-900 mb-2">Sales Approach</h4>
                      <div className="text-sm text-green-800">
                        {extractedKnowledge.sales_approach}
                      </div>
                    </div>
                  )}

                  {/* Product Information */}
                  {extractedKnowledge.products && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h4 className="font-semibold text-purple-900 mb-2">Product Information</h4>
                      <div className="text-sm text-purple-800 space-y-2">
                        {extractedKnowledge.products.map((product, index) => (
                          <div key={index} className="border-l-2 border-purple-300 pl-3">
                            <div className="font-medium">{product.name}</div>
                            <div>{product.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Messages */}
                  {extractedKnowledge.key_messages && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h4 className="font-semibold text-yellow-900 mb-2">Key Messages</h4>
                      <ul className="text-sm text-yellow-800 space-y-1">
                        {extractedKnowledge.key_messages.map((message, index) => (
                          <li key={index} className="flex items-start">
                            <span className="mr-2">•</span>
                            <span>{message}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">No knowledge extracted yet. Please upload documents first.</p>
                </div>
              )}
            </div>
          )}

          {/* Preview Tab */}
          {activeTab === 'preview' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Training Preview</h3>
              
              {extractedKnowledge ? (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">How Your AI Agents Will Use This Knowledge</h4>
                    <ul className="text-sm text-gray-700 space-y-2">
                      <li>• <strong>Prospector Agent:</strong> Will search for leads that match your ideal customer profile</li>
                      <li>• <strong>Copywriter Agent:</strong> Will craft messages using your company's voice and key messages</li>
                      <li>• <strong>Smart Outreach Agent:</strong> Will personalize outreach based on your sales approach</li>
                      <li>• <strong>All Agents:</strong> Will reference your product information and value propositions</li>
                    </ul>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-2">Sample AI-Generated Message</h4>
                    <div className="bg-white border border-blue-200 rounded p-3 text-sm">
                      <p className="text-gray-700 italic">
                        "Hi [Name], I noticed [Company] is in the [Industry] space. At [Your Company], we help companies like yours [value proposition]. 
                        Our [product] has helped [similar companies] achieve [results]. Would you be interested in a brief conversation about how we might help [Company]?"
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">Upload and process documents to see training preview.</p>
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-6 border-t">
            <button
              onClick={resetTraining}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Reset
            </button>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              {extractedKnowledge && (
                <button
                  onClick={saveKnowledge}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Knowledge & Train Agents
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

