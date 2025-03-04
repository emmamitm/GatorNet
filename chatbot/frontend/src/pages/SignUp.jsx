import { React, useState } from "react";
import { Link } from "react-router";
import { useAuth } from "../auth/AuthContext";
import { ClipLoader } from "react-spinners";

function SignUp() {
    const { signup } = useAuth();
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [userData, setUserData] = useState({
        name: "",
        email: "",
        password: "",
        confirm_password: "",
    });
    const [success, setSuccess] = useState(false);

    const handleChange = (e) => {
        setUserData({ ...userData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            await signup(userData);
            setSuccess(true);
        } catch (err) {
            setError(err.toString());
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col max-w-sm h-svh justify-center mx-auto gap-4 p-4">
            {error && (
                <div className="py-2 px-4 bg-red-100 text-red-800 rounded-lg">
                    {error}
                </div>
            )}
            {success && (
                <div className="py-2 px-4 bg-green-100 text-green-800 rounded-lg">
                    Account created successfully!{" "}
                    <Link className="underline" to="/login">
                        Log in
                    </Link>
                </div>
            )}
            <div className="flex flex-col gap-2 p-6 sm:p-8 md:p-12 bg-neutral-100/60 rounded-xl">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">
                    Sign Up
                </h1>
                <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
                    <label className="flex flex-col gap-2">
                        <span>Name</span>
                        <input
                            type="text"
                            placeholder="Name"
                            className="border-2 border-neutral-200 rounded-lg p-2"
                            name="name"
                            value={userData.name}
                            onChange={handleChange}
                            required
                        />
                    </label>
                    <label className="flex flex-col gap-2">
                        <span>Email</span>
                        <input
                            type="email"
                            placeholder="Email"
                            className="border-2 border-neutral-200 rounded-lg p-2"
                            name="email"
                            value={userData.email}
                            onChange={handleChange}
                            required
                        />
                    </label>
                    <label className="flex flex-col gap-2">
                        <span>Password</span>
                        <input
                            type="password"
                            placeholder="Password"
                            className="border-2 border-neutral-200 rounded-lg p-2"
                            name="password"
                            value={userData.password}
                            onChange={handleChange}
                            required
                        />
                    </label>
                    <label className="flex flex-col gap-2">
                        <span>Confirm Password</span>
                        <input
                            type="password"
                            placeholder="Confirm Password"
                            className="border-2 border-neutral-200 rounded-lg p-2"
                            name="confirm_password"
                            value={userData.confirm_password}
                            onChange={handleChange}
                            required
                        />
                    </label>
                    <button
                        type="submit"
                        className="flex justify-center bg-gradient-to-br from-blue-400 to-blue-500 text-white rounded-lg p-2 transition-colors duration-200 hover:from-blue-500 hover:to-blue-600 active:from-blue-600 active:to-blue-700"
                    >
                        {loading ? (
                            <ClipLoader color="white" size={22} />
                        ) : (
                            "Sign Up"
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default SignUp;
