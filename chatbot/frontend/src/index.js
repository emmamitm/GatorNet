import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { BrowserRouter, Routes, Route } from "react-router";
import "./index.css";

// pages
import Welcome from "./pages/Welcome";
import LogIn from "./pages/LogIn";
import SignUp from "./pages/SignUp";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/welcome" element={<Welcome />} />
      <Route path="/login" element={<LogIn />} />
      <Route path="/signup" element={<SignUp />} />
    </Routes>
  </BrowserRouter>
);
