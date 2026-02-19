import React, { useState } from 'react';
import { FiCopy, FiChevronDown, FiChevronUp, FiDownload } from 'react-icons/fi';

const getRiskColor = (riskLabel) => {
  switch (riskLabel) {
    case 'Safe':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'Adjust Dosage':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'Toxic':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'Ineffective':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getRiskIcon = (riskLabel) => {
  switch (riskLabel) {
    case 'Safe':
      return '✓';
    case 'Adjust Dosage':
      return '⚠';
    case 'Toxic':
      return '✕';
    case 'Ineffective':
      return '—';
    default:
      return '?';
  }
};

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'none':
      return 'bg-green-50';
    case 'low':
      return 'bg-blue-50';
    case 'moderate':
      return 'bg-yellow-50';
    case 'high':
      return 'bg-orange-50';
    case 'critical':
      return 'bg-red-50';
    default:
      return 'bg-gray-50';
  }
};

export function ResultCard({ assessment }) {
  const [expandedSummary, setExpandedSummary] = useState('clinical');
  const [copiedSection, setCopiedSection] = useState(null);

  const rawJson = JSON.stringify(assessment, null, 2);

  const copyToClipboard = (text, section) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const downloadJSON = () => {
    const dataStr = rawJson;
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pharma_guard_${assessment.patient_id}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const llmExplanation = assessment.llm_generated_explanation;
  const clinicalRecommendationText =
    typeof assessment.clinical_recommendation === 'string'
      ? assessment.clinical_recommendation
      : assessment.clinical_recommendation?.detail || assessment.clinical_recommendation?.action || 'No recommendation available';
  const clinicalSummaryText = llmExplanation?.summary || llmExplanation?.clinical_summary || 'No clinical summary available';
  const patientSummaryText = llmExplanation?.patient_summary || 'No patient summary available';
  const riskColor = getRiskColor(assessment.risk_assessment.risk_label);
  const riskIcon = getRiskIcon(assessment.risk_assessment.risk_label);
  const severityColor = getSeverityColor(assessment.risk_assessment.severity);

  return (
    <div className={`${severityColor} border-2 border-gray-200 rounded-xl overflow-hidden shadow-lg`}>
      {/* Header Section */}
      <div className="bg-gradient-to-r from-cyan-50 to-sky-50 p-6 border-b border-gray-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-3">
              <div className={`${riskColor} border px-4 py-2 rounded-lg font-bold text-lg`}>
                <span className="mr-2">{riskIcon}</span>
                {assessment.risk_assessment.risk_label}
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                assessment.risk_assessment.severity === 'critical' ? 'bg-red-200 text-red-800' :
                assessment.risk_assessment.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                assessment.risk_assessment.severity === 'moderate' ? 'bg-yellow-200 text-yellow-800' :
                'bg-green-200 text-green-800'
              }`}>
                {assessment.risk_assessment.severity.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600 font-semibold">GENE</p>
                <p className="font-bold text-gray-800">{assessment.pharmacogenomic_profile.primary_gene}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 font-semibold">MEDICATION</p>
                <p className="font-bold text-gray-800">{assessment.drug}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 font-semibold">DIPLOTYPE</p>
                <p className="font-bold text-gray-800">{assessment.pharmacogenomic_profile.diplotype}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 font-semibold">PHENOTYPE</p>
                <p className="font-bold text-gray-800">{assessment.pharmacogenomic_profile.phenotype}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => copyToClipboard(rawJson, 'raw-json')}
              className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
              title="Copy raw JSON"
            >
              <FiCopy size={18} />
              <span className="text-sm">
                {copiedSection === 'raw-json' ? 'Copied!' : 'Copy Raw JSON'}
              </span>
            </button>
            <button
              onClick={downloadJSON}
              className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
            >
              <FiDownload size={18} />
              <span className="text-sm">Download JSON Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Clinical Recommendation */}
      <div className="px-6 py-4 bg-blue-50 border-b border-gray-200">
        <h3 className="font-bold text-gray-800 mb-2">Clinical Recommendation</h3>
        <p className="text-gray-700 text-sm leading-relaxed">
          {clinicalRecommendationText}
        </p>
      </div>

      {/* Dual-Layer LLM Explanations */}
      <div className="p-6 space-y-4">
        {/* Toggle buttons for clinical vs patient view */}
        <div className="flex gap-3 mb-4">
          <button
            onClick={() => setExpandedSummary('clinical')}
            className={`flex-1 py-2 px-4 rounded-lg font-semibold transition-all text-sm ${
              expandedSummary === 'clinical'
                ? 'bg-sky-700 text-white shadow-md'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            📋 For Healthcare Professionals
          </button>
          <button
            onClick={() => setExpandedSummary('patient')}
            className={`flex-1 py-2 px-4 rounded-lg font-semibold transition-all text-sm ${
              expandedSummary === 'patient'
                ? 'bg-sky-700 text-white shadow-md'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            👥 For Patient
          </button>
        </div>

        {/* Clinical Summary Section */}
        {expandedSummary === 'clinical' && (
          <div className="bg-sky-50 border-2 border-sky-200 rounded-lg p-4 animate-fadeIn">
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-bold text-sky-900 text-sm">Clinical Summary (For Healthcare Professionals)</h4>
              <button
                onClick={() => copyToClipboard(clinicalSummaryText, 'clinical')}
                className="text-sky-700 hover:text-sky-900 transition-colors"
                title="Copy to clipboard"
              >
                {copiedSection === 'clinical' ? (
                  <span className="text-xs text-green-600 font-semibold">✓ Copied</span>
                ) : (
                  <FiCopy size={16} />
                )}
              </button>
            </div>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
              {clinicalSummaryText}
            </p>
          </div>
        )}

        {/* Patient Summary Section */}
        {expandedSummary === 'patient' && (
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4 animate-fadeIn">
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-bold text-green-900 text-sm">Patient Summary (Easy to Understand)</h4>
              <button
                onClick={() => copyToClipboard(patientSummaryText, 'patient')}
                className="text-green-600 hover:text-green-800 transition-colors"
                title="Copy to clipboard"
              >
                {copiedSection === 'patient' ? (
                  <span className="text-xs text-green-600 font-semibold">✓ Copied</span>
                ) : (
                  <FiCopy size={16} />
                )}
              </button>
            </div>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
              {patientSummaryText}
            </p>
          </div>
        )}
      </div>

      {/* Detected Variants Section */}
      {assessment.pharmacogenomic_profile.detected_variants?.length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <h4 className="font-bold text-gray-800 mb-3 text-sm">Detected Variants</h4>
          <div className="flex flex-wrap gap-2">
            {assessment.pharmacogenomic_profile.detected_variants.map((variant, idx) => (
              <span
                key={idx}
                className="bg-gray-200 text-gray-800 px-3 py-1 rounded-full text-xs font-semibold"
              >
                {variant.rsid}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footer with metadata */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-600">
        <span>Patient ID: {assessment.patient_id}</span>
        <span>{new Date(assessment.timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default function ResultsDisplay({ assessment, isLoading }) {
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-sky-700 mb-4"></div>
        <p className="text-gray-600 font-semibold">Analyzing your pharmacogenomic profile...</p>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="text-center py-12 bg-yellow-50 rounded-lg border-2 border-yellow-200">
        <p className="text-yellow-800">No results to display. Upload a VCF file to begin analysis.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ResultCard assessment={assessment} />
    </div>
  );
}
