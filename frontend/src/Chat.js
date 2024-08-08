// Chat.js
import React, { useState } from 'react';
import axios from 'axios';

function Chat({ token }) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

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
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
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
  );
}

export default Chat;
