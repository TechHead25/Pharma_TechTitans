import React, { useState, useEffect } from 'react';
import { FiLogOut, FiBarChart2, FiTrendingUp } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

export default function DataVisualizationDashboard() {
  const [userRecords, setUserRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVcf, setSelectedVcf] = useState(null);
  const [selectedRecordName, setSelectedRecordName] = useState('');
  const [loadingVcfId, setLoadingVcfId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserRecords();
  }, []);

  const fetchUserRecords = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/records/user', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch records');
      const data = await response.json();
      setUserRecords(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching records:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleViewVcf = async (record) => {
    try {
      setLoadingVcfId(record.id);
      const response = await fetch(`http://localhost:8000/api/v1/records/${record.id}/vcf`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        if (response.status === 404) {
          throw new Error(`VCF text is not available for ${record.filename}. This record may be older than the VCF storage update.`);
        }
        throw new Error(err.detail || 'Unable to fetch VCF content');
      }

      const text = await response.text();
      setSelectedRecordName(record.filename || record.id);
      setSelectedVcf(text);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingVcfId(null);
    }
  };

  // Calculate statistics
  const totalAnalyses = userRecords.length;
  const completedAnalyses = userRecords.filter(r => r.status === 'completed').length;
  const failedAnalyses = userRecords.filter(r => r.status === 'failed').length;
  const successRate = totalAnalyses > 0 ? ((completedAnalyses / totalAnalyses) * 100).toFixed(1) : 0;

  // Get drug frequency
  const drugFrequency = {};
  userRecords.forEach(record => {
    const drugs = record.analyzed_drugs.split(',');
    drugs.forEach(drug => {
      const trimmed = drug.trim();
      drugFrequency[trimmed] = (drugFrequency[trimmed] || 0) + 1;
    });
  });

  const topDrugs = Object.entries(drugFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-semibold">Loading your analysis data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Your Analysis Dashboard</h1>
              <p className="text-indigo-100">Data Visualization & Insights</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-indigo-100">{user.full_name}</span>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition"
              >
                <FiLogOut size={20} />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">Total Analyses</p>
                <p className="text-4xl font-bold text-gray-800 mt-2">{totalAnalyses}</p>
              </div>
              <FiBarChart2 className="w-12 h-12 text-blue-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">Completed</p>
                <p className="text-4xl font-bold text-green-600 mt-2">{completedAnalyses}</p>
              </div>
              <FiTrendingUp className="w-12 h-12 text-green-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">Failed</p>
                <p className="text-4xl font-bold text-red-600 mt-2">{failedAnalyses}</p>
              </div>
              <FiBarChart2 className="w-12 h-12 text-red-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">Success Rate</p>
                <p className="text-4xl font-bold text-indigo-600 mt-2">{successRate}%</p>
              </div>
              <FiTrendingUp className="w-12 h-12 text-indigo-500 opacity-20" />
            </div>
          </div>
        </div>

        {/* Top Analyzed Drugs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Top Analyzed Drugs</h2>
            <div className="space-y-4">
              {topDrugs.length > 0 ? (
                topDrugs.map(([drug, count], idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                        <span className="text-indigo-700 font-bold">{idx + 1}</span>
                      </div>
                      <span className="text-gray-700 font-medium">{drug}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600"
                          style={{
                            width: `${(count / (topDrugs[0]?.[1] || 1)) * 100}%`
                          }}
                        ></div>
                      </div>
                      <span className="text-gray-600 font-semibold text-sm">{count}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No drug analysis data available</p>
              )}
            </div>
          </div>

          {/* Status Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Analysis Status Distribution</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1">
                  <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                  <span className="text-gray-700 font-medium">Completed</span>
                </div>
                <div className="text-right">
                  <span className="text-green-600 font-bold">{completedAnalyses}</span>
                  <span className="text-gray-500 text-sm ml-2">
                    ({totalAnalyses > 0 ? ((completedAnalyses / totalAnalyses) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
              </div>

              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${totalAnalyses > 0 ? ((completedAnalyses / totalAnalyses) * 100) : 0}%`
                  }}
                ></div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                    <span className="text-gray-700 font-medium">Failed</span>
                  </div>
                  <div className="text-right">
                    <span className="text-red-600 font-bold">{failedAnalyses}</span>
                    <span className="text-gray-500 text-sm ml-2">
                      ({totalAnalyses > 0 ? ((failedAnalyses / totalAnalyses) * 100).toFixed(1) : 0}%)
                    </span>
                  </div>
                </div>
              </div>

              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-2">
                <div
                  className="h-full bg-red-500"
                  style={{
                    width: `${totalAnalyses > 0 ? ((failedAnalyses / totalAnalyses) * 100) : 0}%`
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Analyses Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Your Recent Analyses</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">File</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Drugs Analyzed</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {userRecords.length > 0 ? (
                    userRecords.map((record) => (
                      <tr key={record.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 text-gray-800">{record.filename}</td>
                        <td className="py-3 px-4 text-gray-600 text-sm">{record.analyzed_drugs}</td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            record.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : record.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {record.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-600 text-sm">
                          {new Date(record.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => handleViewVcf(record)}
                            disabled={loadingVcfId === record.id}
                            className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold underline disabled:text-gray-400 disabled:no-underline"
                          >
                            {loadingVcfId === record.id ? 'Loading...' : 'View VCF'}
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="py-4 text-center text-gray-500">
                        No analyses yet. Start by analyzing your first VCF file!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {selectedVcf && (
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-gray-800">VCF Content: {selectedRecordName}</h3>
              <button
                onClick={() => setSelectedVcf(null)}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Close
              </button>
            </div>
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-800 overflow-auto max-h-96 whitespace-pre-wrap">
              {selectedVcf}
            </pre>
          </div>
        )}

        {/* Back to Analysis Button */}
        <div className="mt-8 text-center">
          <a
            href="/dashboard"
            className="inline-block bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-lg transition-all shadow-md hover:shadow-lg"
          >
            Back to Analysis
          </a>
        </div>
      </main>
    </div>
  );
}
