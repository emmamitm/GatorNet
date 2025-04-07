import { React, useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    MinusCircle,
    ChatsCircle,
    Chats,
    PushPin,
    PushPinSlash,
    Plus,
    MagnifyingGlass,
    X,
} from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";

function ChatsSideMenu({ onSelectConversation, currentConversationId }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const [conversations, setConversations] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const { user } = useAuth();

    const [screenSize, setScreenSize] = useState({
        width: window.innerWidth,
        height: window.innerHeight,
    });

    // Fetch user conversations
    const fetchConversations = async () => {
        if (!user) return;

        setIsLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                "http://localhost:5001/api/conversations",
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to fetch conversations: ${response.status}`
                );
            }

            const data = await response.json();
            setConversations(data);
        } catch (err) {
            console.error("Error fetching conversations:", err);
            setError("Failed to load conversations");
        } finally {
            setIsLoading(false);
        }
    };

    // Create a new conversation
    const createNewConversation = async () => {
        if (!user) return;

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

            // Add to conversation list
            setConversations((prev) => [newConversation, ...prev]);

            // Select the new conversation
            if (onSelectConversation) {
                onSelectConversation(newConversation.id);
            }
        } catch (err) {
            console.error("Error creating conversation:", err);
            setError("Failed to create new conversation");
        }
    };

    // Delete a conversation
    const deleteConversation = async (conversationId, e) => {
        e.stopPropagation(); // Prevent selecting the conversation when deleting

        if (!user) return;

        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `http://localhost:5001/api/conversations/${conversationId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to delete conversation: ${response.status}`
                );
            }

            // Remove from conversation list
            setConversations((prev) =>
                prev.filter((conv) => conv.id !== conversationId)
            );

            // If the deleted conversation was the current one, select a new one or clear
            if (currentConversationId === conversationId) {
                // Select the first available conversation or null if none left
                const nextConversation = conversations.find(
                    (conv) => conv.id !== conversationId
                );
                if (onSelectConversation) {
                    onSelectConversation(
                        nextConversation ? nextConversation.id : null
                    );
                }
            }
        } catch (err) {
            console.error("Error deleting conversation:", err);
            setError("Failed to delete conversation");
        }
    };

    // Load conversations on component mount, when user changes, or when expanded
    useEffect(() => {
        if (user) {
            fetchConversations();
        }
    }, [user, isExpanded]);

    useEffect(() => {
        const handleResize = () => {
            setScreenSize({
                width: window.innerWidth,
                height: window.innerHeight,
            });
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const iconSize = 20;

    return (
        <div>
            {screenSize.width < 768 && (
                <div className="fixed md:hidden left-8 top-[26px] z-20">
                    <button
                        className="p-2 rounded-full bg-neutral-100 hover:bg-neutral-100/75 transition-colors"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        <Chats size={iconSize} />
                    </button>
                </div>
            )}
            {isExpanded && (
                <motion.div
                    className="md:hidden fixed inset-0 bg-neutral-100/50 dark:bg-neutral-900/50 z-10"
                    onClick={() => {
                        setIsExpanded(false);
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                ></motion.div>
            )}
            <motion.div className="max-h-fit md:max-h-full z-20 relative">
                <motion.div
                    className="fixed top-0 left-0 md:p-1 h-full backdrop-blur-2xl bg-neutral-200/60 dark:bg-neutral-700/60 border-r-2 border-neutral-200 dark:border-neutral-700 rounded-r-xl overflow-y-scroll"
                    {...(screenSize.width >= 768 && {
                        onMouseOver: () => {
                            if (!isPinned) setIsExpanded(true);
                        },
                        onMouseLeave: () => {
                            if (!isPinned) setIsExpanded(false);
                        },
                    })}
                    animate={{
                        width: isExpanded
                            ? 250
                            : screenSize.width < 768
                            ? 0
                            : 30,
                    }}
                    transition={{ duration: 0.2 }}
                >
                    {isExpanded ? (
                        <motion.div
                            className="flex flex-col p-3 md:p-0"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                        >
                            <div className="flex justify-between px-2 pt-1">
                                {/* <h1 className="text-2xl font-bold">Chats</h1> */}
                                {isPinned ? (
                                    <PushPinSlash
                                        onClick={() => setIsPinned(false)}
                                        weight="fill"
                                        className="cursor-pointer fill-neutral-800 dark:fill-neutral-200 transition-colors"
                                        size={iconSize}
                                    />
                                ) : (
                                    <PushPin
                                        onClick={() => setIsPinned(true)}
                                        weight="fill"
                                        className="cursor-pointer fill-neutral-600 hover:fill-neutral-950 dark:fill-neutral-200 dark:hover:fill-neutral-400 transition-colors"
                                        size={iconSize}
                                    />
                                )}
                                <div className="flex">
                                    <Plus
                                        size={iconSize}
                                        className="cursor-pointer fill-neutral-600 hover:fill-neutral-950 dark:fill-neutral-200 dark:hover:fill-neutral-400 transition-colors"
                                        onClick={createNewConversation}
                                    />
                                </div>
                                {screenSize.width < 768 && (
                                    <button
                                        onClick={() => setIsExpanded(false)}
                                    >
                                        <X
                                            size={iconSize}
                                            className="fill-red-600 hover:fill-red-400 dark:fill-red-500 dark:hover:fill-red-700 transition-colors"
                                        />
                                    </button>
                                )}
                            </div>

                            <hr className="border border-neutral-400 dark:border-neutral-300 my-2" />

                            <h3 className="text-lg font-bold text-neutral-600 dark:text-neutral-300 ml-2">
                                Conversations
                            </h3>

                            {isLoading && (
                                <div className="text-sm text-center py-2">
                                    Loading conversations...
                                </div>
                            )}

                            {error && (
                                <div className="text-sm text-red-500 text-center py-2">
                                    {error}
                                </div>
                            )}

                            {!isLoading && conversations.length === 0 && (
                                <div className="text-sm text-left text-neutral-600 dark:text-neutral-300 my-2 ml-2">
                                    No conversations yet.
                                </div>
                            )}

                            {conversations.map((conversation) => (
                                <div
                                    key={conversation.id}
                                    className={`flex px-2 py-1 gap-1 justify-between items-center text-sm text-left cursor-pointer hover:text-neutral-500 dark:hover:text-neutral-400 transition-colors ${
                                        currentConversationId ===
                                        conversation.id
                                            ? "rounded-md bg-blue-800/10"
                                            : ""
                                    }`}
                                >
                                    <div
                                        className="flex items-center gap-1"
                                        onClick={() => {
                                            if (onSelectConversation) {
                                                onSelectConversation(
                                                    conversation.id
                                                );
                                            }
                                            if (screenSize.width < 768) {
                                                setIsExpanded(false);
                                            }
                                        }}
                                    >
                                        <ChatsCircle size={14} weight="bold" />
                                        <p className="line-clamp-1 text-xs md:text-sm">
                                            {conversation.title}
                                        </p>
                                    </div>
                                    <button
                                        onClick={(e) =>
                                            deleteConversation(
                                                conversation.id,
                                                e
                                            )
                                        }
                                    >
                                        <MinusCircle
                                            size={14}
                                            className="fill-red-600 hover:fill-red-400 dark:fill-red-500 dark:hover:fill-red-700 transition-colors"
                                        />
                                    </button>
                                </div>
                            ))}
                        </motion.div>
                    ) : null}
                </motion.div>
            </motion.div>
        </div>
    );
}

export default ChatsSideMenu;
