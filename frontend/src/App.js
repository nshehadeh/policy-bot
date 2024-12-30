// App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Chat from './components/Chat/Chat';
import Demo from './components/Demo/Demo';
import Home from './components/Home/Home';
import Navbar from './components/Navbar/Navbar';
import Login from './components/Auth/Login';
import Settings from './components/Settings/Settings';
import './App.css';

// Navigation handler component
function NavigationHandler({ token }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (token && window.location.pathname === '/demo') {
      navigate('/chat');
    } else if (!token && window.location.pathname === '/chat') {
      navigate('/demo');
    }
  }, [token, navigate]);

  return null;
}

function App() {
  const [theme, setTheme] = useState('dark');
  const [token, setToken] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const handleLoginClick = () => {
    setShowLogin(true);
  };

  const handleSettingsClick = () => {
    setShowSettings(true);
  };

  return (
    <Router>
      <div className={`app ${theme}`}>
        <Navbar 
          theme={theme} 
          toggleTheme={toggleTheme}
          isLoggedIn={!!token}
          onLoginClick={handleLoginClick}
          onSettingsClick={handleSettingsClick}
        />
        <NavigationHandler token={token} />
        <Routes>
          <Route path="/" element={<Home theme={theme} />} />
          <Route path="/chat" element={<Chat token={token} theme={theme} />} />
          <Route path="/demo" element={<Demo theme={theme} />} />
        </Routes>

        {showLogin && !token && (
          <Login 
            setToken={setToken} 
            onClose={() => setShowLogin(false)}
            theme={theme}
          />
        )}

        {showSettings && token && (
          <Settings 
            onClose={() => setShowSettings(false)}
            theme={theme}
          />
        )}
      </div>
    </Router>
  );
}

export default App;
