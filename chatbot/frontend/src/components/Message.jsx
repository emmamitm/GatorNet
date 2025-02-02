import React from "react";

function Message({ key, text, isUser }) {
  return (
    <div
      key={key}
      className={`flex items-center my-2 w-fit ${
        isUser ? "self-end ml-12 flex-row-reverse" : "mr-12"
      }`}
    >
      <img
        src={isUser ? "https://picsum.photos/200" : "https://picsum.photos/id/237/200/200"}
        alt="avatar"
        className="w-12 h-12 rounded-full mx-2"
      />
      <div
        className={`flex items-center p-3 rounded-xl border ${
          isUser ? "bg-blue-200 border-blue-400" : "bg-white border-gray-300"
        }`}
      >
        <div>{text}</div>
      </div>
    </div>
  );
}

export default Message;
