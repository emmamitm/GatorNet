import React, { useState, useEffect, useRef } from "react";
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
    const isAnyMessageLoading = messages.some((msg) => msg.isLoading);
    const [input, setInput] = useState("");
    const [isConnected, setIsConnected] = useState(false);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [isPlaceholder, setIsPlaceholder] = useState(true);
    const inputRef = useRef(null);
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
        }
        // Don't clear messages when conversation ID is null to prevent
        // message flickering when creating a new conversation
    }, [currentConversationId]);

    // Function to load messages for a conversation
    const loadConversationMessages = async (conversationId) => {
        if (!conversationId) return;

        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `http://localhost:5001/api/conversations/${conversationId}/messages`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(`Failed to load messages: ${response.status}`);
            }

            const messagesData = await response.json();
            setMessages(messagesData);
        } catch (error) {
            console.error("Error loading conversation messages:", error);
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
        console.log("Sending message:", userMessage);

        // Clear input field first
        setInput("");
        if (inputRef.current) {
            inputRef.current.textContent = "";
            setIsPlaceholder(true);
        }

        // Get user ID from authentication
        const userId = user ? user.user_id : localStorage.getItem("userId");

        // Track conversation ID for this request
        let conversationIdForRequest = currentConversationId;

        // If no conversation is selected, create one before continuing
        if (!conversationIdForRequest) {
            try {
                const token = localStorage.getItem("token");
                const response = await fetch(
                    "http://localhost:5001/api/conversations",
                    {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${token}`,
                            "Content-Type": "application/json",
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `Failed to create conversation: ${response.status}`
                    );
                }

                const newConversation = await response.json();
                console.log("Created new conversation:", newConversation);

                // Store the new conversation ID in our local variable
                conversationIdForRequest = newConversation.id;

                // Also update the state (will be used in future requests)
                // Update the state, but don't trigger a re-render/clear yet
                // We'll let the messages update first to avoid flicker
                // setCurrentConversationId will happen after we've shown messages

                if (!conversationIdForRequest) {
                }
            } catch (error) {
                console.error("Error creating conversation:", error);
                // Show error in message list
                setMessages((prev) => [
                    ...prev,
                    {
                        id: "error-" + Date.now(),
                        text: `Error: ${error.message}. Please try again.`,
                        isUser: false,
                        sent_at: new Date().toISOString(),
                    },
                ]);
                return; // Stop execution if we couldn't create a conversation
            }
        }

        // Add user message to UI immediately (optimistic update)
        const newMessage = {
            id: "user-" + Date.now(),
            text: userMessage,
            isUser: true,
            sent_at: new Date().toISOString(),
        };

        // Add both the user message and a loading indicator for the AI
        setMessages((prev) => [
            ...prev,
            newMessage,
            {
                id: "loading-" + Date.now(),
                text: "",
                isUser: false,
                isLoading: true,
                sent_at: new Date().toISOString(),
            },
        ]);

        // Get bot response
        try {
            console.log("Making request to backend...");
            console.log("Using conversation ID:", conversationIdForRequest);

            const res = await fetch("http://localhost:5001/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    message: userMessage,
                    user_id: parseInt(userId),
                    conversation_id: conversationIdForRequest,
                }),
            });

            console.log("Response status:", res.status);

            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }

            const data = await res.json();
            console.log("Received response:", data);

            // Update the conversation ID from the response if provided
            if (data.conversation_id) {
                // Now that we have the AI response, it's safe to update the conversation ID
                setCurrentConversationId(data.conversation_id);
                console.log("Updated conversation ID:", data.conversation_id);
            } else if (conversationIdForRequest && !currentConversationId) {
                // Set the conversation ID we created earlier
                setCurrentConversationId(conversationIdForRequest);
            }

            // Remove the loading indicator and add the AI response
            const aiMessage = {
                id: data.id || "ai-" + Date.now(),
                text: data.message || data.response,
                isUser: false,
                sent_at: data.sent_at || new Date().toISOString(),
            };

            setMessages((prev) =>
                prev
                    // Filter out the loading indicator
                    .filter((msg) => !msg.isLoading)
                    // Add the new AI message
                    .concat(aiMessage)
            );

            // You can still load the full conversation history in the background if needed
            // This ensures your UI stays responsive while data syncs
            loadConversationMessages(
                data.conversation_id || conversationIdForRequest
            ).catch((err) =>
                console.error("Error updating conversation:", err)
            );
        } catch (err) {
            console.error("Detailed error:", err);

            // Remove loading indicator and show error message
            setMessages((prev) =>
                prev
                    // Filter out the loading indicator
                    .filter((msg) => !msg.isLoading)
                    // Add the error message
                    .concat({
                        id: "error-" + Date.now(),
                        text: `Error: ${err.message}. Please try again.`,
                        isUser: false,
                        sent_at: new Date().toISOString(),
                    })
            );
        }
    };

    const handleSuggestion = (text) => () => {
        setInput(text);
        if (inputRef.current) {
            inputRef.current.textContent = text;
            setIsPlaceholder(false);
        }
    };

    const handleInputFocus = () => {
        if (isPlaceholder && inputRef.current) {
            inputRef.current.textContent = "";
            setIsPlaceholder(false);
        }
    };

    const handleInputBlur = () => {
        if (inputRef.current && inputRef.current.textContent.trim() === "") {
            inputRef.current.textContent = "Type your message...";
            setIsPlaceholder(true);
        }
    };

    const handleInputChange = (e) => {
        const content = e.currentTarget.textContent || "";
        setInput(content);
        setIsPlaceholder(content.trim() === "");
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
                                        key={msg.id || idx}
                                        text={msg.text}
                                        isUser={msg.isUser}
                                        isLoading={msg.isLoading}
                                    />
                                ))}
                        </div>
                    )}

                    {/* Message input */}
                    <div className="fixed left-0 bottom-0 w-full p-4 pt-0">
                        <form
                            onSubmit={handleSubmit}
                            className="flex justify-between gap-2 md:max-w-3xl mx-auto rounded-2xl p-4 bg-neutral-100 dark:bg-neutral-800"
                        >
                            <div
                                ref={inputRef}
                                contentEditable="true"
                                suppressContentEditableWarning={true}
                                className={`outline-none flex flex-1 items-center ${
                                    isPlaceholder
                                        ? "text-neutral-500 dark:text-neutral-400"
                                        : ""
                                }`}
                                onInput={handleInputChange}
                                onFocus={handleInputFocus}
                                onBlur={handleInputBlur}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        e.preventDefault();
                                        handleSubmit(e);
                                    }
                                }}
                            >
                                Type your message...
                            </div>
                            <button
                                type="submit"
                                disabled={isAnyMessageLoading}
                            >
                                <ArrowCircleUp
                                    size={32}
                                    weight="fill"
                                    className="fill-neutral-700 hover:fill-neutral-500 active:fill-black dark:fill-neutral-300 dark:hover:fill-neutral-400 dark:active:fill-neutral-100 outline-none transition-colors"
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
