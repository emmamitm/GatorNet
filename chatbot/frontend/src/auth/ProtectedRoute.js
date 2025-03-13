import { Navigate } from "react-router";
import { useAuth } from "../auth/AuthContext";

export const withAuth = (Component) => {
    const ProtectedComponent = (props) => {
        const { isAuthenticated, loading } = useAuth();

        if (loading) {
            return null; // or a loading spinner
        }

        if (!isAuthenticated) {
            return <Navigate to="/" replace />;
        }

        return <Component {...props} />;
    };

    return ProtectedComponent;
};
