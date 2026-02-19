import React, { useState } from 'react';
import { FiUploadCloud, FiX, FiCheck, FiAlertCircle } from 'react-icons/fi';
import { validateVCF } from '../api';

const ERROR_MESSAGES = {
  'NO_FILE': 'No file provided. Please select a VCF file.',
  'NO_FILENAME': 'File has no name. Please select a valid file.',
  'INVALID_EXTENSION': 'Invalid file type. Please upload a .vcf file.',
  'EMPTY_FILE': 'The uploaded file is empty. Please check your file.',
  'FILE_TOO_LARGE': 'File is too large. Maximum size is 5 MB.',
  'ENCODING_ERROR': 'File encoding error. Make sure the file is saved as UTF-8 text.',
  'CONTENT_TOO_SMALL': 'VCF file is too small or contains only whitespace.',
  'INVALID_VCF_STRUCTURE': 'VCF file structure is invalid. Check VCF format compliance.',
  'VALIDATION_ERROR': 'An unexpected validation error occurred.',
};

export default function VCFUploader({ onFileSelect, onValidationStart, onValidationEnd }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationStatus, setValidationStatus] = useState(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      await handleFileSelection(file);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files.length > 0) {
      await handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = async (file) => {
    // Quick client-side validation
    if (!file.name.endsWith('.vcf')) {
      setValidationStatus({
        valid: false,
        error: `Invalid file type: '${file.name}'. Only .vcf files are accepted.`,
        errorCode: 'INVALID_EXTENSION',
      });
      return;
    }

    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > 5) {
      setValidationStatus({
        valid: false,
        error: `File is too large (${fileSizeMB.toFixed(2)} MB). Maximum allowed size is 5 MB.`,
        errorCode: 'FILE_TOO_LARGE',
      });
      return;
    }

    if (file.size === 0) {
      setValidationStatus({
        valid: false,
        error: 'The uploaded file is empty. Please ensure your VCF file contains data.',
        errorCode: 'EMPTY_FILE',
      });
      return;
    }

    setSelectedFile(file);
    setIsValidating(true);
    onValidationStart?.();

    try {
      const result = await validateVCF(file);
      console.log('Validation result:', result);
      
      // Handle validation response
      if (result.valid === false) {
        const errorMessage = ERROR_MESSAGES[result.errorCode] || result.error || 'Validation failed';
        setValidationStatus({
          valid: false,
          error: errorMessage,
          errorCode: result.errorCode,
          details: result.details,
        });
      } else if (result.valid === true) {
        setValidationStatus({
          valid: true,
          message: `VCF file is valid (${result.variant_count} variants detected)`,
          size_mb: result.size_mb,
          file_name: result.file_name,
          variant_count: result.variant_count,
        });
        onFileSelect(file);
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationStatus({
        valid: false,
        error: `Error validating file: ${error.message || 'Unknown error'}`,
        errorCode: 'VALIDATION_ERROR',
      });
    } finally {
      setIsValidating(false);
      onValidationEnd?.();
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setValidationStatus(null);
  };

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400'
        } ${selectedFile ? 'bg-gray-50' : ''}`}
      >
        {!selectedFile ? (
          <>
            <FiUploadCloud className="mx-auto mb-4 text-4xl text-gray-400" />
            <p className="text-lg font-semibold text-gray-700 mb-2">
              Drag and drop your VCF file here
            </p>
            <p className="text-gray-500 mb-4">or click to browse</p>
            <input
              type="file"
              accept=".vcf"
              onChange={handleFileChange}
              className="hidden"
              id="vcf-input"
            />
            <label
              htmlFor="vcf-input"
              className="btn-primary cursor-pointer inline-block"
            >
              Browse Files
            </label>
            <p className="text-sm text-gray-400 mt-4">
              Maximum file size: 5 MB • Format: VCF (Variant Call Format) v4.2 or higher
            </p>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between bg-white p-4 rounded-lg">
              <div className="text-left">
                <p className="font-semibold text-gray-700">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                onClick={clearFile}
                className="text-red-500 hover:text-red-700 transition-colors"
                title="Remove file"
              >
                <FiX size={24} />
              </button>
            </div>

            {isValidating && (
              <div className="flex items-center justify-center space-x-2 text-blue-600 p-4 bg-blue-50 rounded-lg">
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span>Validating VCF file structure...</span>
              </div>
            )}

            {validationStatus && !isValidating && (
              <div
                className={`p-4 rounded-lg flex items-start space-x-3 ${
                  validationStatus.valid
                    ? 'bg-green-50 text-green-800'
                    : 'bg-red-50 text-red-800'
                }`}
              >
                {validationStatus.valid ? (
                  <FiCheck className="mt-0.5 flex-shrink-0" size={20} />
                ) : (
                  <FiAlertCircle className="mt-0.5 flex-shrink-0" size={20} />
                )}
                <div className="flex-1">
                  <p className="font-semibold">
                    {validationStatus.valid ? '✓ File Valid' : '✗ Validation Failed'}
                  </p>
                  <p className="text-sm mt-1">
                    {validationStatus.message || validationStatus.error}
                  </p>
                  {validationStatus.details && (
                    <p className="text-xs mt-1 opacity-75">
                      Details: {validationStatus.details}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

