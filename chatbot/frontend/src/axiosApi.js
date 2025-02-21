import axios from "axios";

// create axios instance
const api = axios.create({
    baseURL: "http://localhost:5001/api",
    withCredentials: true,
});

// request interceptor to include token in headers
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// response interceptor to handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (
            error.response &&
            error.response.status === 401 &&
            !error.config.url.includes("/login")
        ) {
            // Unauthorized - clear token and redirect to login
            localStorage.removeItem("token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

export default api;
