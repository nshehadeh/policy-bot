import React, { useState, useEffect, useRef } from "react";
import DocumentSearch from "../DocumentSearch/DocumentSearch";
import api from "../../services/api";
//import "./Chat.css";
import "./MChat.css";

function Chat({ token, theme }) {
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [isEditingSettings, setIsEditingSettings] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [newChatName, setNewChatName] = useState("");
  const [currentStep, setCurrentStep] = useState(null);
  const [currentMetadata, setCurrentMetadata] = useState(null);
  const [documentDetails, setDocumentDetails] = useState({});
  const [selectedDocument, setSelectedDocument] = useState(null);
  const websocket = useRef(null);
  const aiMessageRef = useRef("");
  const chatMessagesRef = useRef(null);
  const chatHistoryRef = useRef(null);
  // const [theme, setTheme] = useState('dark');

  // Step to display text mapping
  const stepDisplayMap = {
    history: "Analyzing Chat Context",
    grade_documents: "Evaluating Sources",
    agent: "Planning Response",
    rewrite: "Refining Query",
    retrieve: "Retrieving Documents",
    generate: "Generating Response",
    direct_response: "Generating Response",
    end: "Done"
  };

  // Automatically scroll chat to the bottom when new messages arrive
  const scrollToBottom = () => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  };

  // Scroll to bottom whenever chat history updates
  useEffect(() => {
    scrollToBottom();
  }, [history]);

  // Initialize chat sessions on component mount
  useEffect(() => {
    const fetchChatSessions = async () => {
      try {
        const sessionsRes = await api.get("/chat/sessions/", {
          headers: { Authorization: `Token ${token}` },
        });
        setSessions(sessionsRes.data);
      } catch (error) {
        console.error("Error fetching chat sessions:", error);
      }
    };
    fetchChatSessions();
  }, [token]);

  // WebSocket connection management
  useEffect(() => {
    if (currentSessionId) {
      console.log(
        `Trying to open WebSocket connection to: ws://localhost:8000/ws/chat/${currentSessionId}/`
      );

      // Close existing WebSocket connection if open
      if (
        websocket.current &&
        websocket.current.readyState === WebSocket.OPEN
      ) {
        console.log("Closing existing WebSocket connection");
        websocket.current.close();
      }

      // Initialize new WebSocket connection for current chat session
      console.log(
        `Opening WebSocket connection for session: ${currentSessionId}`
      );
      websocket.current = new WebSocket(
        `ws://localhost:8000/ws/chat/${currentSessionId}/?token=${token}`
      );

      // WebSocket event handlers
      websocket.current.onopen = () => {
        console.log("WebSocket connection opened.");
      };

      // Handle incoming messages from AI
      websocket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "complete") {
          setCurrentStep("end");
          return;
        }

        if (data.type === "step") {
          setCurrentStep(data.step);
          // Create an empty AI message if this is the first step and there's no AI message yet
          setHistory((prev) => {
            if (!prev.length || prev[prev.length - 1].role !== "ai") {
              return [...prev, { role: "ai", content: "", metadata: [] }];
            }
            return prev;
          });
          return;
        }

        if (data.type === "metadata") {
          console.log("Raw metadata received:", data.metadata);
          const metadata = Array.isArray(data.metadata) ? data.metadata : [];
          setCurrentMetadata(metadata);
          setHistory((prev) => {
            const newHistory = [...prev];
            if (newHistory.length && newHistory[newHistory.length - 1]?.role === "ai") {
              newHistory[newHistory.length - 1].metadata = metadata;
            }
            return newHistory;
          });
          return;
        }

        if (data.type === "chunk") {
          aiMessageRef.current += data.chunk;
          setHistory((prev) => {
            const newHistory = [...prev];
            if (
              newHistory.length &&
              newHistory[newHistory.length - 1]?.role === "ai"
            ) {
              newHistory[newHistory.length - 1].content = aiMessageRef.current;
              newHistory[newHistory.length - 1].metadata = currentMetadata || [];
            } else {
              newHistory.push({ 
                role: "ai", 
                content: data.chunk, 
                metadata: currentMetadata || [] 
              });
            }
            return newHistory;
          });
        }
      };

      // Connection closure handler
      websocket.current.onclose = () => {
        console.log("WebSocket connection closed.");
      };

      // Error handler
      websocket.current.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      // Cleanup function for component unmount or session change
      return () => {
        websocket.current.close();
      };
    }
  }, [currentSessionId, token]);

  // Fetch document details when metadata is received
  const fetchDocumentDetails = async (documentIds) => {
    try {
      console.log("Fetching details for documents:", documentIds);
      const response = await api.post(
        "/documents/retrieve/",
        { document_ids: documentIds },
        { headers: { Authorization: `Token ${token}` } }
      );
      console.log("Received document details:", response.data);
      const newDetails = {};
      response.data.forEach(doc => {
        if (doc && doc.id) {
          newDetails[doc.id] = doc;
        }
      });
      console.log("Processed document details:", newDetails);
      setDocumentDetails(newDetails);
    } catch (error) {
      console.error("Error fetching document details:", error);
    }
  };

  // Update metadata handling
  useEffect(() => {
    if (currentMetadata) {
      console.log("Current metadata structure:", JSON.stringify(currentMetadata, null, 2));
      const documentIds = currentMetadata;
      console.log("Document IDs to fetch:", documentIds);
      if (documentIds.length > 0) {
        fetchDocumentDetails(documentIds);
      }
    }
  }, [currentMetadata]);

  // Load a previous chat session and its history
  const handleLoadPreviousChat = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setHistory([]); // Clear current chat history

    try {
      const res = await api.post(
        "/chat/load/",
        { session_id: sessionId },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      console.log("Loaded Chat History:", res.data.chat_history);
      setHistory(res.data.chat_history || []); // Update with loaded history
    } catch (error) {
      console.error("Error loading chat history:", error);
    }
  };

  // Handle sending a new message in current chat
  const handleChat = () => {
    if (!currentSessionId) {
      // Create new session if none exists
      handleStartNewChat();
      return;
    }
    // Add user message to chat history
    aiMessageRef.current = "";
    setHistory((prev) => [...prev, { role: "human", content: message }]);

    // Move current session to top of list since it's being used
    setSessions(prevSessions => {
      const selectedSession = prevSessions.find(s => s.session_id === currentSessionId);
      const otherSessions = prevSessions.filter(s => s.session_id !== currentSessionId);
      return [selectedSession, ...otherSessions];
    });

    // Send message through WebSocket if connection is open
    if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
      websocket.current.send(
        JSON.stringify({
          message: message,
        })
      );
      setMessage(""); // Clear input field
    }
  };

  // Start a new chat session
  const handleStartNewChat = async () => {
    try {
      let data = {};
      // Include message in new chat if present
      if (message.trim()) {
        data = { message };
      }
      console.log("Token being used:", token);

      // Create new chat session
      const res = await api.post("/chat/new/", data, {
        headers: { Authorization: `Token ${token}` },
      });

      setHistory([]);
      setCurrentSessionId(res.data.session_id);

      // Handle initial message if provided
      if (data.message) {
        setHistory([{ role: "human", content: message }]);
        if (
          websocket.current &&
          websocket.current.readyState === WebSocket.OPEN
        ) {
          websocket.current.send(
            JSON.stringify({
              message: data.message,
            })
          );
        }
        setMessage("");
      }

      // Refresh chat sessions list
      const sessionsRes = await api.get("/chat/sessions/", {
        headers: { Authorization: `Token ${token}` },
      });
      setSessions(sessionsRes.data);
    } catch (error) {
      console.error("Error starting new chat:", error);
    }
  };

  // Update user's name in settings
  const handleNameChange = async () => {
    try {
      await api.post(
        "/user_settings/",
        { first_name: firstName, last_name: lastName },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setShowSettings(false);
      setIsEditingSettings(false);
    } catch (error) {
      console.error("Error updating name:", error);
    }
  };

  // Fetch user's current settings
  const handleFetchUserData = async () => {
    try {
      const userRes = await api.get("/user_settings/", {
        headers: { Authorization: `Token ${token}` },
      });
      setFirstName(userRes.data.first_name);
      setLastName(userRes.data.last_name);
    } catch (error) {
      console.error("Error fetching user data:", error);
    }
  };

  // Delete a chat session
  const handleDeleteChat = async (sessionId) => {
    try {
      await api.delete(`/chat/sessions/${sessionId}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      // Remove session from local state
      setSessions(
        sessions.filter((session) => session.session_id !== sessionId)
      );
      // Clear current session if it was deleted
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setHistory([]);
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
    }
  };

  // Rename a chat session
  const handleRenameChat = async (sessionId, newName) => {
    try {
      await api.patch(
        `/chat/sessions/${sessionId}/`,
        { name: newName },
        { headers: { Authorization: `Token ${token}` } }
      );
      // Update session name in local state
      setSessions(
        sessions.map((session) =>
          session.session_id === sessionId
            ? { ...session, name: newName }
            : session
        )
      );
      setRenamingSessionId(null);
      setNewChatName("");
    } catch (error) {
      console.error("Error renaming chat:", error);
    }
  };

  // Handle clicking outside chat history panel to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        chatHistoryRef.current &&
        !chatHistoryRef.current.contains(event.target)
      ) {
        setShowChatHistory(false);
      }
    };

    // Add click listener when chat history is shown
    if (showChatHistory) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    // Cleanup listener on unmount or when chat history is hidden
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showChatHistory]);

  // Handle document click
  const handleDocumentClick = (document) => {
    setSelectedDocument(document);
  };

  // Handle closing document modal
  const handleCloseDocument = () => {
    setSelectedDocument(null);
  };

  // Handle overlay click
  const handleOverlayClick = (e) => {
    if (e.target.classList.contains("document-overlay")) {
      setSelectedDocument(null);
    }
  };

  return (
    
    <div className={`flex flex-col chat-tab overflow-hidden theme-${theme}`}>
      {/* Main Container for side-by-side layout */}
      <div className="flex flex-1 min-h-0 w-full">
        {/* Chat Section */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Sub Header */}
          <div className="app-header p-4">
            <div className="flex justify-between items-center max-w-7xl mx-auto">
              <button
                onClick={() => setShowChatHistory(true)}
                className="history-button px-4 py-2 text-white rounded-lg transition-all hover:scale-105"
              >
                Chat History
              </button>
              <button
                onClick={handleStartNewChat}
                className="history-button px-4 py-2 text-white rounded-lg transition-all hover:scale-105"
              >
                New Chat
              </button>
            </div>
          </div>

          {/* Chat Messages */}
          <div 
            ref={chatMessagesRef}
            className="chat-messages flex-1 overflow-y-auto scroll-smooth"
          >
            {history.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'human' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`message-bubble ${msg.role === 'human' ? 'human' : ''}`}
                >
                  {msg.role === "ai" && currentStep && index === history.length - 1 && (
                    <div className="ai-step">
                      <span>{stepDisplayMap[currentStep] || currentStep}</span>
                      {currentStep !== "end" && (
                        <div className="loading-dots">
                          <div></div>
                          <div></div>
                          <div></div>
                        </div>
                      )}
                    </div>
                  )}
                  {msg.content}
                  {msg.role === "ai" && msg.metadata && (
                    <div className="sources-section mt-4 text-sm border-t border-gray-600 pt-2">
                      <div className="flex flex-wrap gap-2 relative">
                        {msg.metadata.map((docId, idx) => {
                          console.log("Processing document ID:", docId);
                          const docDetails = documentDetails[docId];
                          console.log("Document details:", docDetails);
                          return (
                            <div 
                              key={idx}
                              className="source-tag px-1.5 py-0.5 bg-gray-700 rounded-lg text-gray-300 cursor-pointer hover:bg-gray-600 transition-colors relative group"
                              onClick={() => docDetails && handleDocumentClick(docDetails)}
                            >
                              <span>{`Source ${idx + 1}`}</span>
                              <div className="invisible group-hover:visible absolute left-0 bottom-[calc(100%+0.5rem)] p-2 bg-gray-900 rounded-lg shadow-lg z-10 whitespace-nowrap border border-gray-700">
                                <div className="text-white">
                                  {docDetails ? docDetails.title : `Loading...`}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <div className="input-container">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              placeholder="Type your message..."
              className="chat-input"
            />
            <button
              onClick={handleChat}
              disabled={!message.trim() || !currentSessionId}
              className="history-button px-6 py-3 text-white rounded-lg transition-all hover:scale-105 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="divider w-px" />

        {/* Document Search Section */}
        <div className={`flex-1 min-w-0 search-section ${theme === 'dark' ? 'theme-dark' : 'theme-light'}`}>
          <DocumentSearch token={token} theme={theme} />
        </div>
      </div>

      {/* Modals */}
      {showSettings && (
        <div className="modal-backdrop fixed inset-0 flex items-center justify-center p-4 z-50">
          <div className="modal-content p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold settings-label">User Settings</h3>
              <button
                className="settings-close"
                onClick={() => setShowSettings(false)}
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm settings-label">First Name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  disabled={!isEditingSettings}
                  className="settings-input w-full rounded-lg px-3 py-2"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm settings-label">Last Name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  disabled={!isEditingSettings}
                  className="settings-input w-full rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              {isEditingSettings ? (
                <button
                  className="search-button px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                  onClick={handleNameChange}
                >
                  Save
                </button>
              ) : (
                <button
                  className=" px-4 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-colors"
                  onClick={() => setIsEditingSettings(true)}
                >
                  Edit
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {showChatHistory && (
        <div className="modal-backdrop fixed inset-0 flex items-center justify-center p-4 z-50">
          <div 
            ref={chatHistoryRef}
            className="modal-content"
          >
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-100">Previous Chats</h2>
            </div>
            
            <div className="overflow-y-auto max-h-[calc(80vh-8rem)]">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="p-4 hover:bg-gray-700 transition-colors cursor-pointer"
                  onClick={() => {
                    handleLoadPreviousChat(session.session_id);
                    setShowChatHistory(false);
                  }}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      {renamingSessionId === session.session_id ? (
                        <input
                          type="text"
                          value={newChatName}
                          onChange={(e) => setNewChatName(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              handleRenameChat(session.session_id, newChatName);
                            }
                          }}
                          className="bg-gray-600 text-gray-100 rounded px-2 py-1 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="Enter new name"
                        />
                      ) : (
                        <span className="text-gray-100">
                          {session.name || "Untitled Chat"}
                        </span>
                      )}
                      <span className="text-sm text-gray-400 block mt-1">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {renamingSessionId === session.session_id ? (
                        <>
                          <button
                            className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRenameChat(session.session_id, newChatName);
                            }}
                          >
                            Save
                          </button>
                          <button
                            className="px-3 py-1 bg-gray-600 text-gray-200 rounded-lg hover:bg-gray-500 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              setRenamingSessionId(null);
                              setNewChatName("");
                            }}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          className="p-2 text-gray-400 hover:text-gray-200 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenamingSessionId(session.session_id);
                            setNewChatName(session.name || "");
                          }}
                        >
                          ✎
                        </button>
                      )}
                      <button
                        className="p-2 text-red-400 hover:text-red-300 transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteChat(session.session_id);
                        }}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

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
}

export default Chat;
