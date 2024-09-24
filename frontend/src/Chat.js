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
  const [isLoading, setIsLoading] = useState(false);

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
  
  // using fetch instead of axios because of streaming issues, can look into this later
  const handleChat = async () => {
    setIsLoading(true);
    try {
      console.log("Sending request...");
  
      // Switch to the Fetch API to handle streams
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: currentSessionId,
        })
      });
  
      console.log("Response received, starting to read stream...");      
      const reader = response.body.getReader();
      let LLMresponse = '';
      while(true){

        const {done,value} = await reader.read();
        if(done){
          console.log("Stream finished");
          break;
        }

        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n\n');

        for(const line of lines) {
          if (line.startsWith('data: ')) {
            // remove data: prefix from the data
            const data = JSON.parse(line.slice(6));
    
            switch(data.type) {
              case 'initial':
                console.log("Initial package recieved");
                setCurrentSessionId(data.session_id);
                break;
              case 'chunk':
                console.log("Chunk recieved", data.chunk);
                setHistory(prev => {
                  const newHistory = [...prev];
                  LLMresponse += data.chunk
                  if (newHistory.length && newHistory[newHistory.length - 1]?.role === 'ai') {
                    newHistory[newHistory.length - 1].content = LLMresponse;
                  } else {
                    newHistory.push({ role: 'ai', content: LLMresponse });
                  }
                  console.log(newHistory)
                  return newHistory;
                });
                break;
              case 'final':
                console.log("Final chunk recieved")
                setHistory(prev => {
                  const newHistory = [...prev];
                  if (newHistory[newHistory.length - 1]?.role === 'ai') {
                    newHistory[newHistory.length - 1].content = data.response;
                  } else {
                    newHistory.push({ role: 'ai', content: data.response });
                  }
                  return newHistory;
                });
                setIsLoading(false);
                break;
            }
          }
        }          
      }
      setMessage(''); // Clear the input after sending
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
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