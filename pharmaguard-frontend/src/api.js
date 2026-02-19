import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadVCF = async (file, drug) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('drug', drug);
  
  try {
    const response = await api.post('/api/v1/analyze-vcf', formData);
    return response.data;
  } catch (error) {
    console.error('Upload error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to upload VCF file');
  }
};

export const validateVCF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/api/v1/validate-vcf', formData);
    console.log('Validation response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Validation error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to validate VCF file');
  }
};

export const getResults = async (patientId) => {
  try {
    const response = await api.get(`/api/v1/results/${patientId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to retrieve results');
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/api/v1/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'error' };
  }
};
