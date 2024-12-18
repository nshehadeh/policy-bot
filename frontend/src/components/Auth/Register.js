// Register.js
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import './auth.css'; 

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState('');
  let navigate = useNavigate();

  const handleRegister = async () => {
    setError(''); // Clear any previous errors

    // Validate username
    if (!username) {
      setError('Username is required');
      return;
    }
    if (username.length < 3) {
      setError('Username must be at least 3 characters long');
      return;
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setError('Username can only contain letters, numbers, and underscores');
      return;
    }

    // Validate password
    if (!password) {
      setError('Password is required');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    // Check password match
    if (password !== password2) {
      setError('Passwords do not match');
      return;
    }

    try {
      await axios.post('/api/users/', {
        username,
        password,
      });
      navigate('/login');
    } catch (error) {
      if (error.response && error.response.data) {
        // Handle specific error messages from the backend
        if (error.response.data.username) {
          setError(`Username error: ${error.response.data.username[0]}`);
        } else if (error.response.data.password) {
          setError(`Password error: ${error.response.data.password[0]}`);
        } else {
          setError('Registration failed. Please try again.');
        }
      } else {
        setError('An error occurred. Please try again later.');
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h1 className="auth-title">PolicyAI</h1>
        <h2>Create Account</h2>
        {error && <div className="error-message">{error}</div>}
        <div className="input-group">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="auth-input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            className="auth-input"
          />
        </div>
        <button onClick={handleRegister} className="auth-button">Register</button>
        <p className="auth-link">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
