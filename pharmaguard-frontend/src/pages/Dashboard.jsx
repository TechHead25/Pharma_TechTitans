import React, { useState, useRef } from 'react';
import { FiAlertCircle, FiCheckCircle, FiLogOut, FiBarChart2, FiSettings } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import DrugSelector from '../components/DrugSelector';
import VCFUploader from '../components/VCFUploader';
import ResultsDisplay from '../components/ResultsDisplay';
import '../index.css';

function Dashboard() {
  const [selectedDrugs, setSelectedDrugs] = useState([]);
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState('drug-selection');
  const navigate = useNavigate();
  const vcfUploaderRef = useRef(null);

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  // Handle drug selection (no auto-advance - user must click Continue)
  const handleDrugChange = (drugs) => {
    setSelectedDrugs(drugs);
  };

  // Handle file selection
  const handleFileChange = (selectedFile) => {
    setFile(selectedFile);
    setError(null);
  };

  // Handle file upload and analysis
  const handleAnalyze = async () => {
    if (!file || selectedDrugs.length === 0) {
      setError('Please select at least one medication and upload a VCF file');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const drugsParam = selectedDrugs.join(',');
      const response = await fetch(`http://localhost:8000/api/v1/analyze-vcf?drug=${drugsParam}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const analysisResults = await response.json();
      let vcfContent = null;
      try {
        vcfContent = await file.text();
      } catch (vcfReadErr) {
        console.warn('Failed to read VCF file content for saving:', vcfReadErr);
      }
      
      // Save record to database
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          console.warn('No access token found. Skipping record save.');
        } else {
        const saveResponse = await fetch('http://localhost:8000/api/v1/records/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            filename: file.name,
            analyzed_drugs: drugsParam,
            vcf_content: vcfContent,
            analysis_result: JSON.stringify(analysisResults),
            phenotypes: JSON.stringify(analysisResults.phenotypes || {})
          })
        });
        
        if (!saveResponse.ok) {
          let detail = 'Failed to save analysis record';
          try {
            const errJson = await saveResponse.json();
            detail = errJson.detail || detail;
          } catch (_) {
          }
          console.warn('Failed to save analysis record:', detail);
          if (saveResponse.status === 401) {
            setError('Your session expired. Please log in again to save analysis history.');
          }
        }
        }
      } catch (saveErr) {
        console.warn('Error saving record:', saveErr);
      }

      setResults(analysisResults);
      setStage('results');
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle restart
  const handleRestart = () => {
    setSelectedDrugs([]);
    setFile(null);
    setResults(null);
    setError(null);
    setStage('drug-selection');
  };

  const handleChangeDrug = () => {
    setSelectedDrugs([]);
    setFile(null);
    setResults(null);
    setError(null);
    setStage('drug-selection');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header with user menu */}
      <header className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold">PharmaGuard</h1>
              <p className="text-indigo-100 text-sm mt-1">Pharmacogenomic Risk Assessment Platform</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-indigo-100 text-sm">Welcome, {user.full_name}</p>
                <p className="text-indigo-200 text-xs mt-1">v2.0 • Multi-Drug Analysis</p>
              </div>
              <div className="flex items-center space-x-2">
                {user.is_admin && (
                  <button
                    onClick={() => navigate('/admin')}
                    className="flex items-center space-x-2 bg-indigo-500 hover:bg-indigo-600 px-3 py-2 rounded-lg transition text-sm"
                    title="Admin Dashboard"
                  >
                    <FiSettings size={18} />
                    <span hidden className="md:inline">Admin</span>
                  </button>
                )}
                <button
                  onClick={() => navigate('/visualizations')}
                  className="flex items-center space-x-2 bg-purple-500 hover:bg-purple-600 px-3 py-2 rounded-lg transition text-sm"
                  title="Analytics"
                >
                  <FiBarChart2 size={18} />
                  <span className="hidden md:inline">Analytics</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 px-3 py-2 rounded-lg transition text-sm"
                  title="Logout"
                >
                  <FiLogOut size={18} />
                  <span className="hidden md:inline">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress indicators */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className={`flex items-center space-x-3 ${stage === 'drug-selection' ? 'opacity-100' : 'opacity-60'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                stage === 'drug-selection' ? 'bg-indigo-600' : 'bg-green-600'
              }`}>
                {stage !== 'drug-selection' ? '✓' : '1'}
              </div>
              <span className="font-semibold text-gray-700">Select Medication(s)</span>
            </div>

            <div className={`flex-1 h-1 mx-4 ${stage !== 'drug-selection' ? 'bg-green-600' : 'bg-gray-300'}`}></div>

            <div className={`flex items-center space-x-3 ${stage === 'file-upload' || stage === 'results' ? 'opacity-100' : 'opacity-60'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                stage === 'results' ? 'bg-green-600' :
                stage === 'file-upload' ? 'bg-indigo-600' : 'bg-gray-300'
              }`}>
                {stage === 'results' ? '✓' : '2'}
              </div>
              <span className="font-semibold text-gray-700">Upload VCF</span>
            </div>

            <div className={`flex-1 h-1 mx-4 ${stage === 'results' ? 'bg-green-600' : 'bg-gray-300'}`}></div>

            <div className={`flex items-center space-x-3 ${stage === 'results' ? 'opacity-100' : 'opacity-60'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                stage === 'results' ? 'bg-green-600' : 'bg-gray-300'
              }`}>
                3
              </div>
              <span className="font-semibold text-gray-700">Results</span>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start space-x-3">
            <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-semibold text-red-800">Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Stage 1: Drug Selection */}
        {stage === 'drug-selection' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Step 1: Select Your Medications</h2>
            <DrugSelector 
              selectedDrugs={selectedDrugs}
              onDrugsChange={handleDrugChange}
              isLoading={isLoading}
            />
            <p className="text-gray-600 text-sm mt-6 bg-blue-50 p-4 rounded-lg">
              💡 <strong>Tip:</strong> Select one or more medications you're taking or considering. Our analysis will check for genetic interactions with each drug.
            </p>
            
            {/* Continue button - only enabled when drugs are selected */}
            {selectedDrugs.length > 0 && (
              <button
                onClick={() => setStage('file-upload')}
                className="mt-6 w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all shadow-md hover:shadow-lg"
              >
                Continue with Selected Medications ({selectedDrugs.length})
              </button>
            )}
          </div>
        )}

        {/* Stage 2: File Upload */}
        {(stage === 'file-upload' || stage === 'results') && (
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">Step 2: Upload Your VCF File</h2>
                <p className="text-gray-600 text-sm mt-2">
                  Selected medications: <span className="font-semibold text-indigo-600">{selectedDrugs.join(', ')}</span>
                </p>
              </div>
              {selectedDrugs.length > 0 && (
                <button
                  onClick={handleChangeDrug}
                  className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm underline"
                >
                  Change medications
                </button>
              )}
            </div>

            <VCFUploader 
              onFileSelect={handleFileChange}
              isLoading={isLoading}
              selectedFile={file}
            />

            {file && !isLoading && stage !== 'results' && (
              <button
                onClick={handleAnalyze}
                className="mt-6 w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all shadow-md hover:shadow-lg"
              >
                Analyze Pharmacogenomic Profile
              </button>
            )}

            {isLoading && (
              <div className="mt-6 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
                <p className="text-gray-600 font-semibold">Processing your VCF file...</p>
              </div>
            )}
          </div>
        )}

        {/* Stage 3: Results */}
        {stage === 'results' && results && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <FiCheckCircle className="text-green-600" size={28} />
                <h2 className="text-2xl font-bold text-gray-800">Analysis Results</h2>
              </div>
              <button
                onClick={handleRestart}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
              >
                New Analysis
              </button>
            </div>
            
            {/* Handle multiple drug results */}
            {results.analyses ? (
              <div className="grid grid-cols-1 gap-6">
                {results.analyses.map((analysis, idx) => (
                  <div key={idx} className="border-l-4 border-indigo-500 pl-4 pt-4">
                    <h3 className="text-lg font-semibold text-indigo-600 mb-4">
                      {analysis.drug} Analysis
                    </h3>
                    <ResultsDisplay assessment={analysis} isLoading={false} />
                  </div>
                ))}
              </div>
            ) : (
              <ResultsDisplay assessment={results} isLoading={false} />
            )}
          </div>
        )}

        {/* Footer info */}
        <div className="mt-12 p-6 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
          <h3 className="font-bold text-indigo-900 mb-2">About PharmaGuard</h3>
          <p className="text-indigo-800 text-sm mb-3">
            PharmaGuard uses AI-powered pharmacogenomic analysis aligned with CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines. Our dual-layer explanations provide both technical insights for healthcare professionals and simple explanations for patients.
          </p>
          <p className="text-indigo-800 text-sm">
            <strong>Disclaimer:</strong> This tool is for informational purposes only and should not replace professional medical advice. Always consult with your healthcare provider before making medication decisions.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 text-center py-6 mt-12">
        <p className="text-sm">© 2024 PharmaGuard • CPIC-Aligned Pharmacogenomic Analysis</p>
      </footer>
    </div>
  );
}

export default Dashboard;
