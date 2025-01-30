import React from "react";

function Suggestion({ text, func }) {
  return (
    <button
      className="p-3 m-0 rounded-xl border-2 bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200 text-gray-700 cursor-pointer transition-colors duration-200 hover:from-gray-100 hover:to-gray-200 active:from-gray-200 active:to-gray-300"
      onClick={func}
    >
      {text}
    </button>
  );
}

export default Suggestion;
