import { React, useState } from "react";
import { motion } from "motion/react";
import { MinusCircle, ChatsCircle } from "@phosphor-icons/react";

function ChatsSideMenu() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [chats, setChats] = useState([
    { name: "Computer Science Clubs" },
    { name: "Bus Schedule" },
    { name: "Weather in Gainesville" },
  ]);

  return (
    <div className="max-h-full">
    <motion.div
      className="fixed left-0 p-2 h-full backdrop-blur-lg bg-gray-200/50 border-r-2 border-gray-200 rounded-r-xl"
      onMouseOver={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
      animate={{ width: isExpanded ? 250 : 30 }}
      transition={{ duration: 0.2 }}
    >
      {isExpanded ? (
        <motion.div
          className="flex flex-col gap-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h1 className="text-2xl font-bold">Chats</h1>
          {chats.map((chat, index) => (
            <div
              key={index}
              className="flex justify-between items-center text-sm text-left cursor-pointer hover:text-gray-500"
            >
              <div
                className="flex items-center gap-1"
                onClick={() => console.log("Chat clicked: ", chat.name)}
              >
                <ChatsCircle size={14} weight="bold" />
                {chat.name}
              </div>
              <button
                className="cursor-pointer"
                onClick={() => setChats(chats.filter((_, i) => i !== index))}
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
    </div>
  );
  
}

export default ChatsSideMenu;
