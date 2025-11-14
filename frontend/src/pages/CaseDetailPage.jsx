import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useUser } from '../context/UserContext';
import '../styles/CaseDetail.css';

// Drag and Drop component
const FileDropzone = ({ onFileChange, onUpload, selectedFile }) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };
    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };
    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onFileChange(e.dataTransfer.files[0]);
            e.dataTransfer.clearData();
        }
    };

    return (
        <div 
            className={`dropzone ${isDragging ? 'dragging' : ''}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            <input 
                type="file" 
                id="file-upload" 
                style={{display: 'none'}} 
                onChange={(e) => onFileChange(e.target.files[0])} 
            />
            <label htmlFor="file-upload" className="dropzone-label">
                {selectedFile 
                    ? `Selected: ${selectedFile.name}`
                    : "Drag & drop files here, or click to select"}
            </label>
            <button onClick={onUpload} disabled={!selectedFile} className="upload-button">
                Upload File
            </button>
        </div>
    );
};


const CaseDetailPage = () => {
    const { caseId } = useParams();
    const { user } = useUser();
    const [caseDetails, setCaseDetails] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [permissions, setPermissions] = useState([]);
    const [summary, setSummary] = useState('');
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [status, setStatus] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadError, setUploadError] = useState('');
    const [accessError, setAccessError] = useState('');
    const [searchEmail, setSearchEmail] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const [caseRes, docsRes, permsRes] = await Promise.all([
                axios.get(`/api/case/${caseId}`),
                axios.get(`/api/case/${caseId}/documents`),
                axios.get(`/api/case/${caseId}/permissions`),
            ]);
            setCaseDetails(caseRes.data);
            setDocuments(docsRes.data);
            setPermissions(permsRes.data);
            setStatus(caseRes.data.status);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to load case data.');
        } finally {
            setLoading(false);
        }
    }, [caseId]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleUpload = async () => {
        if (!selectedFile) return;
        const formData = new FormData();
        formData.append('file', selectedFile);
        try {
            await axios.post(`/api/case/${caseId}/upload`, formData);
            setSelectedFile(null);
            fetchData();
        } catch (err) {
            setUploadError(err.response?.data?.error || 'File upload failed.');
        }
    };

    const handleStatusUpdate = async () => {
        try {
            await axios.put(`/api/case/${caseId}/status`, { status });
            fetchData();
        } catch (err) {
            console.error("Error updating status:", err);
        }
    };

    const handleSearchUsers = async () => {
        if (searchEmail.length < 3) return;
        try {
            const res = await axios.get(`/api/users/search?email=${searchEmail}`);
            setSearchResults(res.data);
        } catch (err) {
            console.error("Error searching users:", err);
        }
    };

    const handleGrantAccess = async (accessLevel) => {
        if (!selectedUser) return;
        try {
            await axios.post(`/api/case/${caseId}/grant-access`, {
                user_id: selectedUser.user_id,
                access_level: accessLevel,
            });
            fetchData();
            setSearchEmail('');
            setSearchResults([]);
            setSelectedUser(null);
        } catch (err) {
            setAccessError(err.response?.data?.error || 'Failed to grant access.');
        }
    };

    const handleGenerateSummary = async () => {
        setSummaryLoading(true);
        try {
            const res = await axios.get(`/api/case/${caseId}/summary`);
            setSummary(res.data.summary);
        } catch (err) {
            setSummary('Failed to generate summary.');
        } finally {
            setSummaryLoading(false);
        }
    };
    
    const canManage = user.role === 'judge' || permissions.find(p => p.user_id === user.user_id)?.access_level === 'sudo';

    if (loading) return <div>Loading case details...</div>;
    if (error) return <div className="error-message">{error}</div>;

    return (
        <div className="case-detail-container">
            <div className="case-detail-header">
                <h1>{caseDetails.case_name}</h1>
            </div>

            <div className="case-grid">
                <div className="main-content">
                    <section className="card">
                        <h2>Documents</h2>
                        <FileDropzone 
                            onFileChange={setSelectedFile}
                            onUpload={handleUpload}
                            selectedFile={selectedFile}
                        />
                        {uploadError && <p className="error-message">{uploadError}</p>}
                        <ul className="document-list">
                            {documents.map(doc => (
                                <li key={doc.doc_id}>
                                    <span>{doc.file_name}</span>
                                    <a href={`/api/document/${doc.doc_id}/download`} download={doc.file_name}>Download</a>
                                </li>
                            ))}
                        </ul>
                        {documents.length === 0 && <p>No documents uploaded.</p>}
                    </section>

                    {(user.role === 'judge' || user.role === 'advocate') && (
                        <section className="card">
                            <h2>AI Summary</h2>
                            {summary ? (
                                <p>{summary}</p>
                            ) : (
                                <button onClick={handleGenerateSummary} disabled={summaryLoading}>
                                    {summaryLoading ? 'Generating...' : 'Generate Summary'}
                                </button>
                            )}
                        </section>
                    )}
                </div>

                <div className="sidebar-content">
                    <section className="card">
                        <h2>Case Details</h2>
                        <p><strong>Status:</strong> {caseDetails.status}</p>
                        {canManage && (
                            <div className="status-update-form">
                                <select value={status} onChange={(e) => setStatus(e.target.value)}>
                                    <option value="Open">Open</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="Closed">Closed</option>
                                </select>
                                <button onClick={handleStatusUpdate}>Update Status</button>
                            </div>
                        )}
                    </section>

                    <section className="card">
                        <h2>Collaborators</h2>
                        <ul className="collaborator-list">
                            {permissions.map(p => (
                                <li key={p.user_id}>
                                    <div>
                                        <strong>{p.full_name}</strong>
                                        <small>{p.email}</small>
                                    </div>
                                    <span>{p.access_level}</span>
                                </li>
                            ))}
                        </ul>
                    </section>

                    {canManage && (
                        <section className="card">
                            <h2>Manage Access</h2>
                            <div className="access-form">
                                <input
                                    type="text"
                                    placeholder="Search user by email"
                                    value={searchEmail}
                                    onChange={(e) => setSearchEmail(e.target.value)}
                                />
                                <button onClick={handleSearchUsers}>Search</button>
                            </div>
                            {searchResults.length > 0 && (
                                <ul className="search-results">
                                    {searchResults.map(u => (
                                        <li key={u.user_id} onClick={() => {
                                            setSelectedUser(u);
                                            setSearchEmail(u.email);
                                            setSearchResults([]);
                                        }}>
                                            {u.full_name} ({u.email})
                                        </li>
                                    ))}
                                </ul>
                            )}
                            {selectedUser && (
                                <div className="grant-access-section">
                                    <p>Grant access to <strong>{selectedUser.full_name}</strong>:</p>
                                    <button onClick={() => handleGrantAccess('view_only')}>View Only</button>
                                    <button onClick={() => handleGrantAccess('upload_only')}>Upload Only</button>
                                    <button onClick={() => handleGrantAccess('sudo')}>Full Control (Sudo)</button>
                                </div>
                            )}
                            {accessError && <p className="error-message">{accessError}</p>}
                        </section>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CaseDetailPage;