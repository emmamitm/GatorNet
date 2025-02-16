import { React, useState } from "react";
import { motion } from "motion/react";
import { MinusCircle, ChatsCircle, UserCircle } from "@phosphor-icons/react";

function ChatsSideMenu() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [chats, setChats] = useState([
    { name: "Computer Science Clubs" },
    { name: "Bus Schedule" },
    { name: "Weather in Gainesville" },
  ]);

  if (isExpanded) {
    // Expanded
    return (
      <motion.div
        className="fixed left-0 h-full flex flex-col justify-between p-2 border-r-2 border-neutral-200 rounded-r-xl bg-neutral-200/50 backdrop-blur-lg"
        onMouseOver={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
        animate={{ width: 250 }}
        transition={{ duration: 0.2 }}
      >
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
              className="flex gap-2 justify-between items-center text-sm text-left cursor-pointer hover:text-neutral-500"
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
                onClick={() => {
                  setChats(chats.filter((_, i) => i !== index));
                }}
              >
                <MinusCircle
                  size={18}
                  className="fill-red-600 hover:fill-red-400 transition-colors"
                />
              </button>
            </div>
          ))}
        </motion.div>

        <motion.div
          className="flex justify-between border-t-1 border-neutral-300 pt-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="flex gap-1">
            <UserCircle size={20} />
            <button className="text-sm text-neutral-600 hover:text-neutral-400 transition-all cursor-pointer">
              User Name
            </button>
          </div>

          <button className="text-sm hover:text-neutral-500 transition-all underline cursor-pointer">
            Log out
          </button>
        </motion.div>
      </motion.div>
    );
  } else {
    // Collapsed
    return (
      <motion.div
        className="fixed left-0 p-2 flex flex-col h-full backdrop-blur-lg bg-neutral-200/50 border-r-2 border-neutral-200 rounded-r-xl"
        onMouseOver={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
        animate={{ width: 30 }}
        transition={{ duration: 0.2 }}
      ></motion.div>
    );
  }
}

export default ChatsSideMenu;
