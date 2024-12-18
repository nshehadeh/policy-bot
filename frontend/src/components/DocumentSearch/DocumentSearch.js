import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './DocumentSearch.css';

const DocumentSearch = ({ token }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load initial documents
    fetchDocuments('');
  }, []);

  const fetchDocuments = async (searchQuery) => {
    setLoading(true);
    try {
      const response = await api.get(`/search/?query=${encodeURIComponent(searchQuery)}`, {
        headers: { Authorization: `Token ${token}` },
      });
      setResults(response.data.results || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
    setLoading(false);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchDocuments(query);
  };

  const handleDocumentClick = (document) => {
    setSelectedDocument(document);
  };

  const handleCloseDocument = () => {
    setSelectedDocument(null);
  };

  // Close overlay when clicking outside the document details
  const handleOverlayClick = (e) => {
    if (e.target.classList.contains('document-overlay')) {
      setSelectedDocument(null);
    }
  };

  return (
    <div className="document-search">
      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents..."
            className="search-input"
          />
          <button type="submit" className="search-button">
            Search
          </button>
        </form>
      </div>

      <div className="documents-container">
        <div className="documents-grid">
          {loading ? (
            <div className="loading">Loading...</div>
          ) : (
            results.map((doc) => (
              <div
                key={doc.id}
                className="document-card"
                onClick={() => handleDocumentClick(doc)}
              >
                <h3 className="document-title">{doc.title}</h3>
                <div className="document-preview">
                  {doc.summary.substring(0, 150)}...
                </div>
              </div>
            ))
          )}
        </div>

        {selectedDocument && (
          <div className="document-overlay" onClick={handleOverlayClick}>
            <div className="document-details">
              <button className="close-button" onClick={handleCloseDocument}>
                ×
              </button>
              <h2>{selectedDocument.title}</h2>
              <p className="document-summary">{selectedDocument.summary}</p>
              {selectedDocument.url && (
                <a
                  href={selectedDocument.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="document-link"
                >
                  View Original Document
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentSearch;