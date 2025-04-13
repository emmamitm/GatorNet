import React, { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { ClipLoader } from "react-spinners";
import api from "../axiosApi";

// Main component for the suggestion menu
const SuggestionMenu = ({ category, onBack }) => {
    const [menuData, setMenuData] = useState(null);
    const [path, setPath] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [direction, setDirection] = useState(1); // 1 for forward, -1 for backward
    const [customInput, setCustomInput] = useState("");

    // Keep track of menu history
    const historyRef = useRef([]);

    // Fetch initial menu data (mount/category update)
    useEffect(() => {
        fetchMenuData(category, null, false, []);
        console.log("Fetching initial menu data for category:", category);
    }, [category]);

    // Function to fetch menu data from API using axios
    const fetchMenuData = async (
        category,
        selection = null,
        goingBack = false,
        currentPath = path // Use current path by default, but allow override
    ) => {
        setLoading(true);
        setError(null);
        setDirection(goingBack ? -1 : 1);

        // Prepare request data
        // use the path that's passed in, not the state variable which might not have updated yet
        const requestData = {
            category: category,
            path: currentPath,
        };

        // Include selection if provided
        if (selection !== null) {
            requestData.selection = selection;
        }

        try {
            console.log("Sending request with path:", currentPath);

            // Make API request using axios
            const response = await api.post("/menu", requestData);
            const data = response.data;

            // Debug logging
            console.log("Request data:", requestData);
            console.log("Response data:", data);

            setMenuData(data);

            // Reset custom input when navigating
            setCustomInput("");
        } catch (err) {
            console.error("Error fetching menu data:", err);
            setError(
                `Failed to load menu data: ${
                    err.response?.data?.message || err.message
                }. Please try again.`
            );
        } finally {
            setLoading(false);
        }
    };

    // Handle option selection
    const handleSelect = (selection) => {
        // Store current state in history before updating
        historyRef.current = [
            ...historyRef.current,
            {
                category,
                path: [...path],
                menuData: menuData,
            },
        ];

        // Calculate the new path that will include this selection
        const newPath = [...path, selection];

        // Update the path state
        setPath(newPath);

        // Then fetch data with the new path
        fetchMenuData(category, selection, false, newPath);

        console.log("Selected option:", selection, "New path:", newPath);
    };

    // Handle custom input submission
    const handleCustomInputSubmit = () => {
        // Store current state in history
        historyRef.current = [
            ...historyRef.current,
            {
                category,
                path: [...path],
                menuData: menuData,
            },
        ];

        // Calculate the new path
        const newPath = [...path, customInput.trim()];

        // Update the path state
        setPath(newPath);

        // Fetch with the new path
        fetchMenuData(category, customInput.trim(), false, newPath);

        console.log(
            "Custom input submitted:",
            customInput,
            "New path:",
            newPath
        );
    };

    // Handle back button click
    const handleBack = () => {
        if (path.length === 0) {
            // If at root level, exit menu
            onBack();
            return;
        }

        // Get previous state from history
        const prevState = historyRef.current.pop();

        if (prevState) {
            // Get the previous path from history
            const previousPath = prevState.path;
            console.log("Going back to previous path:", previousPath);

            // Update path state
            setPath(previousPath);

            // Fetch menu data for previous path
            fetchMenuData(category, null, true, previousPath);
        } else {
            // If no history (shouldn't happen), just go back one level
            const newPath = [...path];
            newPath.pop();
            console.log("No history found, calculating new path:", newPath);

            // Update path state
            setPath(newPath);

            // Fetch with the new path
            fetchMenuData(category, null, true, newPath);
        }
    };

    // Functions to generate title based on category
    const getCategoryTitle = () => {
        const titles = {
            events: "Events on Campus",
            libraries: "Campus Libraries",
            academics: "Explore Academics",
            clubs: "Discover Clubs",
            housing: "Housing Options",
            tuition: "Tuition and Fees",
        };
        return titles[category] || "Menu";
    };

    // Render loader
    const renderLoader = () => (
        <div className="flex items-center justify-center gap-2">
            <ClipLoader
                loading={loading}
                size={25}
                aria-label="Loading Spinner"
                data-testid="loader"
            />
            <p className="text-neutral-500 dark:text-neutral-400">Loading...</p>
        </div>
    );

    // Render error message
    const renderError = () => (
        <div className="p-4 bg-red-100 dark:bg-red-900 rounded-lg text-red-800 dark:text-red-200">
            <p>{error}</p>
            <button
                onClick={() => fetchMenuData(category)}
                className="mt-2 px-4 py-2 bg-neutral-200 dark:bg-neutral-700 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
                Retry
            </button>
        </div>
    );

    // Animation variants for motion
    const variants = {
        enter: (direction) => ({
            x: direction > 0 ? 300 : -300,
            opacity: 0,
        }),
        center: {
            x: 0,
            opacity: 1,
        },
        exit: (direction) => ({
            x: direction < 0 ? 300 : -300,
            opacity: 0,
        }),
    };

    // Render custom input field when needed
    const renderCustomInput = () => {
        if (!menuData || !menuData.hasCustomInput) return null;

        return (
            <div className="mt-4">
                <div className="flex">
                    <input
                        type="text"
                        value={customInput}
                        onChange={(e) => setCustomInput(e.target.value)}
                        placeholder={
                            menuData.inputPlaceholder || "Enter value..."
                        }
                        className="flex-grow p-2 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-700 dark:border-neutral-600"
                        onKeyDown={(e) =>
                            e.key === "Enter" && handleCustomInputSubmit()
                        }
                    />
                    <button
                        onClick={handleCustomInputSubmit}
                        className="px-4 py-2 bg-blue-500 text-white rounded-r hover:bg-blue-600 transition-colors"
                    >
                        Submit
                    </button>
                </div>
            </div>
        );
    };

    // Render menu content
    const renderMenuContent = () => {
        if (loading) return renderLoader();
        if (error) return renderError();
        if (!menuData) return null;

        return (
            <motion.div
                key={path.join("-") || "root"} // Unique key for each path
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{
                    x: { type: "spring", stiffness: 300, damping: 30 },
                    opacity: { duration: 0.2 },
                }}
                className="flex flex-col"
            >
                {/* Content block if present */}
                {menuData.content && (
                    <div className="mb-4 p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                        <div
                            dangerouslySetInnerHTML={{
                                __html: menuData.content,
                            }}
                        />
                    </div>
                )}

                {/* Subtitle/Question */}
                {menuData.question && (
                    <div className="mb-4">
                        <h3 className="text-lg font-medium">
                            {menuData.question}
                        </h3>
                    </div>
                )}

                {/* Menu Options */}
                {menuData.options && menuData.options.length > 0 && (
                    <div className="grid grid-cols-1 gap-3">
                        {menuData.options.map((option, index) => (
                            <button
                                key={`${option.value}-${index}`}
                                onClick={() => handleSelect(option.value)}
                                className="p-4 text-left bg-neutral-100 dark:bg-neutral-800 rounded-lg shadow hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
                            >
                                <h3 className="font-semibold">
                                    {option.label}
                                </h3>
                                {option.description && (
                                    <p className="text-sm text-neutral-500 dark:text-neutral-400">
                                        {option.description}
                                    </p>
                                )}
                            </button>
                        ))}
                    </div>
                )}

                {/* Custom Input Field */}
                {renderCustomInput()}
            </motion.div>
        );
    };

    return (
        <div className="flex flex-col w-full my-auto py-4">
            {/* Header with title and back button */}
            <div className="flex items-center mb-4">
                <button
                    onClick={handleBack}
                    className="mr-3 p-2 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="24"
                        height="24"
                        fill="currentColor"
                        viewBox="0 0 256 256"
                    >
                        <path d="M228,128a12,12,0,0,1-12,12H69l51.52,51.51a12,12,0,0,1-17,17l-72-72a12,12,0,0,1,0-17l72-72a12,12,0,0,1,17,17L69,116H216A12,12,0,0,1,228,128Z"></path>
                    </svg>
                </button>
                <h2 className="text-2xl font-bold">{getCategoryTitle()}</h2>
            </div>

            {/* Breadcrumb navigation if we have path history */}
            {path.length > 0 && menuData && menuData.breadcrumbs && (
                <div className="flex items-center text-sm text-neutral-500 dark:text-neutral-400 mb-4 overflow-x-auto">
                    <span
                        onClick={() => {
                            const emptyPath = [];
                            setPath(emptyPath);
                            fetchMenuData(category, null, true, emptyPath);
                        }}
                        className="cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-300 whitespace-nowrap"
                    >
                        {getCategoryTitle()}
                    </span>

                    {menuData.breadcrumbs.map((crumb, index) => (
                        <React.Fragment key={index}>
                            <span className="mx-2">/</span>
                            <span
                                onClick={() => {
                                    // Only allow clicking on breadcrumbs that aren't the current one
                                    if (
                                        index <
                                        menuData.breadcrumbs.length - 1
                                    ) {
                                        // Go back to that specific level
                                        const newPath = path.slice(
                                            0,
                                            index + 1
                                        );
                                        setPath(newPath);
                                        fetchMenuData(
                                            category,
                                            null,
                                            true,
                                            newPath
                                        );
                                    }
                                }}
                                className={`whitespace-nowrap ${
                                    index < menuData.breadcrumbs.length - 1
                                        ? "cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-300"
                                        : ""
                                }`}
                            >
                                {crumb}
                            </span>
                        </React.Fragment>
                    ))}
                </div>
            )}

            {/* Main menu content with motion animation */}
            <motion.div
                className="flex-1"
                animate={{ opacity: 1 }}
                initial={{ opacity: 0 }}
            >
                {renderMenuContent()}
            </motion.div>

            {/* Return to Chat button */}
            <div className="mt-auto pt-4">
                <button
                    onClick={onBack}
                    className="w-full py-3 bg-blue-100 dark:bg-gray-700 rounded-lg hover:bg-blue-200 dark:hover:bg-gray-600 transition-colors"
                >
                    Return to Chat
                </button>
            </div>
        </div>
    );
};

export default SuggestionMenu;
