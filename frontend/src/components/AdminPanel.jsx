import React, { useState } from 'react';
import './AdminPanel.css';

const CATEGORIES = [
    { value: 'timetable', label: 'Timetable' },
    { value: 'regulations', label: 'Regulations' },
    { value: 'admissions', label: 'Admissions' },
    { value: 'general', label: 'General' },
    { value: 'fees', label: 'Fees' },
];

const AdminPanel = () => {
    // File Upload State
    const [fileUpload, setFileUpload] = useState({
        file: null,
        category: 'regulations',
        department: '',
        academicYear: '',
        loading: false,
        result: null,
        error: null,
    });

    // Text Ingestion State
    const [textIngestion, setTextIngestion] = useState({
        content: '',
        category: 'regulations',
        department: '',
        academicYear: '',
        loading: false,
        result: null,
        error: null,
    });

    // File Upload Handlers
    const handleFileChange = (e) => {
        setFileUpload({ ...fileUpload, file: e.target.files[0], result: null, error: null });
    };

    const handleFileSubmit = async (e) => {
        e.preventDefault();

        if (!fileUpload.file) {
            setFileUpload({ ...fileUpload, error: { message: 'Please select a file' } });
            return;
        }

        setFileUpload({ ...fileUpload, loading: true, result: null, error: null });

        try {
            const formData = new FormData();
            formData.append('file', fileUpload.file);
            formData.append('category', fileUpload.category);
            formData.append('department', fileUpload.department);
            formData.append('academic_year', fileUpload.academicYear);

            const response = await fetch('http://localhost:8000/api/upload/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            // Check if response indicates failure
            if (!response.ok || data.success === false) {
                setFileUpload({
                    ...fileUpload,
                    loading: false,
                    error: data,
                });
                return;
            }

            setFileUpload({
                ...fileUpload,
                loading: false,
                result: data,
                error: null,
                file: null,
            });

            // Reset form
            e.target.reset();
        } catch (error) {
            setFileUpload({
                ...fileUpload,
                loading: false,
                error: { message: error.message },
            });
        }
    };

    // Template download function
    const downloadTemplate = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/upload/download-template');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'timetable_template.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Template download failed:', error);
        }
    };

    // Template download function for all categories
    const downloadTemplateFile = async (category) => {
        try {
            const response = await fetch(`http://localhost:8000/api/upload/download-template/${category}`);
            if (!response.ok) {
                throw new Error('Failed to download template');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${category}_template.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Template download failed:', error);
            alert(`Failed to download template: ${error.message}`);
        }
    };

    // Text Ingestion Handlers
    const handleTextSubmit = async (e) => {
        e.preventDefault();

        if (!textIngestion.content.trim()) {
            setTextIngestion({ ...textIngestion, error: 'Please enter content' });
            return;
        }

        setTextIngestion({ ...textIngestion, loading: true, result: null, error: null });

        try {
            const response = await fetch('http://localhost:8000/api/upload/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: textIngestion.content,
                    category: textIngestion.category,
                    department: textIngestion.department,
                    academic_year: textIngestion.academicYear,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Text ingestion failed');
            }

            setTextIngestion({
                ...textIngestion,
                loading: false,
                result: data,
                error: null,
                content: '',
            });
        } catch (error) {
            setTextIngestion({
                ...textIngestion,
                loading: false,
                error: error.message,
            });
        }
    };

    return (
        <div className="admin-panel">
            <div className="admin-container">
                <header className="admin-header">
                    <h1>📚 Admin Content Management</h1>
                    <p>Upload files or add text content to the EduVerse knowledge base</p>
                </header>

                <div className="admin-sections">
                    {/* File Upload Section */}
                    <section className="admin-section">
                        <h2>📁 File Upload</h2>
                        <p className="section-description">
                            Upload PDF, CSV, XLSX, or image files. Timetable files will be parsed into structured data.
                        </p>

                        <form onSubmit={handleFileSubmit} className="admin-form">
                            <div className="form-group">
                                <label htmlFor="file-input">File</label>
                                <input
                                    id="file-input"
                                    type="file"
                                    onChange={handleFileChange}
                                    accept=".pdf,.csv,.xlsx,.xls,.png,.jpg,.jpeg"
                                    className="file-input"
                                    disabled={fileUpload.loading}
                                />
                                {fileUpload.file && (
                                    <span className="file-name">Selected: {fileUpload.file.name}</span>
                                )}
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="file-category">Category</label>
                                    <select
                                        id="file-category"
                                        value={fileUpload.category}
                                        onChange={(e) => setFileUpload({ ...fileUpload, category: e.target.value })}
                                        className="form-select"
                                        disabled={fileUpload.loading}
                                    >
                                        {CATEGORIES.map((cat) => (
                                            <option key={cat.value} value={cat.value}>
                                                {cat.label}
                                            </option>
                                        ))}
                                    </select>
                                    {/* Template Download Button */}
                                    {['timetable', 'admissions', 'fees', 'regulations'].includes(fileUpload.category) && (
                                        <button
                                            type="button"
                                            onClick={() => downloadTemplateFile(fileUpload.category)}
                                            className="template-button"
                                            style={{ marginTop: '8px' }}
                                        >
                                            📥 Download {fileUpload.category.charAt(0).toUpperCase() + fileUpload.category.slice(1)} Template
                                        </button>
                                    )}
                                </div>

                                <div className="form-group">
                                    <label htmlFor="file-department">Department</label>
                                    <input
                                        id="file-department"
                                        type="text"
                                        value={fileUpload.department}
                                        onChange={(e) => setFileUpload({ ...fileUpload, department: e.target.value })}
                                        placeholder="e.g., Computer Science"
                                        className="form-input"
                                        disabled={fileUpload.loading}
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="file-year">Academic Year</label>
                                    <input
                                        id="file-year"
                                        type="text"
                                        value={fileUpload.academicYear}
                                        onChange={(e) => setFileUpload({ ...fileUpload, academicYear: e.target.value })}
                                        placeholder="e.g., 2024-2025"
                                        className="form-input"
                                        disabled={fileUpload.loading}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={!fileUpload.file || fileUpload.loading}
                                className="submit-button"
                            >
                                {fileUpload.loading ? (
                                    <>
                                        <span className="spinner-small"></span> Uploading...
                                    </>
                                ) : (
                                    '📤 Upload File'
                                )}
                            </button>

                            {/* Error Display - Missing Columns */}
                            {fileUpload.error && fileUpload.error.error_type === 'missing_columns' && (
                                <div className="alert alert-error-detailed">
                                    <div className="alert-header">
                                        <span className="alert-icon">❌</span>
                                        <strong>Upload Failed - Missing Required Columns</strong>
                                    </div>
                                    <div className="alert-body">
                                        <p>Your file is missing the following required columns:</p>
                                        <ul className="missing-columns-list">
                                            {fileUpload.error.missing_columns.map((col) => (
                                                <li key={col}><code>{col}</code></li>
                                            ))}
                                        </ul>
                                        <p className="help-text">
                                            <strong>Found columns:</strong> {fileUpload.error.found_columns.join(', ')}
                                        </p>
                                        <button
                                            type="button"
                                            onClick={downloadTemplate}
                                            className="template-button"
                                        >
                                            📥 Download Timetable Template
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Error Display - Other Errors */}
                            {fileUpload.error && fileUpload.error.error_type !== 'missing_columns' && (
                                <div className="alert alert-error">
                                    <div className="alert-header">
                                        <span className="alert-icon">❌</span>
                                        <strong>Error</strong>
                                    </div>
                                    <p>{fileUpload.error.message || fileUpload.error}</p>
                                </div>
                            )}

                            {/* Success Display */}
                            {fileUpload.result && fileUpload.result.success && (
                                <div className="alert alert-success">
                                    <div className="alert-header">
                                        <span className="alert-icon">✓</span>
                                        <strong>Upload Successful!</strong>
                                    </div>
                                    <div className="stats-grid">
                                        <div className="stat-card">
                                            <div className="stat-value">{fileUpload.result.total_rows || fileUpload.result.chunks_created || 'N/A'}</div>
                                            <div className="stat-label">
                                                {fileUpload.result.category === 'timetable' ? 'Total Classes' : 'Chunks Created'}
                                            </div>
                                        </div>
                                        {fileUpload.result.unique_teachers && (
                                            <div className="stat-card">
                                                <div className="stat-value">{fileUpload.result.unique_teachers}</div>
                                                <div className="stat-label">Unique Teachers</div>
                                            </div>
                                        )}
                                        {fileUpload.result.entries_inserted !== undefined && (
                                            <div className="stat-card">
                                                <div className="stat-value">{fileUpload.result.entries_inserted}</div>
                                                <div className="stat-label">Stored Successfully</div>
                                            </div>
                                        )}
                                        {fileUpload.result.total_characters && (
                                            <div className="stat-card">
                                                <div className="stat-value">{fileUpload.result.total_characters}</div>
                                                <div className="stat-label">Total Characters</div>
                                            </div>
                                        )}
                                    </div>
                                    {fileUpload.result.invalid_rows && fileUpload.result.invalid_rows.length > 0 && (
                                        <div className="warning-section">
                                            <p><strong>⚠️ Warning:</strong> {fileUpload.result.invalid_rows.length} row(s) had errors and were skipped.</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </form>
                    </section>

                    {/* Text Ingestion Section */}
                    <section className="admin-section">
                        <h2>📝 Direct Text Ingestion</h2>
                        <p className="section-description">
                            Paste text content directly. Content will be chunked and embedded for RAG retrieval.
                        </p>

                        <form onSubmit={handleTextSubmit} className="admin-form">
                            <div className="form-group">
                                <label htmlFor="text-content">Content</label>
                                <textarea
                                    id="text-content"
                                    value={textIngestion.content}
                                    onChange={(e) => setTextIngestion({ ...textIngestion, content: e.target.value })}
                                    placeholder="Paste your content here..."
                                    rows={10}
                                    className="form-textarea"
                                />
                                <span className="char-count">
                                    {textIngestion.content.length} characters
                                </span>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="text-category">Category</label>
                                    <select
                                        id="text-category"
                                        value={textIngestion.category}
                                        onChange={(e) => setTextIngestion({ ...textIngestion, category: e.target.value })}
                                        className="form-select"
                                    >
                                        {CATEGORIES.filter(cat => cat.value !== 'timetable').map((cat) => (
                                            <option key={cat.value} value={cat.value}>
                                                {cat.label}
                                            </option>
                                        ))}
                                    </select>
                                    <small className="form-hint">
                                        Note: Timetable requires structured CSV/XLSX upload
                                    </small>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="text-department">Department</label>
                                    <input
                                        id="text-department"
                                        type="text"
                                        value={textIngestion.department}
                                        onChange={(e) => setTextIngestion({ ...textIngestion, department: e.target.value })}
                                        placeholder="e.g., Computer Science"
                                        className="form-input"
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="text-year">Academic Year</label>
                                    <input
                                        id="text-year"
                                        type="text"
                                        value={textIngestion.academicYear}
                                        onChange={(e) => setTextIngestion({ ...textIngestion, academicYear: e.target.value })}
                                        placeholder="e.g., 2024-2025"
                                        className="form-input"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={!textIngestion.content.trim() || textIngestion.loading}
                                className="submit-button"
                            >
                                {textIngestion.loading ? (
                                    <>
                                        <span className="spinner-small"></span> Processing...
                                    </>
                                ) : (
                                    '✨ Ingest Text'
                                )}
                            </button>

                            {textIngestion.error && (
                                <div className="alert alert-error">
                                    <strong>Error:</strong> {textIngestion.error}
                                </div>
                            )}

                            {textIngestion.result && (
                                <div className="alert alert-success">
                                    <strong>✓ Success!</strong>
                                    <ul>
                                        <li>{textIngestion.result.message}</li>
                                        <li>Chunks created: {textIngestion.result.chunks_created}</li>
                                        <li>Total characters: {textIngestion.result.total_characters}</li>
                                        <li>Category: {textIngestion.result.category}</li>
                                    </ul>
                                </div>
                            )}
                        </form>
                    </section>
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;
