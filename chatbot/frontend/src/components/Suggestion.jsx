import React from "react";

function Suggestion({ text, func }) {
    return (
        <button
            className="p-2 m-0 text-left w-fit rounded-xl border-2 bg-gradient-to-br from-neutral-50 to-neutral-100 border-neutral-200 text-neutral-700 transition-colors duration-200 hover:from-neutral-100 hover:to-neutral-200 active:from-neutral-200 active:to-neutral-300"
            onClick={func}
        >
            {text}
        </button>
    );
}

export default Suggestion;
