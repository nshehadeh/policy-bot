import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar({ theme, toggleTheme, isLoggedIn, onLoginClick, onSettingsClick }) {
  const location = useLocation();

  return (
    <nav className={`navbar ${theme}`}>
      <div className="nav-content">
        <div className="nav-brand">
          <h1>PolicyAI</h1>
          <div className="nav-links">
            <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
              About
            </Link>
            <Link 
              to={isLoggedIn ? "/chat" : "/demo"} 
              className={`nav-link ${location.pathname === (isLoggedIn ? '/chat' : '/demo') ? 'active' : ''}`}
            >
              {isLoggedIn ? 'Chat' : 'Demo'}
            </Link>
          </div>
        </div>
        <div className="nav-actions">
          <button 
            onClick={isLoggedIn ? onSettingsClick : onLoginClick} 
            className="nav-button"
          >
            {isLoggedIn ? 'Settings' : 'Login'}
          </button>
          <button onClick={toggleTheme} className="nav-button">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
