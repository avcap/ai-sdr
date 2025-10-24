import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

const GoogleSheetsImport = ({ campaignId, onImportComplete }) => {
  const { data: session } = useSession();
  const [sheets, setSheets] = useState([]);
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [sheetData, setSheetData] = useState(null);
  const [columnMapping, setColumnMapping] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Select sheet, 2: Preview & map, 3: Import

  const leadFields = [
    { key: 'name', label: 'Name', required: true },
    { key: 'company', label: 'Company', required: true },
    { key: 'title', label: 'Title', required: true },
    { key: 'email', label: 'Email', required: false },
    { key: 'linkedin_url', label: 'LinkedIn URL', required: false },
    { key: 'phone', label: 'Phone', required: false },
    { key: 'industry', label: 'Industry', required: false },
    { key: 'company_size', label: 'Company Size', required: false },
    { key: 'location', label: 'Location', required: false }
  ];

  useEffect(() => {
    if (step === 1) {
      loadSheets();
    }
  }, [step]);

  const loadSheets = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/google/sheets/list', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSheets(data.sheets || []);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to load sheets');
      }
    } catch (err) {
      setError('Failed to load sheets');
    } finally {
      setLoading(false);
    }
  };

  const previewSheet = async (sheetId) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/google/sheets/${sheetId}/preview`, {
        headers: {
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSheetData(data.data);
        
        // Auto-map columns based on header names
        const autoMapping = {};
        data.data.headers.forEach(header => {
          const lowerHeader = header.toLowerCase();
          leadFields.forEach(field => {
            if (lowerHeader.includes(field.key) || lowerHeader.includes(field.label.toLowerCase())) {
              autoMapping[header] = field.key;
            }
          });
        });
        setColumnMapping(autoMapping);
        
        setStep(2);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to preview sheet');
      }
    } catch (err) {
      setError('Failed to preview sheet');
    } finally {
      setLoading(false);
    }
  };

  const importLeads = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/google/sheets/${selectedSheet.id}/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || 'demo_token'}`
        },
        body: JSON.stringify({
          campaign_id: campaignId,
          column_mapping: columnMapping
        })
      });

      if (response.ok) {
        const data = await response.json();
        onImportComplete(data);
        setStep(3);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to import leads');
      }
    } catch (err) {
      setError('Failed to import leads');
    } finally {
      setLoading(false);
    }
  };

  const handleSheetSelect = (sheet) => {
    setSelectedSheet(sheet);
    previewSheet(sheet.id);
  };

  const handleColumnMappingChange = (sheetColumn, leadField) => {
    setColumnMapping(prev => ({
      ...prev,
      [sheetColumn]: leadField
    }));
  };

  if (step === 1) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Import Leads from Google Sheets</h3>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading your Google Sheets...</p>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 mb-4">Select a Google Sheet to import leads from:</p>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {sheets.map(sheet => (
                <div
                  key={sheet.id}
                  className="border rounded p-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleSheetSelect(sheet)}
                >
                  <div className="font-medium">{sheet.name}</div>
                  <div className="text-sm text-gray-500">
                    Modified: {new Date(sheet.modified_time).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
            {sheets.length === 0 && (
              <p className="text-gray-500 text-center py-4">No Google Sheets found</p>
            )}
          </div>
        )}
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Preview & Map Columns</h3>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-4">
          <p className="text-gray-600">
            Sheet: <strong>{sheetData?.sheet_name}</strong> ({sheetData?.total_rows} rows)
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-3">Map Sheet Columns to Lead Fields</h4>
            <div className="space-y-3">
              {sheetData?.headers.map(header => (
                <div key={header} className="flex items-center space-x-3">
                  <label className="w-32 text-sm font-medium">{header}:</label>
                  <select
                    value={columnMapping[header] || ''}
                    onChange={(e) => handleColumnMappingChange(header, e.target.value)}
                    className="flex-1 border rounded px-3 py-1 text-sm"
                  >
                    <option value="">-- Select field --</option>
                    {leadFields.map(field => (
                      <option key={field.key} value={field.key}>
                        {field.label} {field.required ? '*' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">Preview Data</h4>
            <div className="border rounded overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {sheetData?.headers.map(header => (
                      <th key={header} className="px-3 py-2 text-left font-medium">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sheetData?.rows.slice(0, 5).map((row, index) => (
                    <tr key={index} className="border-t">
                      {sheetData.headers.map(header => (
                        <td key={header} className="px-3 py-2">
                          {row[header] || ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="flex justify-between mt-6">
          <button
            onClick={() => setStep(1)}
            className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          <button
            onClick={importLeads}
            disabled={loading || !Object.values(columnMapping).includes('name') || !Object.values(columnMapping).includes('company') || !Object.values(columnMapping).includes('title')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Importing...' : 'Import Leads'}
          </button>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-green-800 mb-2">Import Complete!</h3>
          <p className="text-gray-600 mb-4">
            Successfully imported leads from Google Sheets
          </p>
          <button
            onClick={() => {
              setStep(1);
              setSelectedSheet(null);
              setSheetData(null);
              setColumnMapping({});
              setError(null);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Import More Leads
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default GoogleSheetsImport;


