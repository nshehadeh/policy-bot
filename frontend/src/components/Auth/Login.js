import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./auth.css";

const Login = ({ setToken, onClose, theme }) => {
  // State management for form inputs and error handling
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  let navigate = useNavigate();

  // Handle user login process
  const handleLogin = async () => {
    setError(""); // Clear any previous errors

    // Validate inputs
    if (!username) {
      setError("Username is required");
      return;
    }
    if (!password) {
      setError("Password is required");
      return;
    }

    try {
      // Submit login request and get authentication token
      const res = await axios.post("/api-token-auth/", {
        username,
        password,
      });
      setToken(res.data.token); // Store token in parent component
      onClose(); // Close the overlay
      navigate("/chat"); // Redirect to chat page on success
    } catch (error) {
      // Handle authentication errors
      if (error.response && error.response.status === 400) {
        setError("Invalid username or password");
      } else {
        setError("An error occurred. Please try again later.");
      }
    }
  };

  return (
    // Main login overlay container
    <div className={`auth-overlay ${theme}`}>
      <div className="auth-modal">
        <div className="auth-header">
          <h2>Login</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        <div className="auth-content">
          <h1 className="auth-title">PolicyAI</h1>
          <h2>Welcome Back</h2>
          {/* Error message display */}
          {error && <div className="error-message">{error}</div>}
          {/* Login form inputs */}
          <div className="auth-form">
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
            {/* Login submit button */}
            <button onClick={handleLogin} className="auth-button">
              Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
