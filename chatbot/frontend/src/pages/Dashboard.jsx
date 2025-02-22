import React, { useState, useEffect } from "react";
import "../css/output.css";

import { ArrowCircleUp } from "@phosphor-icons/react";
// component imports
import TopBar from "../components/TopBar";
import ChatsSideMenu from "../components/ChatsSideMenu";
import Message from "../components/Message";
import Suggestion from "../components/Suggestion";

function Dashboard() {
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
            setMessages((prev) => [
                ...prev,
                { text: data.response, isUser: false },
            ]);
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
        <div className="flex flex-col">
            <TopBar>
                <ChatsSideMenu
                    chats={[{ name: "Chat 1" }, { name: "Chat 2" }]}
                />
                <div className="md:max-w-3xl mx-auto px-4 md:px-0 flex flex-col flex-1 text-base">
                    {!isConnected && (
                        <div className="error-banner">
                            Warning: Backend not connected. Messages won't be
                            processed.
                        </div>
                    )}

                    {/* Header (only if messages) */}
                    {messages.length === 0 && (
                        <h1 className="text-2xl md:text-3xl font-bold m-2 mt-auto mx-auto mb-4">
                            What would you like to know?
                        </h1>
                    )}

                    {/* Suggestions (if no messages) */}
                    {messages.length === 0 ? (
                        <div className="flex justify-center mb-auto mx-auto whitespace-nowrap flex-wrap gap-2 md:gap-4 sm:max-w-md md:max-w-lg">
                            <Suggestion
                                text="Events at UF"
                                func={handleSuggestion(
                                    "What events are going on today at UF?"
                                )}
                            />
                            <Suggestion
                                text="Gainesville Weather"
                                func={handleSuggestion(
                                    "What is the weather like in Gainesville?"
                                )}
                            />
                            <Suggestion
                                text="Dining on campus"
                                func={handleSuggestion(
                                    "Tell me about dining options on campus."
                                )}
                            />
                            <Suggestion
                                text="Room maintenance"
                                func={handleSuggestion(
                                    "How do I request maintenance for my room?"
                                )}
                            />
                            <Suggestion
                                text="UF Health"
                                func={handleSuggestion(
                                    "How do I make an appointment at UF Health?"
                                )}
                            />
                            <Suggestion
                                text="UF Libraries"
                                func={handleSuggestion(
                                    "What are the library hours at UF?"
                                )}
                            />
                        </div>
                    ) : (
                        <div className="overflow-y-auto scroll flex flex-col-reverse h-full pb-2">
                            {messages
                                .slice(0)
                                .reverse()
                                .map((msg, idx) => (
                                    <Message
                                        key={idx}
                                        text={msg.text}
                                        isUser={msg.isUser}
                                    />
                                ))}
                        </div>
                    )}

                    {/* Generated Suggestions */}
                    {messages.length > 0 && (
                        <div className="flex flex-wrap gap-2"></div>
                    )}

                    <div className="fixed left-0 bottom-0 w-full p-4 pt-0">
                        {/* Message input */}
                        <form
                            onSubmit={handleSubmit}
                            className="flex justify-between gap-2 md:max-w-3xl mx-auto rounded-2xl p-4 bg-neutral-100"
                        >
                            <div
                                contentEditable="true"
                                suppressContentEditableWarning={true}
                                className="outline-none flex flex-1 items-center"
                                onInput={(e) => {
                                    setInput(e.currentTarget.textContent);
                                }}
                                onFocus={(e) =>
                                    e.currentTarget.textContent ===
                                        "Type your message..." &&
                                    (e.currentTarget.textContent = "")
                                }
                                onBlur={(e) =>
                                    e.currentTarget.textContent === "" &&
                                    (e.currentTarget.textContent =
                                        "Type your message...")
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
                </div>
            </TopBar>
        </div>
    );
}

export default Dashboard;
