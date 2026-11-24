import { useState, useCallback } from 'react';
import api from '../lib/api';
import { UploadCloud, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

const FileUpload = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState({ status: 'idle', message: '' });

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateAndUpload = useCallback(async (selectedFile) => {
    if (!selectedFile) return;
    
    // Client-side validation
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(pdf|docx)$/i)) {
      setUploadState({ status: 'error', message: 'Only PDF and DOCX files are allowed.' });
      return;
    }

    if (selectedFile.size > 20 * 1024 * 1024) {
      setUploadState({ status: 'error', message: 'File exceeds the 20MB limit.' });
      return;
    }

    setUploadState({ status: 'uploading', message: 'Uploading and processing document...' });

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await api.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadState({ status: 'success', message: 'Document processed successfully!' });
      
      // Reset after a short delay and refresh document list
      setTimeout(() => {
        setUploadState({ status: 'idle', message: '' });
        if (onUploadComplete) onUploadComplete();
      }, 2000);

    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Upload failed. Make sure the backend server is running.';
      setUploadState({ status: 'error', message: errorMsg });
    }
  }, [onUploadComplete]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndUpload(droppedFile);
  }, [validateAndUpload]);

  const handleFileSelect = useCallback((e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) validateAndUpload(selectedFile);
    e.target.value = ''; // Reset so same file can be re-uploaded
  }, [validateAndUpload]);

  return (
    <div className="w-full">
      <div 
        className={`relative glass-panel p-8 text-center border-2 border-dashed transition-all duration-200 ease-in-out cursor-pointer overflow-hidden
          ${isDragging ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/20 hover:border-white/40'}
          ${uploadState.status === 'uploading' ? 'pointer-events-none opacity-80' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload').click()}
      >
        <input 
          id="file-upload" 
          type="file" 
          className="hidden" 
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileSelect}
        />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          {uploadState.status === 'idle' && (
            <>
              <div className="p-4 bg-white/5 rounded-full">
                <UploadCloud className="w-10 h-10 text-primary" />
              </div>
              <div>
                <p className="text-lg font-medium text-white mb-1">Click or drag document to upload</p>
                <p className="text-sm text-gray-400">Supports PDF and DOCX exactly up to 20MB</p>
              </div>
            </>
          )}

          {uploadState.status === 'uploading' && (
            <>
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <p className="text-lg font-medium text-white">{uploadState.message}</p>
            </>
          )}

          {uploadState.status === 'success' && (
            <>
              <CheckCircle2 className="w-12 h-12 text-green-500" />
              <p className="text-lg font-medium text-green-400">{uploadState.message}</p>
            </>
          )}

          {uploadState.status === 'error' && (
            <>
              <AlertCircle className="w-12 h-12 text-red-500" />
              <p className="text-lg font-medium text-red-400">{uploadState.message}</p>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setUploadState({ status: 'idle', message: '' });
                }}
                className="mt-2 px-4 py-1.5 bg-white/10 hover:bg-white/20 rounded-md text-sm text-white transition-colors"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
