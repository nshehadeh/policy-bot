import React, { useState, useEffect, useRef } from "react";
import DocumentSearch from "../DocumentSearch/DocumentSearch";
import "../Chat/MChat.css";

function Demo({ token, theme }) {
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [sessions, setSessions] = useState([
    { session_id: 1, name: "Sample Chat", created_at: new Date().toISOString() },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [newChatName, setNewChatName] = useState("");
  const chatMessagesRef = useRef(null);
  const chatHistoryRef = useRef(null);

  const scrollToBottom = () => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleLoadPreviousChat = (sessionId) => {
    setCurrentSessionId(sessionId);
    setHistory([
      { role: "ai", content: "Welcome back to your chat!" },
      { role: "human", content: "Hello!" },
      { role: "ai", content: "How can I help you today?" },
      { role: "human", content: "I need help understanding Biden's policies on immigration." },
      { role: "ai", content: "Sure, I can retrieve information from the policy database, and provide you with the relevant details. Then, you can ask follow-up questions or dive deeper into the sources." },
    ]);
  };

  const handleChat = () => {
    if (!currentSessionId) {
      handleStartNewChat();
      return;
    }

    setHistory((prev) => [...prev, { role: "human", content: message }]);

    setTimeout(() => {
      setHistory((prev) => [
        ...prev,
        { role: "ai", content: `Register or log in to get AI respones to your policy question: "${message}"` },
      ]);
    }, 1000);

    setMessage("");
  };

  const handleStartNewChat = () => {
    setHistory([]);
    setCurrentSessionId(Date.now());
    setSessions((prev) => [
      { session_id: Date.now(), name: "New Chat", created_at: new Date().toISOString() },
      ...prev,
    ]);
    setMessage("");
  };

  const handleDeleteChat = (sessionId) => {
    setSessions(sessions.filter((session) => session.session_id !== sessionId));
    if (sessionId === currentSessionId) {
      setCurrentSessionId(null);
      setHistory([]);
    }
  };

  const handleRenameChat = (sessionId, newName) => {
    setSessions(
      sessions.map((session) =>
        session.session_id === sessionId ? { ...session, name: newName } : session
      )
    );
    setRenamingSessionId(null);
    setNewChatName("");
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        chatHistoryRef.current &&
        !chatHistoryRef.current.contains(event.target)
      ) {
        setShowChatHistory(false);
      }
    };

    if (showChatHistory) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showChatHistory]);

  return (
    <div className={`flex flex-col chat-tab overflow-hidden theme-${theme}`}>
      <div className="flex flex-1 min-h-0 w-full">
        <div className="flex-1 flex flex-col min-w-0">
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

          <div
            ref={chatMessagesRef}
            className="chat-messages flex-1 overflow-y-auto scroll-smooth"
          >
            {history.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === "human" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`message-bubble ${msg.role === "human" ? "human" : ""}`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          <div className="input-container">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleChat()}
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

        <div className="divider w-px" />

        <div
          className={`flex-1 min-w-0 search-section ${
            theme === "dark" ? "theme-dark" : "theme-light"
          }`}
        >
          <DocumentSearch token={token} theme={theme} />
        </div>
      </div>

      {showChatHistory && (
        <div className="modal-backdrop fixed inset-0 flex items-center justify-center p-4 z-50">
          <div ref={chatHistoryRef} className="modal-content">
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
    </div>
  );
}

export default Demo;
