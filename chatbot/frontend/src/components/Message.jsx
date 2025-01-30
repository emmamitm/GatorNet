import React from "react";

function Message({ key, text, isUser }) {
  return (
    <div
      key={key}
      className={`p-3 my-2 rounded-xl w-fit border ${
        isUser
          ? "bg-blue-200 border-blue-400 self-end ml-12"
          : "bg-white border-gray-300 mr-12"
      }`}
    >
      {text}
    </div>
  );
}

export default Message;
