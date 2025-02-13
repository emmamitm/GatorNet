import React, { useState, useEffect } from "react";
import "./css/output.css";
import ChatsSideMenu from "./components/ChatsSideMenu";

import { TopBar } from "./components/TopBar";
import AppContent from "./AppContent";

function App() {
  return (
    <div className="flex flex-col h-screen">
      <TopBar>
        <ChatsSideMenu chats={[{ name: "Chat 1" }, { name: "Chat 2" }]} />
        <AppContent />
      </TopBar>
    </div>
  );
}

export default App;
