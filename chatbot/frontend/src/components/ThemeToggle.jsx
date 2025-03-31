import React from "react";
import { useTheme } from "../theme/ThemeContext";
import { Sun, Moon } from "@phosphor-icons/react";

function ThemeToggle() {
    const { darkMode, toggleTheme } = useTheme();
    const iconSize = 20;

    return (
        <button
            onClick={() => {
                toggleTheme();
            }}
            aria-label={
                darkMode ? "Switch to light mode" : "Switch to dark mode"
            }
            className="p-2 rounded-full hover:bg-neutral-100/40 active:bg-neutral-200/20 transition-colors"
        >
            {darkMode ? (
                <Moon
                    size={iconSize}
                    weight="fill"
                    className="fill-neutral-50"
                />
            ) : (
                <Sun
                    size={iconSize}
                    weight="fill"
                    className="fill-neutral-50"
                />
            )}
        </button>
    );
}

export default ThemeToggle;
