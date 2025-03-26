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
            <div className="bg-blue-800/95 w-full flex justify-between items-center h-14 pl-12 md:pl-8">
                <Link
                    to={"/"}
                    className="text-4xl font-bold text-white pl-4 p-2"
                >
                    GatorNet
                </Link>
                <div className="flex flex-col justify-center items-center p-2">
                    <AccountPopOver />
                    <p className="text-neutral-200 text-xs -mt-0.5">
                        {user?.name || ""}
                    </p>
                </div>
            </div>
            <div className="bg-orange-400 h-2"></div>
            <div className="flex flex-1 overflow-auto mb-20">{children}</div>
        </div>
    );
}

export default TopBar;
