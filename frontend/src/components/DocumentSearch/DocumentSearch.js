import React, { useState, useEffect } from "react";
import api from "../../services/api";
import "./DocumentSearch.css";

// DocumentSearch component for searching and displaying document results
const DocumentSearch = ({ token }) => {
  // State management for search functionality
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load initial documents
    fetchDocuments("");
  }, []);

  // Fetch documents from the API based on search query
  const fetchDocuments = async (searchQuery) => {
    setLoading(true);
    try {
      const response = await api.get(
        `/search/?query=${encodeURIComponent(searchQuery)}`,
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setResults(response.data.results || []); // Update results, default to empty array if null
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
    setLoading(false);
  };

  // Handle search form submission
  const handleSearch = (e) => {
    e.preventDefault();
    fetchDocuments(query);
  };

  // Set the selected document for detailed view
  const handleDocumentClick = (document) => {
    setSelectedDocument(document);
  };

  // Clear the selected document view
  const handleCloseDocument = () => {
    setSelectedDocument(null);
  };

  // Close document overlay when clicking outside the details panel
  const handleOverlayClick = (e) => {
    if (e.target.classList.contains("document-overlay")) {
      setSelectedDocument(null);
    }
  };

  return (
    // Main document search container
    <div className="document-search">
      {/* Search form section */}
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

      {/* Results display section */}
      <div className="documents-container">
        <div className="documents-grid">
          {loading ? (
            // Loading indicator
            <div className="loading">Loading...</div>
          ) : (
            // Document results grid
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

        {/* Document detail overlay */}
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
