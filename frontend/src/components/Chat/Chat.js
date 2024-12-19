import React, { useState, useEffect, useRef } from "react";
import DocumentSearch from "../DocumentSearch/DocumentSearch";
import api from "../../services/api";
import "./Chat.css";

function Chat({ token }) {
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
  const websocket = useRef(null);
  const aiMessageRef = useRef("");
  const chatMessagesRef = useRef(null);
  const chatHistoryRef = useRef(null);

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
        if (data.type === "complete") return; // Return after completion messages
        aiMessageRef.current += ` ${data.chunk}`; // Accumulate AI response
        console.log(data.chunk);

        // Update chat history with AI response
        setHistory((prev) => {
          const newHistory = [...prev];
          if (
            newHistory.length &&
            newHistory[newHistory.length - 1]?.role === "ai"
          ) {
            // Update existing AI message if it's the last message
            newHistory[newHistory.length - 1].content = aiMessageRef.current;
          } else {
            // Add new AI message otherwise
            newHistory.push({ role: "ai", content: data.chunk });
          }
          return newHistory;
        });
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

  return (
    // Main application container
    <div className="app-container">
      {/* Header section */}
      <div className="app-header">
        <h1>PolicyAI</h1>
      </div>

      {/* Main content area containing chat and search sections */}
      <div className="main-content">
        {/* Chat interface section */}
        <div className="chat-section">
          {/* Chat controls header */}
          <div className="chat-header">
            <button
              className="button-standard"
              onClick={() => setShowChatHistory(true)}
            >
              Chat History
            </button>
            <button className="button-standard" onClick={handleStartNewChat}>
              New Chat
            </button>
          </div>

          {/* Chat history overlay */}
          {showChatHistory && (
            <div className="chat-history-overlay">
              <div className="chat-history-modal" ref={chatHistoryRef}>
                <h2>Previous Chats</h2>
                {/* List of previous chat sessions */}
                <div className="chat-sessions-list">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      className="chat-session-item"
                      onClick={() => {
                        handleLoadPreviousChat(session.session_id);
                        setShowChatHistory(false);
                      }}
                    >
                      {/* Session information display */}
                      <div className="session-info">
                        {renamingSessionId === session.session_id ? (
                          // Rename input field
                          <input
                            type="text"
                            value={newChatName}
                            onChange={(e) => setNewChatName(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleRenameChat(
                                  session.session_id,
                                  newChatName
                                );
                              }
                            }}
                            placeholder="Enter new name"
                            className="rename-input"
                          />
                        ) : (
                          // Session name display
                          <span className="session-name">
                            {session.name || "Untitled Chat"}
                          </span>
                        )}
                        {/* Session creation date */}
                        <span className="session-date">
                          {new Date(session.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {/* Session action buttons */}
                      <div className="session-actions">
                        {renamingSessionId === session.session_id ? (
                          // Rename mode actions
                          <>
                            <button
                              className="rename-button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRenameChat(
                                  session.session_id,
                                  newChatName
                                );
                              }}
                              title="Save"
                            >
                              Save
                            </button>
                            <button
                              className="rename-button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setRenamingSessionId(null);
                                setNewChatName("");
                              }}
                              title="Cancel"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          // Normal mode actions
                          <button
                            className="rename-button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setRenamingSessionId(session.session_id);
                              setNewChatName(session.name || "");
                            }}
                            title="Rename chat"
                          >
                            ✎
                          </button>
                        )}
                        {/* Delete session button */}
                        <button
                          className="delete-session-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteChat(session.session_id);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Chat messages display area */}
          <div className="chat-messages" ref={chatMessagesRef}>
            {history.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
          </div>

          {/* Chat input area */}
          <div className="chat-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleChat()}
              placeholder="Type your message..."
            />
            <button
              onClick={handleChat}
              disabled={!message.trim() || !currentSessionId}
              className="send-button"
            >
              Send
            </button>
          </div>
        </div>

        {/* Document search section */}
        <div className="search-section">
          <DocumentSearch token={token} />
        </div>
      </div>

      {/* Settings button and panel */}
      {!showSettings ? (
        <button
          className="settings-button"
          onClick={() => {
            setShowSettings(true);
            handleFetchUserData();
            setIsEditingSettings(false);
          }}
        >
          Settings
        </button>
      ) : (
        <div className="settings-panel">
          <div className="settings-header">
            <button
              className="settings-close"
              onClick={() => setShowSettings(false)}
              title="Close settings"
            >
              ×
            </button>
            <h3>User Settings</h3>
          </div>
          {/* Settings form */}
          <div className="settings-form">
            <div className="form-group">
              <label>First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={!isEditingSettings}
                className="settings-input"
              />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                disabled={!isEditingSettings}
                className="settings-input"
              />
            </div>
          </div>
          <div className="settings-footer">
            {isEditingSettings ? (
              <button className="save-button" onClick={handleNameChange}>
                Save
              </button>
            ) : (
              <button
                className="edit-button"
                onClick={() => setIsEditingSettings(true)}
              >
                Edit
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Chat;
