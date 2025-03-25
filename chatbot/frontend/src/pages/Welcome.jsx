import React, { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router";
import { useAuth } from "../auth/AuthContext";
import { motion } from "motion/react";
import { ClipLoader } from "react-spinners";
import "../css/custom.css";

function Welcome() {
    const navigate = useNavigate();
    const location = useLocation();
    const { isAuthenticated, loading: authLoading, login } = useAuth();

    // Form states
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    // Validation states
    const [emailError, setEmailError] = useState("");
    const [passwordTouched, setPasswordTouched] = useState(false);

    // Login states
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            navigate("/dashboard");
        }

        // Check for email parameter in URL
        const params = new URLSearchParams(location.search);
        const emailParam = params.get("em");

        if (emailParam) {
            // Decode the email parameter (in case it's URL encoded)
            setEmail(decodeURIComponent(emailParam));
        }
    }, [authLoading, isAuthenticated, navigate, location]);

    const validateEmail = () => {
        const emailInput = document.querySelector('input[type="email"]');
        if (!emailInput.checkValidity()) {
            setEmailError("Please enter a valid email address");
            return false;
        }
        setEmailError("");
        return true;
    };

    const handleEmailClick = () => {
        if (validateEmail()) {
            setShowPassword(true);
        }
    };

    const handlePasswordChange = (e) => {
        setPassword(e.target.value);
        if (!passwordTouched) {
            setPasswordTouched(true);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validate email again
        if (!validateEmail()) {
            return;
        }

        // Validate password
        if (!password) {
            return;
        }

        setLoading(true);
        setError("");

        try {
            await login({ email, password });
            navigate("/dashboard");
        } catch (err) {
            setError(err.toString());
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center gap-8 p-4 py-8 max-w-4xl mx-auto">
            {/* Welcome Card */}
            <div className="relative overflow-hidden w-full px-8 py-10 flex flex-col bg-neutral-100/60 rounded-2xl outline-2 outline-neutral-200">
                <h1 className="text-4xl font-bold text-neutral-700 mb-2">
                    Welcome to GatorNet 🐊
                </h1>

                <h2 className="text-xl font-semibold text-neutral-500 mb-4">
                    Your AI assistant for all things UF
                </h2>

                <hr className="mb-6 border-neutral-200" />

                <div className="flex flex-col justify-center">
                    <p className="text-lg text-neutral-600 mb-4">
                        To get started, create an account or log in to your
                        existing account.
                    </p>

                    <motion.form
                        className="flex flex-col w-full sm:w-96 gap-4"
                        onSubmit={handleSubmit}
                        animate={{ height: "auto" }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                        <div className="flex flex-col gap-1">
                            <input
                                type="email"
                                className="py-2 px-4 rounded-lg border-2 border-neutral-200 placeholder-neutral-400 text-neutral-700 focus:outline-none focus:border-blue-200 focus:ring-2 focus:ring-blue-200 transition-colors duration-200"
                                placeholder="Enter your email address"
                                value={email}
                                onChange={(e) => {
                                    setEmail(e.target.value);
                                    if (emailError) validateEmail();
                                }}
                                required
                            />
                            {emailError && (
                                <p className="text-sm text-red-600 px-1">
                                    {emailError}
                                </p>
                            )}
                        </div>

                        {showPassword && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                transition={{ duration: 0.3 }}
                                className="flex flex-col gap-1"
                            >
                                <input
                                    type="password"
                                    className="w-full py-2 px-4 rounded-lg border-2 border-neutral-200 placeholder-neutral-400 text-neutral-700 focus:outline-none focus:border-blue-200 focus:ring-2 focus:ring-blue-200 transition-colors duration-200"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={handlePasswordChange}
                                    onBlur={() => setPasswordTouched(true)}
                                    required
                                    autoFocus
                                />
                                {passwordTouched && !password && (
                                    <p className="text-sm text-red-600 px-1">
                                        Please enter your password
                                    </p>
                                )}
                            </motion.div>
                        )}

                        {error && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="py-2 px-4 bg-red-100 text-red-800 rounded-lg text-sm"
                            >
                                {error}
                            </motion.div>
                        )}

                        <div className="flex flex-col sm:flex-row items-center gap-2">
                            <button
                                type={showPassword ? "submit" : "button"}
                                onClick={
                                    showPassword ? undefined : handleEmailClick
                                }
                                className="w-full sm:w-fit py-2 px-6 rounded-lg sm:rounded-xl font-medium text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 transition-colors duration-200 flex items-center justify-center"
                                disabled={loading}
                            >
                                {loading ? (
                                    <ClipLoader color="white" size={20} />
                                ) : showPassword ? (
                                    "Log In"
                                ) : (
                                    "Continue"
                                )}
                            </button>

                            {!showPassword && (
                                <Link
                                    to="/signup"
                                    className="w-full sm:w-fit py-2 px-6 rounded-lg sm:rounded-xl font-medium text-white bg-orange-500 hover:bg-orange-600 active:bg-orange-700 transition-colors duration-200 text-center"
                                >
                                    Create Account
                                </Link>
                            )}
                        </div>
                    </motion.form>
                </div>
            </div>

            {/* About Card */}
            <div className="w-full px-8 py-10 bg-neutral-100/60 rounded-2xl outline-2 outline-neutral-200">
                <h2 className="text-3xl font-bold text-neutral-700 mb-6">
                    About GatorNet
                </h2>

                <div className="grid md:grid-cols-2 gap-8">
                    <div>
                        <p className="text-neutral-600 mb-4">
                            GatorNet is an AI-powered assistant designed
                            exclusively for the University of Florida community.
                            Built to help students, faculty, and staff navigate
                            campus life with ease.
                        </p>
                        <p className="text-neutral-600 mb-6">
                            Whether you need information about classes, campus
                            resources, events, or academic policies, GatorNet
                            provides instant, accurate answers tailored to UF.
                        </p>

                        <div>
                            <h3 className="text-xl font-semibold text-neutral-700 mb-3">
                                Key Features
                            </h3>
                            <ul className="space-y-2">
                                <li className="flex items-start">
                                    <span className="text-blue-500 mr-2">
                                        ✓
                                    </span>
                                    <span className="text-neutral-600">
                                        24/7 instant answers to your UF
                                        questions
                                    </span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-500 mr-2">
                                        ✓
                                    </span>
                                    <span className="text-neutral-600">
                                        Personalized academic guidance and
                                        resources
                                    </span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-500 mr-2">
                                        ✓
                                    </span>
                                    <span className="text-neutral-600">
                                        Up-to-date campus event information
                                    </span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-500 mr-2">
                                        ✓
                                    </span>
                                    <span className="text-neutral-600">
                                        Navigation assistance for campus
                                        facilities
                                    </span>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <div className="flex flex-col justify-center space-y-6">
                        <div className="bg-orange-50 p-6 rounded-xl border border-orange-100">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="text-3xl">📚</span>
                                <h3 className="text-lg font-semibold text-orange-700">
                                    Smart Learning Support
                                </h3>
                            </div>
                            <p className="text-neutral-600">
                                Get help with course selection, study resources,
                                and academic planning tailored to your program.
                            </p>
                        </div>

                        <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="text-3xl">🗓️</span>
                                <h3 className="text-lg font-semibold text-blue-700">
                                    Campus Life Navigator
                                </h3>
                            </div>
                            <p className="text-neutral-600">
                                Discover events, clubs, dining options, and
                                recreational activities to enhance your UF
                                experience.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="w-full flex flex-col items-center gap-2">
                <hr className="w-full border-neutral-200" />
                <p className="text-center text-neutral-500">
                    Developed by a small group of UF students.
                </p>
            </div>
        </div>
    );
}

export default Welcome;
