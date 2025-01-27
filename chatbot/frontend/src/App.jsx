import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  // Test backend connection on load
  useEffect(() => {
    fetch('http://localhost:5001/')
      .then(response => {
        console.log("Backend connection test:", response.ok);
        setIsConnected(response.ok);
      })
      .catch(error => {
        console.error("Backend connection test failed:", error);
        setIsConnected(false);
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    console.log("Sending message:", userMessage);  // Debug print

    // Add user message
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
    setInput('');

    // Get bot response
    try {
      console.log("Making request to backend...");  // Debug print
      const res = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
      });
      
      console.log("Response status:", res.status);  // Debug print
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      console.log("Received response:", data);  // Debug print
      setMessages(prev => [...prev, { text: data.response, isUser: false }]);
    } catch (err) {
      console.error("Detailed error:", err);
      setMessages(prev => [...prev, { 
        text: `Error: ${err.message}. Please try again.`, 
        isUser: false 
      }]);
    }
  };

  return (
    <div className="app">
      {!isConnected && (
        <div className="error-banner">
          Warning: Backend not connected. Messages won't be processed.
        </div>
      )}
      <div className="chat-box">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.isUser ? 'message user' : 'message bot'}>
            {msg.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          autoFocus
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default App;