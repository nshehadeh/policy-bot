import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = async () => {
    try {
      const res = await axios.post('/api-token-auth/', {
        username,
        password,
      });
      setToken(res.data.token);
      setIsLoggedIn(true);
      console.log('Token:', res.data.token);
    } catch (error) {
      console.error('Error logging in:', error);
    }
  };

  const handleChat = async () => {
    try {
      const res = await axios.post(
        '/api/chat/',
        { message },
        {
          headers: {
            Authorization: `Token ${token}`,
          },
        }
      );
      setResponse(res.data.response);
      console.log('Response:', res.data.response);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div className="App">
      <h1>Chat with Bot</h1>
      <div>
        <h2>Login</h2>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleLogin}>Login</button>
      </div>
      {isLoggedIn && (
        <div>
          <h2>Chat</h2>
          <input
            type="text"
            placeholder="Type your message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <button onClick={handleChat}>Send</button>
          <p>Response: {response}</p>
        </div>
      )}
    </div>
  );
}

export default App;
