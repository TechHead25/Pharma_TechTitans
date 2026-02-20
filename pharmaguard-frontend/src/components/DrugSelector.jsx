import React, { useState, useEffect } from 'react';
import { FiChevronDown, FiX } from 'react-icons/fi';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DrugSelector({ selectedDrugs, onDrugsChange, isLoading }) {
  const [drugs, setDrugs] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch available drugs from API
  useEffect(() => {
    const fetchDrugs = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/v1/drugs`);
        if (!response.ok) {
          throw new Error(`Failed to fetch drugs: ${response.status}`);
        }
        const data = await response.json();
        console.log('Drugs API response:', data);
        
        // Extract drugs array from response
        const drugsList = Array.isArray(data.drugs) ? data.drugs : [];
        console.log('Extracted drugs list:', drugsList);
        
        setDrugs(drugsList);
        setError(null);
      } catch (err) {
        console.error('Error fetching drugs:', err);
        setError(`Error loading medications: ${err.message}`);
        setDrugs([]);  // Set empty array on error
      } finally {
        setLoading(false);
      }
    };
    fetchDrugs();
  }, []);

  // Filter drugs based on search
  const filteredDrugs = drugs.filter(drug =>
    (drug.name && drug.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (drug.id && drug.id.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (drug.category && drug.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDrugToggle = (drugId) => {
    const newSelection = selectedDrugs.includes(drugId)
      ? selectedDrugs.filter(d => d !== drugId)
      : [...selectedDrugs, drugId];
    onDrugsChange(newSelection);
  };

  const handleRemoveDrug = (drugId) => {
    onDrugsChange(selectedDrugs.filter(d => d !== drugId));
  };

  const selectedDrugDetails = drugs.filter(d => selectedDrugs.includes(d.id));

  return (
    <div className="relative w-full">
      <label className="block text-sm font-semibold text-gray-700 mb-3">
        Select Medications <span className="text-xs text-gray-500">(choose one or more)</span>
      </label>
      
      {/* Selected drugs display */}
      {selectedDrugDetails.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {selectedDrugDetails.map(drug => (
            <div key={drug.id} className="inline-flex items-center gap-2 bg-green-50 border border-green-300 rounded-full px-3 py-1.5">
              <span className="text-sm font-medium text-green-700">{drug.name}</span>
              <button
                onClick={() => handleRemoveDrug(drug.id)}
                className="text-green-600 hover:text-green-800"
                title="Remove"
              >
                <FiX size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Main dropdown button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading || loading}
        className={`w-full px-4 py-3 text-left border-2 rounded-lg font-medium transition-all
          ${selectedDrugs.length > 0
            ? 'border-green-500 bg-green-50 text-gray-800' 
            : 'border-gray-300 bg-white text-gray-600 hover:border-green-400'}
          ${isLoading || loading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}
          flex items-center justify-between
        `}
      >
        <span>
          {loading ? 'Loading medications...' :
           selectedDrugs.length === 0 
            ? 'Choose medications...' 
            : `${selectedDrugs.length} selected`}
        </span>
        <FiChevronDown 
          className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}
          size={18}
        />
      </button>

      {/* Dropdown menu */}
      {isOpen && !loading && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-gray-300 rounded-lg shadow-lg z-50" style={{maxWidth: '500px'}}>
          {/* Search input */}
          <div className="p-3 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search by name, category, or gene..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              autoFocus
            />
          </div>

          {/* Drug list */}
          <div className="max-h-96 overflow-y-auto">
            {drugs.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500">
                <p className="mb-2">No medications available</p>
                <p className="text-xs">Check backend connection</p>
              </div>
            ) : filteredDrugs.length > 0 ? (
              filteredDrugs.map((drug) => (
                <label
                  key={drug.id}
                  className={`flex items-start gap-3 px-4 py-3 border-b border-gray-100 cursor-pointer transition-colors
                    ${selectedDrugs.includes(drug.id) 
                      ? 'bg-green-50' 
                      : 'hover:bg-gray-50'}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={selectedDrugs.includes(drug.id)}
                    onChange={() => handleDrugToggle(drug.id)}
                    className="mt-1 w-4 h-4 cursor-pointer"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">{drug.name}</div>
                    <div className="text-xs text-gray-600">{drug.category}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Genes: {Array.isArray(drug.genes) ? drug.genes.join(', ') : drug.genes} • {drug.description}
                    </div>
                  </div>
                </label>
              ))
            ) : (
              <div className="px-4 py-3 text-gray-500 text-center">
                No medications match "{searchTerm}"
              </div>
            )}
          </div>
          
          {/* Show total count */}
          <div className="px-4 py-2 bg-gray-50 text-xs text-gray-600 border-t border-gray-200">
            Showing {filteredDrugs.length} of {drugs.length} medications
          </div>
        </div>
      )}

      {error && (
        <p className="text-xs text-red-600 mt-2">⚠️ {error}</p>
      )}

      {/* Info text */}
      <p className="text-xs text-gray-500 mt-2">
        Select one or more medications to analyze genetic interactions (CPIC-aligned)
      </p>
    </div>
  );
}

