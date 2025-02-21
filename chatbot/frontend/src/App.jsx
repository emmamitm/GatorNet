import React from "react";
import "./css/output.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";

// auth
import { AuthProvider } from "./auth/AuthContext";
import { withAuth } from "./auth/ProtectedRoute";

// pages
import Welcome from "./pages/Welcome";
import LogIn from "./pages/LogIn";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";

// protected routes
const ProtectedDashboard = withAuth(Dashboard);
// TODO: const ProtectedProfile = withAuth(Profile);

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Welcome />} />
                    <Route path="/login" element={<LogIn />} />
                    <Route path="/signup" element={<SignUp />} />
                    <Route path="/dashboard" element={<ProtectedDashboard />} />
                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
