import { UserCircle } from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";

export function TopBar({ children }) {
    const { logout } = useAuth();
    const { user } = useAuth();

    return (
        <div className="flex flex-col w-screen h-screen">
            <div className="bg-blue-800/95 w-full flex justify-between items-center h-14 pl-12 md:pl-8">
                <h1 className="text-4xl font-bold text-white pl-4 p-2">
                    GatorNet
                </h1>
                <div className="flex flex-col justify-center items-center p-2">
                    <button className="" onClick={logout}>
                        <UserCircle
                            size={32}
                            weight="fill"
                            className="fill-orange-400"
                        />
                    </button>
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
