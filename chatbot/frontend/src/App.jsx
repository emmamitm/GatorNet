import React, { useState, useEffect } from "react";
import "./css/output.css";
import { Routes, Route } from "react-router";

// pages
import Welcome from "./pages/Welcome";
import LogIn from "./pages/LogIn";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";

function App() {
    return (
        <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/welcome" element={<Welcome />} />
            <Route path="/login" element={<LogIn />} />
            <Route path="/signup" element={<SignUp />} />
        </Routes>
    );
}

export default App;
