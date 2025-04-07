import React, { useState, useRef, useEffect } from "react";
import { ArrowCircleUp } from "@phosphor-icons/react";
import Message from "./Message";
import Suggestion from "./Suggestion";
import { motion } from "motion/react";

const ChatInterface = ({
    messages,
    onSendMessage,
    onMenuSelect,
    isConnected = true,
}) => {
    const [input, setInput] = useState("");
    const [isPlaceholder, setIsPlaceholder] = useState(true);
    const inputRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const lastMessageRef = useRef(null);
    const messagesLengthRef = useRef(messages.length);
    const prevIsLoadingRef = useRef(false);
    const [isAnyMessageLoading, setIsAnyMessageLoading] = useState(() =>
        messages.some((msg) => msg.isLoading)
    );

    useEffect(() => {
        setIsAnyMessageLoading(messages.some((msg) => msg.isLoading));
    }, [messages]);

    // Initialize input ref with placeholder
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.textContent = "Type your message...";
        }
    }, []);

    // Function to handle scrolling to the bottom
    const scrollToBottom = () => {
        requestAnimationFrame(() => {
            if (messagesContainerRef.current) {
                // For a flex-col-reverse container, 0 is the bottom (newest messages)
                messagesContainerRef.current.scrollTop = 0;
            }

            // Backup approach using lastMessageRef
            if (lastMessageRef.current) {
                lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
            }
        });

        // Additional delayed scroll to catch any layout shifts
        setTimeout(() => {
            if (messagesContainerRef.current) {
                messagesContainerRef.current.scrollTop = 0;
            }
        }, 100);
    };

    // Track message changes and handle scrolling
    useEffect(() => {
        // If messages array has changed
        if (messages.length !== messagesLengthRef.current) {
            // Update our ref to the new length
            messagesLengthRef.current = messages.length;
            scrollToBottom();
        }

        // Check if loading state changed from true to false
        const currentIsLoading = messages.some((msg) => msg.isLoading);
        if (prevIsLoadingRef.current && !currentIsLoading) {
            // Loading state changed from true to false - an AI message was updated
            scrollToBottom();
        }
        prevIsLoadingRef.current = currentIsLoading;
    }, [messages]);

    const handleSubmit = (e) => {
        // Prevent default form submission
        e.preventDefault();
        if (!input.trim() || isAnyMessageLoading) return;

        // Send the message
        onSendMessage(input.trim());

        // Clear input field
        setInput("");
        if (inputRef.current) {
            inputRef.current.textContent = "";
            setIsPlaceholder(true);
        }

        // Scroll to bottom after short delay
        // to ensure the new message is visible before the scroll
        setTimeout(() => {
            scrollToBottom();
        }, 50);
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
        <motion.div
            className="flex flex-col flex-1 justify-end"
            initial={{
                opacity: 0,
                y: 50,
            }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.3 }}
        >
            {/* Suggestions (if no messages) */}
            {messages.length === 0 ? (
                <>
                    <h1 className="text-2xl md:text-3xl font-bold m-2 mt-auto mx-auto mb-4">
                        What would you like to know?
                    </h1>
                    <div className="flex justify-center mb-auto mx-auto whitespace-nowrap flex-wrap gap-2 md:gap-4 sm:max-w-md md:max-w-lg">
                        <Suggestion
                            text="Events on Campus"
                            func={() => onMenuSelect("events")}
                        />
                        <Suggestion
                            text="Find a Library"
                            func={() => onMenuSelect("libraries")}
                        />
                        <Suggestion
                            text="Explore Academics"
                            func={() => onMenuSelect("academics")}
                        />
                        <Suggestion
                            text="Discover Clubs"
                            func={() => onMenuSelect("clubs")}
                        />
                        <Suggestion
                            text="Housing Options"
                            func={() => onMenuSelect("housing")}
                        />
                        <Suggestion
                            text="Tuition and Fees"
                            func={() => onMenuSelect("tuition")}
                        />
                    </div>
                </>
            ) : (
                /* Messages */
                <div
                    ref={messagesContainerRef}
                    className="overflow-y-auto scroll flex flex-col-reverse h-full pb-2 px-1"
                >
                    {/* Using two approaches: container scrollTop and lastMessageRef */}
                    {messages
                        .slice(0)
                        .reverse()
                        .map((msg, idx) => (
                            <Message
                                key={msg.id || idx}
                                text={msg.text}
                                isUser={msg.isUser}
                                isLoading={msg.isLoading}
                                ref={idx === 0 ? lastMessageRef : null}
                            />
                        ))}
                </div>
            )}

            {/* Message input */}
            <div className="w-full pb-2 sticky bottom-0 bg-gradient-to-b from-35% to-45% from-transparent to-white dark:to-neutral-900">
                {!isConnected && (
                    <div className="text-red-500 text-center p-2">
                        Warning: Backend not connected. Messages won't be
                        processed.
                    </div>
                )}
                <form
                    onSubmit={handleSubmit}
                    className="flex justify-between gap-2 md:max-w-3xl mx-auto rounded-2xl p-4 bg-neutral-100 dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700"
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
                            if (e.key === "Enter" && !isAnyMessageLoading) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                    >
                        Type your message...
                    </div>
                    <button
                        disabled={isAnyMessageLoading}
                        type="submit"
                        aria-label="Send message"
                        className="outline-none transition-colors"
                    >
                        <ArrowCircleUp
                            size={32}
                            weight="fill"
                            className="fill-neutral-700 hover:fill-neutral-500 active:fill-black dark:fill-neutral-300 dark:hover:fill-neutral-400 dark:active:fill-neutral-100"
                        />
                    </button>
                </form>
            </div>
        </motion.div>
    );
};

export default ChatInterface;
