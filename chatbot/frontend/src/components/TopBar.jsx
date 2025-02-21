import { UserCircle } from "@phosphor-icons/react";

export function TopBar({ children }) {
    return (
        <div className="flex flex-col w-screen min-h-screen">
            <div className="bg-blue-600 w-full flex justify-between items-center h-14">
                <h1 className="text-4xl font-bold text-white pl-4 p-2">
                    GatorNet
                </h1>
                <div className="pr-4">
                    <UserCircle
                        size={40}
                        weight="fill"
                        className="fill-orange-400"
                    />
                </div>
            </div>
            <div className="bg-orange-400 h-2"></div>
            <div className="flex-1 flex ">{children}</div>
        </div>
    );
}

export default TopBar;
