import React from 'react';
import './Home.css';

function Home() {
  return (
    <div className="home">
      <div className="home-content">
        <h1>Welcome to PolicyAI</h1>
        <p>Your AI-powered assistant for policy research</p>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Chat Interface</h3>
            <p>Interact with our AI to get instant answers about policies direct from federal sources</p>
          </div>
          <div className="feature-card">
            <h3>Smart Search</h3>
            <p>Find relevant policy information quickly and efficiently based on your semantic search queries</p>
          </div>
          <div className="feature-card">
            <h3>Customizable</h3>
            <p>Adjust settings to match your preferences and get tailored policy reports</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
