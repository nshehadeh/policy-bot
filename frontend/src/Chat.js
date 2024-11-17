import React, { useState, useEffect, useRef } from 'react';
import ChatSessionItem from './ChatSessionItem';
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
  const [loading, setLoading] = useState(false);  // New loading state



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
        if (data.status == 'complete') return;
        aiMessageRef.current += ` ${data.chunk}`;
        console.log(data.chunk)

        setHistory(prev => {
          const newHistory = [...prev];
          if (newHistory.length && newHistory[newHistory.length - 1]?.role === 'ai') {
            newHistory[newHistory.length - 1].content = aiMessageRef.current;
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
    aiMessageRef.current = ''
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
  const handleDeleteChat = async (sessionId) => {
    try {
      await api.delete(`/chat/sessions/${sessionId}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setSessions(sessions.filter(session => session.session_id !== sessionId));
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setHistory([]);
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };
  
  const handleRenameChat = async (sessionId, newName) => {
    try {
      await api.patch(`/chat/sessions/${sessionId}/`, 
        { name: newName },
        { headers: { Authorization: `Token ${token}` },
      });
      setSessions(sessions.map(session => 
        session.session_id === sessionId 
          ? { ...session, name: newName }
          : session
      ));
    } catch (error) {
      console.error('Error renaming chat:', error);
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
          <ChatSessionItem
            key={session.session_id}
            session={session}
            isActive={session.session_id === currentSessionId}
            onSelect={handleLoadPreviousChat}
            onDelete={handleDeleteChat}
            onRename={handleRenameChat}
          />
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