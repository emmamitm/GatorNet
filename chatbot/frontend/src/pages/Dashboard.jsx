import React, { useState, useEffect } from "react";
// component imports
import TopBar from "../components/TopBar";
import ChatsSideMenu from "../components/ChatsSideMenu";
import SuggestionMenu from "../components/SuggestionMenu";
import ChatInterface from "../components/Chat";
// auth
import { useAuth } from "../auth/AuthContext";

function Dashboard() {
    // Messages
    const [messages, setMessages] = useState([]);

    // Decision Tree
    const [activeMenu, setActiveMenu] = useState(null);

    // Auth
    const [isConnected, setIsConnected] = useState(false);
    const [currentConversationId, setCurrentConversationId] = useState(null);
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

    const handleSubmit = async (userMessage) => {
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

    // Handle suggestion click
    const handleMenuSelect = (selection) => {
        setActiveMenu(selection);
    };

    // Handle exiting from menu to chat
    const handleExitMenu = () => {
        setActiveMenu(null);
    };

    // render chat or menu
    const renderMainContent = () => {
        if (activeMenu) {
            return (
                // Menu
                <div className="flex flex-col flex-1 justify-center">
                    <SuggestionMenu
                        category={activeMenu}
                        onBack={handleExitMenu}
                    />
                </div>
            );
        }
        return (
            // Chat interface
            <ChatInterface
                messages={messages}
                onSendMessage={handleSubmit}
                onMenuSelect={handleMenuSelect}
                isConnected={isConnected}
            />
        );
    };

    return (
        <div className="flex flex-col w-screen h-screen">
            <TopBar />
            <ChatsSideMenu
                onSelectConversation={handleSelectConversation}
                currentConversationId={currentConversationId}
            />
            <div className="md:w-3xl px-4 md:pl-8 mx-auto flex flex-col flex-1 text-base">
                {/* Main content (messages or menu) */}
                {renderMainContent()}
            </div>
        </div>
    );
}

export default Dashboard;
