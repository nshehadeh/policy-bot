import React, { useState, useEffect, useRef } from 'react';
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
  const websocket = useRef(null);
  const aiMessageRef = useRef('');


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

  // Connect to websock if session is established
  // Connect to WebSocket when a session is loaded
  useEffect(() => {
    if (currentSessionId) {
      console.log(`Trying to open WebSocket connection to: ws://localhost:8000/ws/chat/${currentSessionId}/`);

      // Close any existing connection

      if (websocket.current) {
        console.log('Closing existing WebSocket connection');
        websocket.current.close();
      }

      // Open new WebSocket connection
      console.log(`Opening WebSocket connection for session: ${currentSessionId}`);
      websocket.current = new WebSocket(`ws://localhost:8000/ws/chat/${currentSessionId}/?token=${token}`);

      websocket.current.onopen = () => {
        console.log('WebSocket connection opened.');
      };

      websocket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        aiMessageRef.current += ` ${data.chunk}`;

        setHistory(prev => {
          const newHistory = [...prev];
          if (newHistory.length && newHistory[newHistory.length - 1]?.role === 'ai') {
            newHistory[newHistory.length - 1].content = aiMessageRef.current.trim();
          } else {
            newHistory.push({ role: 'ai', content: data.chunk });
          }
          // console.log('Updated history:', newHistory);
          return newHistory;
        });
      
      };

      websocket.current.onclose = () => {
        console.log('WebSocket connection closed.');
      };

      websocket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      // Cleanup WebSocket on component unmount or session change
      return () => {
        websocket.current.close();
      };
    }
  }, [currentSessionId]);
  
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
  
  const handleChat = () => {
    // push human message
    setHistory((prev) => [...prev, { role: 'human', content: message}]);
    // send on websocket
    if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
      websocket.current.send(JSON.stringify({
        message: message
      }));
      setMessage(''); // Clear the input
    }
  };

  const handleStartNewChat = async () => {
    try {
      let data = {}
      // Check if message is empty
      if(message.trim()) {
        data = {message};
      }
      console.log("Token being used:", token);

      const res = await api.post('/chat/new/', data, {
        headers: { Authorization: `Token ${token}` },
      });

      setHistory([]);
      setCurrentSessionId(res.data.session_id);
      // If starting chat with new message --> send in WS
      if(data.message){
        setHistory([{ role: 'human', content: message }]);
         if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
          websocket.current.send(JSON.stringify({
            message: data.message
          }));
        }
        setMessage('');
      }
      // Reload sessions
      const sessionsRes = await api.get('/chat/sessions/', {  // Reload chat sessions
        headers: { Authorization: `Token ${token}` },
      });
      setSessions(sessionsRes.data);
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
    {currentSessionId && (
      <button onClick={handleStartNewChat} className="button-standard">
        Start New Chat
      </button>
    )}
    <button onClick={() => { setShowSettings(!showSettings); if (!showSettings) handleFetchUserData(); }} className="button-standard">
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
      <button onClick={handleNameChange} className="button-standard">Update Name</button>
    </div>
  )}

  <div className="chat-content">
    <div className="chat-sidebar">
     
      <h3>Previous Chats</h3>
      <div className="sessions-list">
        {sessions.map((session) => (
          <button
            key={session.session_id}
            onClick={() => handleLoadPreviousChat(session.session_id)}
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
          <button onClick={handleChat} className="button-standard">Send</button>
        ) : (
          <button onClick={handleStartNewChat} className="button-standard">Start New Chat</button>
        )}
      </div>
    </div>
  </div>
</div>



  );
}

export default Chat;