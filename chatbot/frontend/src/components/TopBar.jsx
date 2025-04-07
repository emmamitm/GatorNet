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
        <div className="w-full md:w-3xl flex self-center pt-4 px-4 md:pl-12 sticky top-0 z-10 bg-gradient-to-b from-white via-white to-white/0 dark:from-neutral-900 dark:via-neutral-900 dark:to-neutral-900/0">
            <div className="bg-gradient-to-br from-blue-900 to-blue-950 w-full flex justify-between items-center rounded-3xl h-14 p-4 pl-14 md:pl-4">
                <Link to={"/"} className="text-3xl font-bold text-white p-2">
                    Gator<span className="text-orange-400">Net</span>
                </Link>

                <AccountPopOver />
            </div>
        </div>
    );
}

export default TopBar;
