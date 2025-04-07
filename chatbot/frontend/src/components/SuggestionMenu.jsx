import React, { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { ClipLoader } from "react-spinners";

// Main component for the suggestion menu
const SuggestionMenu = ({ category, onBack }) => {
    const [menuData, setMenuData] = useState(null);
    const [path, setPath] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [direction, setDirection] = useState(1); // 1 for forward, -1 for backward

    // Keep track of menu history
    const historyRef = useRef([]);

    // Fetch initial menu data (mount/category update)
    useEffect(() => {
        fetchMenuData(category);
    }, [category]);

    // Function to fetch menu data from API
    const fetchMenuData = async (
        category,
        selection = null,
        goingBack = false
    ) => {
        setLoading(true);
        setError(null);
        setDirection(goingBack ? -1 : 1);

        // sample API request & response

        // delay to simulate loading
        await new Promise((resolve) => setTimeout(resolve, 500));
        // Sample data
        setMenuData({
            question: "What would you like to know?",
            options: [
                { label: "Option 1", value: "option1" },
                { label: "Option 2", value: "option2" },
            ],
            content: "<p>This is some content.</p>",
            breadcrumbs: ["Home", "Category"],
        });

        // Uncomment the following code to make an actual API request

        // try {
        //     // Prepare request data
        //     const requestData = {
        //         category: category,
        //         path: path,
        //     };

        //     // Include selection if provided
        //     if (selection !== null) {
        //         requestData.selection = selection;
        //     }

        //     // Get auth token
        //     const token = localStorage.getItem("token");

        //     // Make API request
        //     const response = await fetch("http://localhost:5001/api/menu", {
        //         method: "POST",
        //         headers: {
        //             "Content-Type": "application/json",
        //             Authorization: `Bearer ${token}`,
        //         },
        //         body: JSON.stringify(requestData),
        //     });

        //     if (!response.ok) {
        //         throw new Error(`API error: ${response.status}`);
        //     }

        //     const data = await response.json();
        //     setMenuData(data);

        // Update history if moving forward
        if (!goingBack && selection !== null) {
            // Store current state in history
            historyRef.current = [
                ...historyRef.current,
                {
                    category,
                    path: [...path],
                    menuData: menuData,
                },
            ];

            // Update path with new selection
            setPath([...path, selection]);
        }
        // } catch (err) {
        //     console.error("Error fetching menu data:", err);
        //     setError("Failed to load menu data. Please try again.");
        // } finally {
        setLoading(false);
        // }
    };

    // Handle option selection
    const handleSelect = (selection) => {
        fetchMenuData(category, selection);
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
            // Update path to previous state
            setPath(prevState.path);

            // Fetch menu data for previous path
            fetchMenuData(category, null, true);
        } else {
            // If no history (shouldn't happen), just go back one level
            const newPath = [...path];
            newPath.pop();
            setPath(newPath);
            fetchMenuData(category, null, true);
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

    // Render menu content
    const renderMenuContent = () => {
        if (loading) return renderLoader();
        if (error) return renderError();
        if (!menuData) return null;

        return (
            <motion.div
                key={path.length} // Important: key changes trigger animation
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{
                    x: { type: "spring", stiffness: 300, damping: 30 },
                    opacity: { duration: 0.2 },
                }}
            >
                {/* Subtitle/Question */}
                {menuData.question && (
                    <div className="mb-4">
                        <h3 className="text-lg font-medium">
                            {menuData.question}
                        </h3>
                    </div>
                )}

                {/* Menu Options */}
                <div className="grid grid-cols-1 gap-3">
                    {menuData.options &&
                        menuData.options.map((option, index) => (
                            <button
                                key={index}
                                onClick={() => handleSelect(option.value)}
                                className="p-4 text-left bg-white dark:bg-neutral-700 rounded-lg shadow hover:bg-neutral-100 dark:hover:bg-neutral-600 transition-colors"
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

                {/* Content block if present */}
                {menuData.content && (
                    <div className="mt-4 p-4 bg-white dark:bg-neutral-700 rounded-lg shadow">
                        <div
                            dangerouslySetInnerHTML={{
                                __html: menuData.content,
                            }}
                        />
                    </div>
                )}
            </motion.div>
        );
    };

    return (
        <div className="flex flex-col my-auto">
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
                            setPath([]);
                            fetchMenuData(category, null, true);
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
                                        fetchMenuData(category, null, true);
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
                    className="w-full py-3 bg-neutral-200 dark:bg-neutral-700 rounded-lg hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-colors"
                >
                    Return to Chat
                </button>
            </div>
        </div>
    );
};

export default SuggestionMenu;
