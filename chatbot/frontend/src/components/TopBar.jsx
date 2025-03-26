import React, { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import { Link } from "react-router";
import AccountPopOver from "./AccountPopOver";

export function TopBar({ children }) {
    const { user } = useAuth();

    // eslint-disable-next-line no-unused-vars
    const [avatarSrc, setAvatarSrc] = useState(null);

    useEffect(() => {
        if (user?.avatar) {
            const src = user.avatar.startsWith("data:image/")
                ? user.avatar
                : `data:image/png;base64,${user.avatar}`;
            setAvatarSrc(src);
        } else {
            setAvatarSrc(null);
        }
    }, [user]);

    return (
        <div className="flex flex-col w-screen h-screen">
            <div className="w-full sm:w-3/4 md:w-3/5 flex self-center p-4">
                <div
                    className="bg-gradient-to-br from-blue-800 to-blue-900
                 w-full flex justify-between items-center rounded-3xl h-14 p-4 pl-14 sm:pl-4"
                >
                    <Link
                        to={"/"}
                        className="text-3xl font-bold text-white p-2"
                    >
                        Gator<span className="text-orange-400">Net</span>
                    </Link>

                    <AccountPopOver />
                </div>
            </div>

            <div className="flex flex-1 overflow-auto mb-20">{children}</div>
        </div>
    );
}

export default TopBar;
