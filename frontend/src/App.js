// App.js
import React, { useState } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Login from "./components/Auth/Login";
import Chat from "./components/Chat/Chat";
import Register from "./components/Auth/Register";
import "./App.css";

function App() {
  const [token, setToken] = useState("");
  console.log("App rendered");

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login setToken={setToken} />} />
          <Route path="/chat" element={<Chat token={token} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
