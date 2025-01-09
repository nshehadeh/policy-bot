// Required imports for React functionality and styling
import React, { useState, useEffect, useCallback, useRef } from "react";
import api from "../../services/api";
// import "./DocumentSearch.css";

// DocumentSearch component for searching and displaying document results
const DocumentSearch = ({ token, theme }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [loading, setLoading] = useState(false);
  const initialFetchDone = useRef(false);

  // Fetch documents from the API based on search query
  const fetchDocuments = useCallback(
    async (searchQuery) => {
      setLoading(true);
      try {
        const response = await api.get(
          `/documents/search/?query=${encodeURIComponent(searchQuery)}`,
        );
        setResults(response.data.results || []); // Update results, default to empty array if null
      } catch (error) {
        console.error("Error fetching documents:", error);
      }
      setLoading(false);
    },
    [token]
  );

  // Load initial documents when component mounts
  useEffect(() => {
    if (!initialFetchDone.current) {
      fetchDocuments("");
      initialFetchDone.current = true;
    }
  }, [fetchDocuments]);

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
    <div className={`h-full flex flex-col ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-100'} p-4`}>
      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents..."
            className={`flex-1 rounded-lg px-4 py-2 border focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
              theme === 'dark' 
                ? 'bg-gray-800 text-gray-100 border-gray-700' 
                : 'bg-white text-gray-900 border-gray-200'
            }`}
          />
          <button
            type="submit"
            className="search-button px-4 py-2 bg-indigo-600 text-white rounded-lg transition-all hover:bg-indigo-500 hover:scale-105"
          >
            Search
          </button>
        </div>
      </form>

      {/* Results Grid */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>Loading...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {results.map((doc) => (
              <div
                key={doc.id}
                onClick={() => handleDocumentClick(doc)}
                className={`document-card ${theme === 'dark' ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-gray-50 border-gray-100 hover:bg-white'} rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg hover:scale-[1.02]`}
              >
                <h3 className={`document-title ${theme === 'dark' ? 'text-gray-100' : 'text-gray-800'} text-lg font-semibold mb-2`}>
                  {doc.title}
                </h3>
                <div className={`document-summary ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} text-sm`}>
                  {doc.summary.substring(0, 150)}...
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document Detail Modal */}
      {selectedDocument && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center p-4 z-50 document-overlay"
          onClick={handleOverlayClick}
        >
          <div className={`document-modal ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-xl`}>
            <div className="document-modal-header flex justify-between items-start p-6 border-b border-gray-700">
              <h2 className={`text-xl font-semibold ${theme === 'dark' ? 'text-gray-100' : 'text-gray-800'}`}>
                {selectedDocument.title}
              </h2>
              <button
                onClick={handleCloseDocument}
                className="text-gray-400 hover:text-gray-200 text-2xl transition-colors"
              >
                ×
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-8rem)]">
              <p className={`text-gray-300 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} whitespace-pre-wrap text-left`}>
                {selectedDocument.summary}
              </p>
              {selectedDocument.url && (
                <a
                  href={selectedDocument.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                >
                  View Original Document
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentSearch;