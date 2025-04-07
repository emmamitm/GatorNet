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
    const isAnyMessageLoading = messages.some((msg) => msg.isLoading);

    // Initialize input ref with placeholder
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.textContent = "Type your message...";
        }
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        // Send the message
        onSendMessage(input.trim());

        // Clear input field
        setInput("");
        if (inputRef.current) {
            inputRef.current.textContent = "";
            setIsPlaceholder(true);
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
        <motion.div
            className="flex flex-col flex-1"
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
                <div className="overflow-y-auto scroll flex flex-col-reverse h-full pb-2 px-1">
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
                            if (e.key === "Enter") {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                    >
                        Type your message...
                    </div>
                    <button type="submit" disabled={isAnyMessageLoading}>
                        <ArrowCircleUp
                            size={32}
                            weight="fill"
                            className="fill-neutral-700 hover:fill-neutral-500 active:fill-black dark:fill-neutral-300 dark:hover:fill-neutral-400 dark:active:fill-neutral-100 outline-none transition-colors"
                        />
                    </button>
                </form>
            </div>
        </motion.div>
    );
};

export default ChatInterface;
