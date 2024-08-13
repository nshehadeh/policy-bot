import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Chat({ token }) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [history, setHistory] = useState([]);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  
  useEffect(() => {
    // Fetch chat history and user name on load
    const fetchUserData = async () => {
      try {
        const res = await axios.get('/api/user/history/', {
          headers: { Authorization: `Token ${token}` },
        });
        setHistory(res.data.chat_history);
        setFirstName(res.data.first_name);
        setLastName(res.data.last_name);
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    };
    fetchUserData();
  }, [token]);

  const handleChat = async () => {
    try {
      const res = await axios.post(
        '/api/chat/',
        { message },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setResponse(res.data.response);
      setHistory([...history, { message, response: res.data.response }]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleNameChange = async () => {
    try {
      await axios.post(
        '/api/user/update-settings/',
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

  // Renders chat dates
  const chatDates = [...new Set(history.map(chat => new Date(chat.timestamp).toLocaleDateString()))];

  return (
    <div>
      <h2>Chat</h2>
      <div style={{ float: 'right' }}>
        <button onClick={() => setShowSettings(!showSettings)}>
          Settings
        </button>
      </div>
      {showSettings && (
        <div>
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
      <div style={{ display: 'flex' }}>
        <div style={{ width: '20%', borderRight: '1px solid #ccc', paddingRight: '10px' }}>
          <h3>Chat Dates</h3>
          {chatDates.map((date, index) => (
            <p key={index}>{date}</p>
          ))}
        </div>
        <div style={{ width: '80%', paddingLeft: '10px' }}>
          <input
            type="text"
            placeholder="Type your message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <button onClick={handleChat}>Send</button>
          <p>Response: {response}</p>
        </div>
      </div>
    </div>
  );
}

export default Chat;