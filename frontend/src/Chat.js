import React, { useState, useEffect } from 'react';
import api from './api';
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
        const sessionsRes = await api.get('/chat/sessions/', {
          headers: { Authorization: `Token ${token}` },
        });
        setSessions(sessionsRes.data);
      } catch (error) {
        console.error('Error fetching chat sessions:', error);
      }
    };
    fetchChatSessions();
  }, [token]);
  
  const handleLoadPreviousChat = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setHistory([]);  // Clear any existing history
  
    try {
      const res = await api.post(
        '/chat/load/',
        { session_id: sessionId },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      console.log("Loaded Chat History:", res.data.chat_history);  // Log the chat history to the console
   
      setHistory(res.data.chat_history || []);  // Ensure chat_history is an array
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };
  /*
  // Fetch chat history when a session is selected
  useEffect(() => {
    if (currentSessionId) {
      const fetchChatHistory = async () => {
        try {
          const res = await api.post(
            '/chat/load/',
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
*/
  const handleChat = async () => {
    try {
      const res = await api.post(
        '/chat/',
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

      let data = {}
      // Check if message is empty
      if(message.trim()) {
        data = {message};
      }
      const res = await api.post(
        '/chat/',
        data,
        {headers: { Authorization: `Token ${token}` },}
      );
      setHistory([]);
      if(data.message){
        setHistory([{ role: 'human', content: message }, { role: 'ai', content: res.data.response }]);
         // Clear the input after sending
        setMessage('');
      }
      setCurrentSessionId(res.data.session_id);
      const sessionsRes = await api.get('/chat/sessions/', {  // Reload chat sessions
        headers: { Authorization: `Token ${token}` },
      });
      setSessions(sessionsRes.data);  // Update the list of sessions
    } catch (error) {
      console.error('Error starting new chat:', error);
    }
  };

  const handleNameChange = async () => {
    try {
      await api.post(
        '/user_settings/',  
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

  const handleFetchUserData = async () => {  
    try {
      const userRes = await api.get('/user_settings/', {  
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
        {currentSessionId && (
          <button onClick={handleStartNewChat} style={{ position: 'absolute', right: '10px', top: '10px' }}>
            Start New Chat
          </button>)}
        <button onClick={() => { setShowSettings(!showSettings); if (!showSettings) handleFetchUserData(); }}>
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
                onClick={() => handleLoadPreviousChat(session.session_id)}  // Load chat history when a previous chat is selected
                className={session.session_id === currentSessionId ? 'active' : ''}
              >
                {new Date(session.created_at).toLocaleString()}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-main">
          <div className="chat-history">
            {Array.isArray(history) && history.map((chat, index) => (
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
              <button onClick={handleChat}>Send</button>)
              : (
              <button onClick={handleStartNewChat}>Start New Chat</button>)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;