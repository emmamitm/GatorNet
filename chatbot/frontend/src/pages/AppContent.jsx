import React, { useState, useEffect } from "react";
import "../css/output.css";

import { ArrowCircleUp } from "@phosphor-icons/react";
// component imports
import ChatsSideMenu from "../components/ChatsSideMenu";
import Message from "../components/Message";
import Suggestion from "../components/Suggestion";

function AppContent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);

  // Test backend connection on load
  useEffect(() => {
    fetch("http://localhost:5001/")
      .then((response) => {
        console.log("Backend connection test:", response.ok);
        setIsConnected(response.ok);
      })
      .catch((error) => {
        console.error("Backend connection test failed:", error);
        setIsConnected(false);
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!input.trim()) return;

    const userMessage = input.trim();
    console.log("Sending message:", userMessage); // Debug print

    // Add user message
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setInput("");
    document.querySelector('[contenteditable="true"]').textContent = "";

    // Get bot response
    try {
      console.log("Making request to backend..."); // Debug print
      const res = await fetch("http://localhost:5001/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      console.log("Response status:", res.status); // Debug print

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      console.log("Received response:", data); // Debug print
      setMessages((prev) => [...prev, { text: data.response, isUser: false }]);
    } catch (err) {
      console.error("Detailed error:", err);
      setMessages((prev) => [
        ...prev,
        {
          text: `Error: ${err.message}. Please try again.`,
          isUser: false,
        },
      ]);
    }
  };

  const handleSuggestion = (text) => () => {
    setInput(text);
    document.querySelector('[contenteditable="true"]').textContent = text;
  };

  return (
    <div className="max-w-3xl mx-auto p-4 pt-0 flex flex-col justify-center h-full text-base">
        {/* <ChatsSideMenu chats={[{ name: "Chat 1" }, { name: "Chat 2" }]} /> */}

      {!isConnected && (
        <div className="error-banner">
          Warning: Backend not connected. Messages won't be processed.
        </div>
      )}

      {/* Header */}
      <h1 className="text-3xl font-bold m-2">
        What would you like to know?
      </h1>

      {/* Suggestions (if no messages) */}
      {messages.length === 0 ? (
        <div className="flex flex-wrap gap-4">
          <Suggestion
            text="What events are going on today at UF?"
            func={handleSuggestion("What events are going on today at UF?")}
          />
          <Suggestion
            text="What is the weather like in Gainesville?"
            func={handleSuggestion("What is the weather like in Gainesville?")}
          />
          <Suggestion
            text="What is the latest news in the world?"
            func={handleSuggestion("What is the latest news in the world?")}
          />
          <Suggestion
            text="What events are going on today at UF?"
            func={handleSuggestion("What events are going on today at UF?")}
          />
        </div>
      ) : (
        <div className="flex flex-col flex-grow  border-2 rounded-2xl p-4 mb-4 border-neutral-200 bg-gradient-to-br from-neutral-50 to-neutral-100">
          <div className="overflow-y-auto scroll flex flex-col-reverse h-full">
            {messages
              .slice(0)
              .reverse()
              .map((msg, idx) => (
                <Message key={idx} text={msg.text} isUser={msg.isUser} />
              ))}
          </div>
        </div>
      )}

      {/* Generated Suggestions */}
      {messages.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Suggestion
            text="What events are going on today at UF?"
            func={handleSuggestion("What events are going on today at UF?")}
          />
          <Suggestion
            text="What is the weather like in Gainesville?"
            func={handleSuggestion("What is the weather like in Gainesville?")}
          />
          <Suggestion
            text="What is the latest news in the world?"
            func={handleSuggestion("What is the latest news in the world?")}
          />
          <Suggestion
            text="What events are going on today at UF?"
            func={handleSuggestion("What events are going on today at UF?")}
          />
        </div>
      )}

      <hr className="my-4 border border-neutral-300" />

      {/* Message input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-2 rounded-2xl p-4 border-neutral-300 bg-white"
      >
        <div
          contentEditable="true"
          suppressContentEditableWarning={true}
          className="flex-1 outline-none flex items-center"
          onInput={(e) => setInput(e.currentTarget.textContent)}
          onFocus={(e) =>
            e.currentTarget.textContent === "Type your message..." &&
            (e.currentTarget.textContent = "")
          }
          onBlur={(e) =>
            e.currentTarget.textContent === "" &&
            (e.currentTarget.textContent = "Type your message...")
          }
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        >
          Type your message...
        </div>
        <button type="submit">
          <ArrowCircleUp
            size={32}
            weight="fill"
            className="fill-neutral-700 hover:fill-neutral-500 active:fill-black outline-none cursor-pointer transition-colors duration-200"
          />
        </button>
      </form>
    </div>
  );
}

export default AppContent;
