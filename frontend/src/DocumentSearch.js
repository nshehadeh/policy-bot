import React, { useState, useEffect } from 'react';
import api from './api';
import './DocumentSearch.css';

function DocumentSearch({ token }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(false);

    // Fetch initial documents on component mount
    useEffect(() => {
        const fetchInitialDocuments = async () => {
            try {
                const res = await api.get('/search/', {
                    headers: { Authorization: `Token ${token}` },
                });
                setSearchResults(res.data.results);
            } catch (error) {
                console.error('Error fetching initial documents:', error);
            }
        };
        fetchInitialDocuments();
    }, [token]);

    const handleSearch = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/search/?query=${encodeURIComponent(searchQuery)}`, {
                headers: { Authorization: `Token ${token}` },
            });
            setSearchResults(res.data.results);
        } catch (error) {
            console.error('Error searching:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="document-search-container">
            <div className="search-bar">
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Search documents..."
                    className="search-input"
                />
                <button 
                    onClick={handleSearch}
                    className="search-button"
                    disabled={loading}
                >
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>
            
            <div className="document-cards">
                {searchResults.map((doc, index) => (
                    <div key={doc.id} className="document-card">
                        <h3>{doc.title}</h3>
                        <p className="document-summary">{doc.summary}</p>
                        <div className="document-meta">
                            <span className="document-date">
                                {new Date(doc.publication_date).toLocaleDateString()}
                            </span>
                            <a 
                                href={doc.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="document-link"
                            >
                                View Document
                            </a>
                        </div>
                    </div>
                ))}
                {searchResults.length === 0 && !loading && (
                    <div className="no-results">No documents found</div>
                )}
            </div>
        </div>
    );
}

export default DocumentSearch;