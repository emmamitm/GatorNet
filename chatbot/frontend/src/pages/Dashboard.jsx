import React, { useState, useEffect } from "react";
import "../css/output.css";
import { ArrowCircleUp } from "@phosphor-icons/react";
// component imports
import TopBar from "../components/TopBar";
import ChatsSideMenu from "../components/ChatsSideMenu";
import Message from "../components/Message";
import Suggestion from "../components/Suggestion";
import { useAuth } from "../auth/AuthContext";

function Dashboard() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isConnected, setIsConnected] = useState(false);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [isFetchingMessages, setIsFetchingMessages] = useState(false);
    const { user } = useAuth();

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

    // Load messages when conversation changes
    useEffect(() => {
        if (currentConversationId) {
            loadConversationMessages(currentConversationId);
        } else {
            // Clear messages if no conversation is selected
            setMessages([]);
        }
    }, [currentConversationId]);

    // Function to load messages for a conversation
    const loadConversationMessages = async (conversationId) => {
        if (!conversationId) return;
        
        setIsFetchingMessages(true);
        
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`http://localhost:5001/api/conversations/${conversationId}/messages`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load messages: ${response.status}`);
            }
            
            const messagesData = await response.json();
            setMessages(messagesData);
        } catch (error) {
            console.error("Error loading conversation messages:", error);
        } finally {
            setIsFetchingMessages(false);
        }
    };

    // Handle conversation selection from sidebar
    const handleSelectConversation = (conversationId) => {
        setCurrentConversationId(conversationId);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        
        const userMessage = input.trim();
        console.log("Sending message:", userMessage); // Debug print
        
        // Clear input field first
        setInput("");
        document.querySelector('[contenteditable="true"]').textContent = "";
        
        // Get user ID from authentication
        const userId = user ? user.user_id : localStorage.getItem("userId");
        
        // If no conversation is selected, we need to create one
        if (!currentConversationId) {
            try {
                const token = localStorage.getItem("token");
                const response = await fetch("http://localhost:5001/api/conversations", {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to create conversation: ${response.status}`);
                }
                
                const newConversation = await response.json();
                setCurrentConversationId(newConversation.id);
                
                // Continue with the message sending...
            } catch (error) {
                console.error("Error creating conversation:", error);
                return;
            }
        }
        
        // Add user message to UI immediately (optimistic update)
        const tempUserMessage = { 
            id: 'temp-' + Date.now(),
            text: userMessage, 
            isUser: true,
            sent_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempUserMessage]);
        
        // Get bot response
        try {
            console.log("Making request to backend..."); // Debug print
            console.log("Using conversation ID:", currentConversationId);
            
            const res = await fetch("http://localhost:5001/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify({ 
                    message: userMessage,
                    user_id: parseInt(userId),
                    conversation_id: currentConversationId
                }),
            });
            
            console.log("Response status:", res.status); // Debug print
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            console.log("Received response:", data); // Debug print
            
            // Update the conversation ID from the response if provided
            if (data.conversation_id) {
                setCurrentConversationId(data.conversation_id);
                console.log("Updated conversation ID:", data.conversation_id);
            }
            
            // After getting response, reload the full conversation to ensure we have all messages
            await loadConversationMessages(data.conversation_id || currentConversationId);
            
        } catch (err) {
            console.error("Detailed error:", err);
            
            // Show error in message list
            setMessages(prev => [
                ...prev,
                {
                    id: 'error-' + Date.now(),
                    text: `Error: ${err.message}. Please try again.`,
                    isUser: false,
                    sent_at: new Date().toISOString()
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
                    onSelectConversation={handleSelectConversation}
                    currentConversationId={currentConversationId}
                />
                <div className="md:max-w-3xl mx-auto px-4 md:px-0 flex flex-col flex-1 text-base">
                    {!isConnected && (
                        <div className="error-banner">
                            Warning: Backend not connected. Messages won't be
                            processed.
                        </div>
                    )}
                    
                    {isFetchingMessages && (
                        <div className="text-center py-4">Loading messages...</div>
                    )}
                    
                    {/* Header (only if messages) */}
                    {messages.length === 0 && !isFetchingMessages && (
                        <h1 className="text-2xl md:text-3xl font-bold m-2 mt-auto mx-auto mb-4">
                            What would you like to know?
                        </h1>
                    )}
                    
                    {/* Suggestions (if no messages) */}
                    {messages.length === 0 && !isFetchingMessages ? (
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
                            {!isFetchingMessages && messages
                                .slice(0)
                                .reverse()
                                .map((msg, idx) => (
                                    <Message
                                        key={msg.id || idx}
                                        text={msg.text}
                                        isUser={msg.isUser}
                                    />
                                ))}
                        </div>
                    )}
                    
                    {/* Message input */}
                    <div className="fixed left-0 bottom-0 w-full p-4 pt-0">
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