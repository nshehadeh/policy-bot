// App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './Login';
import Chat from './Chat';
import './App.css';

function App() {
  const [token, setToken] = useState('');
  console.log('App rendered');

  return (
    <Router>
      <div className="App">
        <h1>Chat with Bot</h1>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Login setToken={setToken} />} />
          <Route path="/chat" element={<Chat token={token} />} />
        </Rou