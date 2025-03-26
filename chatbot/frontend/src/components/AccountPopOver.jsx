import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import { motion, AnimatePresence } from "motion/react";
import { ClipLoader } from "react-spinners";
import { UserCircle, X } from "@phosphor-icons/react";

function AccountPopOver() {
    const { user, updatePassword, logout, updateAvatar } = useAuth();
    const [showPopover, setShowPopover] = useState(false);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [showAvatarModal, setShowAvatarModal] = useState(false);
    const [passwordForm, setPasswordForm] = useState({
        oldPassword: "",
        newPassword: "",
        confirmPassword: "",
    });
    const [formErrors, setFormErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [avatarLoading, setAvatarLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [avatarSuccess, setAvatarSuccess] = useState(false);
    const [avatarSrc, setAvatarSrc] = useState(null);
    const [newAvatarFile, setNewAvatarFile] = useState(null);
    const [newAvatarPreview, setNewAvatarPreview] = useState(null);
    const popoverRef = useRef(null);
    const modalRef = useRef(null);
    const avatarModalRef = useRef(null);
    const fileInputRef = useRef(null);

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

    // Handle clicks outside the popover to close it
    useEffect(() => {
        function handleClickOutside(event) {
            if (
                popoverRef.current &&
                !popoverRef.current.contains(event.target)
            ) {
                setShowPopover(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [showPasswordModal, showAvatarModal]);

    // Close popover when modals open
    useEffect(() => {
        if (showPasswordModal || showAvatarModal) {
            setShowPopover(false);
        }
    }, [showPasswordModal, showAvatarModal]);

    const handlePasswordChange = (e) => {
        const { name, value } = e.target;
        setPasswordForm((prev) => ({
            ...prev,
            [name]: value,
        }));

        // Clear the specific error when user starts typing
        if (formErrors[name]) {
            setFormErrors((prev) => ({
                ...prev,
                [name]: "",
            }));
        }
    };

    const validatePasswordForm = () => {
        const errors = {};

        if (!passwordForm.oldPassword) {
            errors.oldPassword = "Current password is required";
        }

        if (!passwordForm.newPassword) {
            errors.newPassword = "New password is required";
        } else if (passwordForm.newPassword.length < 8) {
            errors.newPassword = "Password must be at least 8 characters";
        }

        if (!passwordForm.confirmPassword) {
            errors.confirmPassword = "Please confirm your new password";
        } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
            errors.confirmPassword = "Passwords do not match";
        }

        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmitPasswordChange = async (e) => {
        e.preventDefault();
        setSuccess(false);

        if (!validatePasswordForm()) {
            return;
        }

        setLoading(true);

        try {
            await updatePassword(passwordForm);

            // Show success message
            setSuccess(true);

            // Reset form
            setPasswordForm({
                oldPassword: "",
                newPassword: "",
                confirmPassword: "",
            });

            // Close modal after a delay
            setTimeout(() => {
                setShowPasswordModal(false);
                setSuccess(false);
            }, 2000);
        } catch (error) {
            // Check for specific error messages from the backend
            if (error.response && error.response.data) {
                if (error.response.data.error === "Invalid old password") {
                    setFormErrors((prev) => ({
                        ...prev,
                        oldPassword: "Current password is incorrect",
                    }));
                } else {
                    setFormErrors((prev) => ({
                        ...prev,
                        general:
                            "Failed to update password: " +
                            error.response.data.error,
                    }));
                }
            } else {
                // Handle network or unexpected errors
                setFormErrors((prev) => ({
                    ...prev,
                    general:
                        "An unexpected error occurred. Please try again later.",
                }));
                console.error("Password change error:", error);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAvatarChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        ];
        if (!validTypes.includes(file.type)) {
            setFormErrors({
                avatar: "Please select a valid image file (JPEG, PNG, GIF, WEBP)",
            });
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            setFormErrors({
                avatar: "Image size should be less than 5MB",
            });
            return;
        }

        setNewAvatarFile(file);

        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
            setNewAvatarPreview(reader.result);
        };
        reader.readAsDataURL(file);

        // Clear any previous errors
        if (formErrors.avatar) {
            setFormErrors((prev) => ({ ...prev, avatar: "" }));
        }
    };

    const handleAvatarSubmit = async (e) => {
        e.preventDefault();

        if (!newAvatarFile) {
            setFormErrors({
                avatar: "Please select an image",
            });
            return;
        }

        setAvatarLoading(true);
        setAvatarSuccess(false);

        try {
            // Call the updateProfile function from AuthContext
            var avatarForm = new FormData();
            avatarForm.append("avatar", newAvatarFile);
            await updateAvatar(avatarForm);

            // Show success message
            setAvatarSuccess(true);

            // Reset form
            setNewAvatarFile(null);
            setNewAvatarPreview(null);

            // Close modal after a delay
            setTimeout(() => {
                setShowAvatarModal(false);
                setAvatarSuccess(false);
            }, 2000);
        } catch (error) {
            console.error("Avatar update error:", error);
            setFormErrors({
                avatar: "Failed to update avatar. Please try again.",
            });
        } finally {
            setAvatarLoading(false);
        }
    };

    const handleSignOut = () => {
        setShowPopover(false);
        logout();
    };

    const openFileSelector = () => {
        fileInputRef.current.click();
    };

    const clearSelectedAvatar = () => {
        setNewAvatarFile(null);
        setNewAvatarPreview(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    return (
        <div className="relative">
            <button
                onClick={() => setShowPopover(!showPopover)}
                className="focus:outline-none"
            >
                {avatarSrc ? (
                    <img
                        src={avatarSrc}
                        alt="Avatar"
                        className="w-8 h-8 object-cover rounded-full"
                    />
                ) : (
                    <UserCircle
                        size={32}
                        weight="fill"
                        className="fill-orange-400"
                    />
                )}
            </button>

            {/* Account Popover */}
            <AnimatePresence>
                {showPopover && (
                    <motion.div
                        ref={popoverRef}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute right-0 top-10 w-64 bg-white rounded-xl shadow-lg border border-neutral-200 overflow-hidden z-50"
                    >
                        <div className="p-4 bg-blue-50 border-b border-blue-100">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full overflow-hidden">
                                    {avatarSrc ? (
                                        <img
                                            src={avatarSrc}
                                            alt="User avatar"
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <div className="w-full h-full bg-blue-500 flex items-center justify-center text-white text-xl font-medium">
                                            {user?.name
                                                ? user.name
                                                      .charAt(0)
                                                      .toUpperCase()
                                                : "U"}
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <h3 className="font-medium text-neutral-800">
                                        {user?.name || "User"}
                                    </h3>
                                    <p className="text-sm text-neutral-500">
                                        {user?.email || "user@example.com"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="p-2">
                            <button
                                onClick={() => setShowPasswordModal(true)}
                                className="w-full text-left px-3 py-2 rounded-lg hover:bg-neutral-100 text-neutral-700 transition-colors"
                            >
                                Change Password
                            </button>

                            <button
                                onClick={() => setShowAvatarModal(true)}
                                className="w-full text-left px-3 py-2 rounded-lg hover:bg-neutral-100 text-neutral-700 transition-colors"
                            >
                                Change Profile Picture
                            </button>
                        </div>

                        <div className="p-2 border-t border-neutral-200">
                            <button
                                onClick={handleSignOut}
                                className="w-full text-left px-3 py-2 rounded-lg hover:bg-red-50 text-red-600 transition-colors"
                            >
                                Sign Out
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Change Password Modal */}
            <AnimatePresence>
                {showPasswordModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
                    >
                        <motion.div
                            ref={modalRef}
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="w-full max-w-md bg-white rounded-xl shadow-xl p-6"
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-neutral-800">
                                    Change Password
                                </h2>
                                <button
                                    onClick={() => setShowPasswordModal(false)}
                                    className="text-neutral-400 hover:text-neutral-600"
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="24"
                                        height="24"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <line
                                            x1="18"
                                            y1="6"
                                            x2="6"
                                            y2="18"
                                        ></line>
                                        <line
                                            x1="6"
                                            y1="6"
                                            x2="18"
                                            y2="18"
                                        ></line>
                                    </svg>
                                </button>
                            </div>

                            <form
                                onSubmit={handleSubmitPasswordChange}
                                className="space-y-4"
                            >
                                <div>
                                    <label className="block text-sm font-medium text-neutral-700 mb-1">
                                        Current Password
                                    </label>
                                    <input
                                        type="password"
                                        name="oldPassword"
                                        className={`w-full py-2 px-3 rounded-lg border ${
                                            formErrors.oldPassword
                                                ? "border-red-300"
                                                : "border-neutral-300"
                                        } focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors`}
                                        value={passwordForm.oldPassword}
                                        onChange={handlePasswordChange}
                                    />
                                    {formErrors.oldPassword && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {formErrors.oldPassword}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-700 mb-1">
                                        New Password
                                    </label>
                                    <input
                                        type="password"
                                        name="newPassword"
                                        className={`w-full py-2 px-3 rounded-lg border ${
                                            formErrors.newPassword
                                                ? "border-red-300"
                                                : "border-neutral-300"
                                        } focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors`}
                                        value={passwordForm.newPassword}
                                        onChange={handlePasswordChange}
                                    />
                                    {formErrors.newPassword && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {formErrors.newPassword}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-700 mb-1">
                                        Confirm New Password
                                    </label>
                                    <input
                                        type="password"
                                        name="confirmPassword"
                                        className={`w-full py-2 px-3 rounded-lg border ${
                                            formErrors.confirmPassword
                                                ? "border-red-300"
                                                : "border-neutral-300"
                                        } focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-colors`}
                                        value={passwordForm.confirmPassword}
                                        onChange={handlePasswordChange}
                                    />
                                    {formErrors.confirmPassword && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {formErrors.confirmPassword}
                                        </p>
                                    )}
                                </div>

                                {success && (
                                    <div className="p-2 bg-green-50 text-green-700 rounded-lg text-sm">
                                        Password changed successfully!
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-2">
                                    <button
                                        type="button"
                                        onClick={() =>
                                            setShowPasswordModal(false)
                                        }
                                        className="px-4 py-2 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center justify-center min-w-[80px]"
                                        disabled={loading}
                                    >
                                        {loading ? (
                                            <ClipLoader
                                                color="white"
                                                size={20}
                                            />
                                        ) : (
                                            "Save"
                                        )}
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Avatar Change Modal */}
            <AnimatePresence>
                {showAvatarModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
                    >
                        <motion.div
                            ref={avatarModalRef}
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="w-full max-w-md bg-white rounded-xl shadow-xl p-6"
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-neutral-800">
                                    Change Profile Picture
                                </h2>
                                <button
                                    onClick={() => setShowAvatarModal(false)}
                                    className="text-neutral-400 hover:text-neutral-600"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <form
                                onSubmit={handleAvatarSubmit}
                                className="space-y-4"
                            >
                                <div className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-neutral-300 rounded-lg bg-neutral-50">
                                    {newAvatarPreview ? (
                                        <div className="relative mb-4">
                                            <img
                                                src={newAvatarPreview}
                                                alt="New avatar preview"
                                                className="w-24 h-24 rounded-full object-cover"
                                            />
                                            <button
                                                type="button"
                                                onClick={clearSelectedAvatar}
                                                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                                            >
                                                <X size={16} />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                                            <UserCircle
                                                size={64}
                                                className="text-blue-500"
                                            />
                                        </div>
                                    )}

                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleAvatarChange}
                                        accept="image/jpeg,image/png,image/gif,image/webp"
                                        className="hidden"
                                    />

                                    <button
                                        type="button"
                                        onClick={openFileSelector}
                                        className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                                    >
                                        {newAvatarPreview
                                            ? "Choose Different Image"
                                            : "Select Image"}
                                    </button>
                                </div>

                                {formErrors.avatar && (
                                    <p className="text-sm text-red-600">
                                        {formErrors.avatar}
                                    </p>
                                )}

                                {avatarSuccess && (
                                    <div className="p-2 bg-green-50 text-green-700 rounded-lg text-sm">
                                        Profile picture updated successfully!
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-2">
                                    <button
                                        type="button"
                                        onClick={() =>
                                            setShowAvatarModal(false)
                                        }
                                        className="px-4 py-2 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center justify-center min-w-[80px]"
                                        disabled={
                                            !newAvatarFile || avatarLoading
                                        }
                                    >
                                        {avatarLoading ? (
                                            <ClipLoader
                                                color="white"
                                                size={20}
                                            />
                                        ) : (
                                            "Save"
                                        )}
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default AccountPopOver;
