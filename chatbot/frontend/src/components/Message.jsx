import React from "react";
import { ClipLoader } from "react-spinners";

function Message({ text, isUser, isLoading }) {
    // if the message is loading, display a loading spinner
    if (isLoading) {
        return (
            <div
                className={`flex items-center my-2 w-fit ${
                    isUser ? "self-end ml-12 flex-row-reverse" : "mr-12"
                }`}
            >
                <div
                    className={`flex items-center p-3 rounded-xl bg-gradient-to-tr ${
                        isUser
                            ? "from-blue-100 to-cyan-100 dark:from-blue-900 dark:to-cyan-900"
                            : "from-neutral-100 to-slate-100 dark:from-neutral-800 dark:to-neutral-800"
                    }`}
                >
                    <ClipLoader size={15} color="rgb(115 115 115)" />
                    <div className="ml-1 text-neutral-500 dark:text-neutral-400">
                        Thinking...
                    </div>
                </div>
            </div>
        );
    }

    // if the message is not loading, display the message text
    return (
        <div className={`flex p-2 ${isUser ? "justify-end" : "justify-start"}`}>
            <div
                className={`flex items-center p-3 rounded-xl bg-gradient-to-tr ${
                    isUser
                        ? "from-blue-100 to-cyan-100 dark:from-slate-700 dark:to-slate-700 dark:text-neutral-100"
                        : "from-neutral-100 to-neutral-100 dark:from-neutral-800 dark:to-neutral-800 dark:text-neutral-200"
                }`}
            >
                <div>{text}</div>
            </div>
        </div>
    );
}

export default Message;
