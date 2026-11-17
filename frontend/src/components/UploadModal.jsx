import { useState, useEffect, useRef } from 'react';
import {
  FiUploadCloud,
  FiFileText,
  FiX,
  FiCheckCircle,
  FiAlertCircle,
  FiRefreshCw,
  FiFile,
  FiClock,
  FiLayers,
} from 'react-icons/fi';
import { useToast } from '../context/ToastContext';
import './UploadModal.css';

const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

export default function UploadModal({ isOpen, onClose, onSuccess, companyId }) {
  const { addToast } = useToast();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [recentUploads, setRecentUploads] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (isOpen && companyId) {
      fetchUploadHistory();
    }
  }, [isOpen, companyId]);

  const fetchUploadHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API}/api/companies/${companyId}/uploads`);
      if (res.ok) {
        const data = await res.json();
        setRecentUploads(data);
      }
    } catch (err) {
      console.error('Failed to load upload history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      addToast('Please select a file to upload', 'warning');
      return;
    }

    setUploading(true);
    addToast(`Uploading and analyzing '${selectedFile.name}'...`, 'info');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API}/api/companies/${companyId}/uploads`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Upload processing failed');
      }

      addToast(
        `Extracted ${data.signals_created_count} internal signals from '${selectedFile.name}'!`,
        'success'
      );
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchUploadHistory();
      if (onSuccess) onSuccess(data);
    } catch (err) {
      console.error('Upload error:', err);
      addToast('Upload failed: ' + err.message, 'error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-modal-overlay" onClick={onClose}>
      <div className="upload-modal-card card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="upload-modal-header">
          <div className="upload-header-left">
            <span className="upload-header-icon"><FiUploadCloud /></span>
            <div>
              <h2 className="upload-modal-title">Internal Intelligence Upload</h2>
              <p className="upload-modal-subtitle">
                Upload sales objection logs, CRM lost-deal exports, or feedback documents (CSV, XLSX, PDF, TXT).
              </p>
            </div>
          </div>
          <button type="button" className="upload-close-btn" onClick={onClose} title="Close modal">
            <FiX />
          </button>
        </div>

        {/* Drag and Drop Zone */}
        <div
          className={`upload-dropzone ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".csv,.xlsx,.xls,.pdf,.txt,.md"
            onChange={handleFileChange}
          />

          <div className="dropzone-content">
            <span className="dropzone-icon">
              {selectedFile ? <FiCheckCircle style={{ color: 'var(--secondary)' }} /> : <FiUploadCloud />}
            </span>

            {selectedFile ? (
              <div className="dropzone-file-info">
                <span className="selected-filename">{selectedFile.name}</span>
                <span className="selected-filesize">
                  {(selectedFile.size / 1024).toFixed(1)} KB • Click to choose a different file
                </span>
              </div>
            ) : (
              <div className="dropzone-prompts">
                <span className="dropzone-main-text">
                  Drag and drop your file here, or <strong>browse files</strong>
                </span>
                <span className="dropzone-sub-text">
                  Supported formats: <strong>CSV</strong> (CRM lost-deal export), <strong>XLSX</strong>, <strong>PDF</strong>, <strong>TXT</strong>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="upload-modal-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
            disabled={uploading}
          >
            Cancel
          </button>

          <button
            type="button"
            className="btn-primary"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? <FiRefreshCw className="spin-icon" /> : <FiLayers />}
            <span>{uploading ? 'Extracting Signals...' : 'Extract Internal Signals'}</span>
          </button>
        </div>

        {/* Upload History Section */}
        {recentUploads.length > 0 && (
          <div className="upload-history-wrap">
            <div className="upload-history-header">
              <span className="history-title"><FiFileText /> Previously Uploaded Intelligence</span>
              <span className="history-count">{recentUploads.length} Files</span>
            </div>

            <div className="upload-history-list">
              {recentUploads.map((up) => (
                <div key={up.id} className="history-item">
                  <div className="history-file-meta">
                    <span className={`file-kind-badge kind-${up.kind}`}>
                      {up.kind.toUpperCase()}
                    </span>
                    <span className="history-filename">{up.filename}</span>
                  </div>
                  <div className="history-date-meta">
                    <FiClock />
                    <span>{new Date(up.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
