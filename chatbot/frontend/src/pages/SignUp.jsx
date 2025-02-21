import { React } from "react";

function SignUp() {
    return (
        <div className="flex flex-col max-w-sm h-screen justify-center mx-auto gap-4 p-4">
            <h1 className="text-4xl font-bold">Sign Up</h1>
            <form className="flex flex-col gap-4">
                <label className="flex flex-col gap-2">
                    <span>Email</span>
                    <input
                        type="email"
                        placeholder="Email"
                        className="border-2 border-neutral-200 rounded-lg p-2"
                    />
                </label>
                <label className="flex flex-col gap-2">
                    <span>Password</span>
                    <input
                        type="password"
                        placeholder="Password"
                        className="border-2 border-neutral-200 rounded-lg p-2"
                    />
                </label>
                <label className="flex flex-col gap-2">
                    <span>Confirm Password</span>
                    <input
                        type="password"
                        placeholder="Confirm Password"
                        className="border-2 border-neutral-200 rounded-lg p-2"
                    />
                </label>
                <button
                    type="submit"
                    className="bg-gradient-to-br from-blue-400 to-blue-500 text-white rounded-lg p-2 cursor-pointer transition-colors duration-200 hover:from-blue-500 hover:to-blue-600 active:from-blue-600 active:to-blue-700"
                >
                    Sign Up
                </button>
            </form>
        </div>
    );
}

export default SignUp;
