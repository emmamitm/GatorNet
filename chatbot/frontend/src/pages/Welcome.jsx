import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth } from "../auth/AuthContext";

function Welcome() {
    const navigate = useNavigate();
    const { isAuthenticated, loading } = useAuth();

    useEffect(() => {
        if (!loading && isAuthenticated) {
            navigate("/dashboard");
        }
    }, [loading, isAuthenticated, navigate]);

    return (
        <div className="flex flex-col justify-center h-svh max-w-3xl mx-auto p-4">
            <div className="flex flex-col p-12 bg-neutral-100/60 rounded-xl">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-neutral-700">
                    Welcome to GatorNet
                </h1>
                <h2 className="text-lg sm:text-2xl font-semibold bg-clip-text text-transparent bg-gradient-to-tr from-neutral-400 to-neutral-500">
                    Your AI assistant for all things UF
                </h2>
                <hr className="my-4 border-neutral-200" />
                <p className="text-lg text-neutral-600">
                    To get started, create an account or log in to your existing
                    account.
                </p>
                <div className="flex gap-4 mt-4">
                    <Link
                        to="/signup"
                        className="px-4 py-3 rounded-xl border-2 bg-gradient-to-br from-neutral-50 to-neutral-100 border-neutral-200 text-neutral-700 transition-colors duration-200 hover:from-green-100 hover:to-green-200 active:from-green-200 active:to-green-300"
                    >
                        Create Account
                    </Link>
                    <Link
                        to="/login"
                        className="px-4 py-3 rounded-xl border-2 bg-gradient-to-br from-neutral-50 to-neutral-100 border-neutral-200 text-neutral-700 transition-colors duration-200 hover:from-blue-100 hover:to-blue-200 active:from-blue-200 active:to-blue-300"
                    >
                        Log In
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default Welcome;
