import React from "react";

function Message({ key, text, isUser }) {
    return (
        <div
            key={key}
            className={`flex items-center my-2 w-fit ${
                isUser ? "self-end ml-12 flex-row-reverse" : "mr-12"
            }`}
        >
            <div
                className={`flex items-center p-3 rounded-xl bg-gradient-to-tr ${
                    isUser
                        ? "from-blue-100 to-cyan-100"
                        : "from-neutral-100 to-slate-100"
                }`}
            >
                <div>{text}</div>
            </div>
        </div>
    );
}

export default Message;
