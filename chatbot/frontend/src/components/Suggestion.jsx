import React from "react";

function Suggestion({ text, func }) {
    return (
        <button
            className="p-2 m-0 text-left w-fit rounded-xl border-2 
            bg-gradient-to-br from-neutral-50 to-neutral-100 border-neutral-200 text-neutral-700 
            dark:from-neutral-800 dark:to-neutral-900 dark:border-neutral-700 dark:text-neutral-300
            transition-colors duration-200 
            hover:from-neutral-100 hover:to-neutral-200 
            dark:hover:from-neutral-700 dark:hover:to-neutral-800
            active:from-neutral-200 active:to-neutral-300
            dark:active:from-neutral-600 dark:active:to-neutral-700"
            onClick={func}
        >
            {text}
        </button>
    );
}

export default Suggestion;
