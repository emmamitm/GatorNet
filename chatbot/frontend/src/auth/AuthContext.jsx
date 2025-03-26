import { createContext, useState, useEffect, useContext } from "react";
import { authService } from "../auth/auth";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check if user is logged in on app load
    useEffect(() => {
        const loadUser = async () => {
            if (authService.isAuthenticated()) {
                try {
                    const userData = await authService.getCurrentUser();
                    setUser(userData);
                } catch (err) {
                    console.error("Failed to load user:", err);
                    authService.logout();
                }
            }
            setLoading(false);
        };

        loadUser();
    }, []);

    // Login function
    const login = async (credentials) => {
        setError(null);
        try {
            const data = await authService.login(credentials);
            setUser(data);
            return data;
        } catch (err) {
            setError(err);
            throw err;
        }
    };

    // Signup function
    const signup = async (userData) => {
        setError(null);
        try {
            const data = await authService.signup(userData);
            setUser(data);
            return data;
        } catch (err) {
            setError(err);
            throw err;
        }
    };

    // Logout function
    const logout = () => {
        authService.logout();
        setUser(null);
    };

    // Update password function
    const updatePassword = async (passwordData) => {
        setError(null);
        try {
            await authService.updatePassword(passwordData);
        } catch (err) {
            setError(err);
            throw err;
        }
    };

    // Update profile function
    const updateProfile = async (userData) => {
        setError(null);
        try {
            const updatedUser = await authService.updateProfile(userData);
            setUser((prevUser) => ({ ...prevUser, ...updatedUser }));
            return updatedUser;
        } catch (err) {
            setError(err);
            throw err;
        }
    };

    const value = {
        user,
        loading,
        error,
        login,
        signup,
        logout,
        updatePassword,
        updateProfile,
        isAuthenticated: authService.isAuthenticated(),
    };

    return (
        <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
