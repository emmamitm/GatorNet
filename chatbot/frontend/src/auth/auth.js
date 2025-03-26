import api from "../axiosApi";

export const authService = {
    // login
    login: async (credentials) => {
        try {
            const response = await api.post("/login", credentials);
            const { token, user_id } = response.data;

            // Store token in localStorage
            localStorage.setItem("token", token);
            localStorage.setItem("userId", user_id);

            return response.data;
        } catch (error) {
            throw error.response?.data?.error || "Login failed";
        }
    },

    // signup
    signup: async (userData) => {
        try {
            const response = await api.post("/signup", userData);

            // If you want to auto-login after signup
            if (response.data.success) {
                return authService.login({
                    email: userData.email,
                    password: userData.password,
                });
            }

            return response.data;
        } catch (error) {
            throw error.response?.data?.error || "Signup failed: Unknown error";
        }
    },

    // logout
    logout: () => {
        localStorage.removeItem("token");
        localStorage.removeItem("userId");
    },

    // check if user is authenticated
    isAuthenticated: () => {
        return !!localStorage.getItem("token");
    },

    // get user profile
    getCurrentUser: async () => {
        try {
            const response = await api.get("/user/profile");
            return response.data;
        } catch (error) {
            throw error.response?.data?.error || "Failed to get profile";
        }
    },

    // update user password
    updatePassword: async (passwordData) => {
        try {
            const response = await api.put(
                "/user/update-password",
                passwordData,
                {
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );
            return response.data;
        } catch (error) {
            throw error.response?.data?.error || "Update failed";
        }
    },

    // update avatar
    updateAvatar: async (formData) => {
        try {
            const response = await api.post("/user/update-avatar", formData, {
                headers: {
                    // Don't set Content-Type explicitly - axios will set it correctly with boundary
                    // when sending FormData including the boundary parameter
                },
            });
            return response.data;
        } catch (error) {
            console.error("Avatar update error in service:", error);
            throw error.response?.data?.error || "Update failed";
        }
    },

    // update user profile
    updateProfile: async (userData) => {
        try {
            const response = await api.put("/user/update", userData);
            return response.data;
        } catch (error) {
            throw error.response?.data?.error || "Update failed";
        }
    },
};
