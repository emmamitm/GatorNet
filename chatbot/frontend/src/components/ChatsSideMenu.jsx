import { React, useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    MinusCircle,
    ChatsCircle,
    Chats,
    PushPin,
    PushPinSlash,
    Plus,
    MagnifyingGlass,
    X,
} from "@phosphor-icons/react";

function ChatsSideMenu() {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const [chats, setChats] = useState([
        { name: "Computer Science Clubs" },
        { name: "Bus Schedule" },
        { name: "Weather in Gainesville" },
    ]);
    const [screenSize, setScreenSize] = useState({
        width: window.innerWidth,
        height: window.innerHeight,
    });

    useEffect(() => {
        const handleResize = () => {
            setScreenSize({
                width: window.innerWidth,
                height: window.innerHeight,
            });
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const iconSize = 25;

    return (
        <div>
            {screenSize.width < 768 && (
                <div className="fixed md:hidden left-2 top-2">
                    <button
                        className="p-2 rounded-full bg-neutral-100 hover:bg-neutral-100/75 transition-colors"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        <Chats size={iconSize} />
                    </button>
                </div>
            )}
            {isExpanded && (
                <motion.div
                    className="md:hidden fixed inset-0 top-16 bg-neutral-100/50 bg-opacity-50 z-10"
                    onClick={() => {
                        setIsExpanded(false);
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                ></motion.div>
            )}
            <motion.div className="max-h-fit md:max-h-full z-20 relative">
                <motion.div
                    className="fixed md:top-0 left-0 md:p-2 h-full backdrop-blur-xl bg-neutral-200/60 border-r-2 border-neutral-200 rounded-r-xl"
                    {...(screenSize.width >= 768 && {
                        onMouseOver: () => {
                            if (!isPinned) setIsExpanded(true);
                        },
                        onMouseLeave: () => {
                            if (!isPinned) setIsExpanded(false);
                        },
                    })}
                    animate={{
                        width: isExpanded
                            ? 250
                            : screenSize.width < 768
                            ? 0
                            : 30,
                    }}
                    transition={{ duration: 0.2 }}
                >
                    {isExpanded ? (
                        <motion.div
                            className="flex flex-col gap-2 p-3 md:p-0"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                        >
                            <div className="flex justify-between">
                                {/* <h1 className="text-2xl font-bold">Chats</h1> */}
                                {isPinned ? (
                                    <PushPinSlash
                                        onClick={() => setIsPinned(false)}
                                        weight="fill"
                                        className="cursor-pointer hover:fill-neutral-950 transition-colors"
                                        size={iconSize}
                                    />
                                ) : (
                                    <PushPin
                                        onClick={() => setIsPinned(true)}
                                        weight="fill"
                                        className="cursor-pointer hover:fill-neutral-950 transition-colors"
                                        size={iconSize}
                                    />
                                )}
                                <div className="flex">
                                    <MagnifyingGlass
                                        size={iconSize}
                                        className="cursor-pointer hover:fill-neutral-950 transition-colors"
                                    />
                                    <Plus
                                        size={iconSize}
                                        className="cursor-pointer hover:fill-neutral-950 transition-colors"
                                    />
                                </div>
                                {screenSize.width < 768 && (
                                    <button
                                        onClick={() => setIsExpanded(false)}
                                    >
                                        <X
                                            size={iconSize}
                                            className="fill-red-600 hover:fill-red-400 transition-colors"
                                        />
                                    </button>
                                )}
                            </div>

                            <hr className="border border-neutral-300" />

                            {chats.map((chat, index) => (
                                <div
                                    key={index}
                                    className="flex gap-2 justify-between items-center text-sm text-left cursor-pointer hover:text-neutral-500"
                                >
                                    <div
                                        className="flex items-center gap-1"
                                        onClick={() =>
                                            console.log(
                                                "Chat clicked: ",
                                                chat.name
                                            )
                                        }
                                    >
                                        <ChatsCircle size={14} weight="bold" />
                                        {chat.name}
                                    </div>
                                    <button
                                        onClick={() =>
                                            setChats(
                                                chats.filter(
                                                    (_, i) => i !== index
                                                )
                                            )
                                        }
                                    >
                                        <MinusCircle
                                            size={18}
                                            className="fill-red-600 hover:fill-red-400 transition-colors"
                                        />
                                    </button>
                                </div>
                            ))}
                        </motion.div>
                    ) : null}
                </motion.div>
            </motion.div>
        </div>
    );
}

export default ChatsSideMenu;
