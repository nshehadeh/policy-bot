import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Chat.css';

function Chat({ token }) {
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // Fetch chat sessions on component mount
  useEffect(() => { 
    const fetchChatSessions = async () => {
      try {
        const sessionsRes = await axios.get('/api/chat/sessions/', {
          headers: { Authorization: `Token ${token}` },
        });
        setSessions(sessionsRes.data);
      } catch (error) {
        console.error('Error fetching chat sessions:', error);
      }
    };
    fetchChatSessions();
  }, [token]);

  // Fetch chat history when a session is selected
  useEffect(() => {
    if (currentSessionId) {
      const fetchChatHistory = async () => {
        try {
          const res = await axios.post(
            '/api/chat/load/',
            { session_id: currentSessionId },
            {
              headers: { Authorization: `Token ${token}` },
            }
          );
          setHistory(res.data.chat_history);
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      };
      fetchChatHistory();
    }
  }, [currentSessionId, token]);

  const handleChat = async () => {
    try {
      const res = await axios.post(
        '/api/chat/',
        { message, session_id: currentSessionId },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setHistory([...history, { role: 'human', content: message }, { role: 'ai', content: res.data.response }]);
      setMessage(''); // Clear the input after sending
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleStartNewChat = async () => {
    try {
      const res = await axios.post(
        '/api/chat/',
        { message },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setCurrentSessionId(res.data.session_id);
      setHistory([{ role: 'human', content: message }, { role: 'ai', content: res.data.response }]);
      setMessage(''); // Clear the input after sending
    } catch (error) {
      console.error('Error starting new chat:', error);
    }
  };

  const handleNameChange = async () => {
    try {
      await axios.post(
        '/api/user_settings/',  // CHANGE: Adjusted the URL endpoint for user settings
        { first_name: firstName, last_name: lastName },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      alert('Name updated!');
      setShowSettings(false);
    } catch (error) {
      console.error('Error updating name:', error);
    }
  };

  const handleFetchUserData = async () => {  // CHANGE: Moved user data fetching logic here
    try {
      const userRes = await axios.get('/api/user_settings/', {  // CHANGE: Adjusted the URL endpoint for fetching user data
        headers: { Authorization: `Token ${token}` },
      });
      setFirstName(userRes.data.first_name);
      setLastName(userRes.data.last_name);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Chat</h2>
        <button onClick={() => { setShowSettings(!showSettings); if (!showSettings) handleFetchUserData(); }}>  {/* CHANGE: Added user data fetching on settings button click */}
          Settings
        </button>
      </div>
      
      {showSettings && (
        <div className="settings-panel">
          <input
            type="text"
            placeholder="First Name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Last Name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
          <button onClick={handleNameChange}>Update Name</button>
        </div>
      )}

      <div className="chat-content">
        <div className="chat-sidebar">
          <h3>Previous Chats</h3>
          <div className="sessions-list">
            {sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => setCurrentSessionId(session.session_id)}
                className={session.session_id === currentSessionId ? 'active' : ''}
              >
                {new Date(session.created_at).toLocaleString()}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-main">
          <div className="chat-history">
            {history.map((chat, index) => (
              <div key={index} className={`chat-message ${chat.role}`}>
                <p>{chat.content}</p>
              </div>
            ))}
          </div>

          <div className="chat-input">
            <input
              type="text"
              placeholder="Type your message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            {currentSessionId ? (
              <button onClick={handleChat}>Send</button>
            ) : (
              <button onClick={handleStartNewChat}>Start New Chat</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;
