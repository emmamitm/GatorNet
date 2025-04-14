import React from "react";
import "./css/output.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";

// auth
import { AuthProvider } from "./auth/AuthContext";
import { withAuth } from "./auth/ProtectedRoute";

// pages
import Welcome from "./pages/Welcome";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";
import CampusMap from './pages/CampusMap';

// protected routes
const ProtectedDashboard = withAuth(Dashboard);
// TODO: const ProtectedProfile = withAuth(Profile);

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Welcome />} />
                    <Route path="/signup" element={<SignUp />} />
                    <Route path="/dashboard" element={<ProtectedDashboard />} />
                    <Route path="/campus-map" element={<CampusMap />} />
                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
