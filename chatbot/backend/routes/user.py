# user.py
from flask import Blueprint, request, jsonify
from database_tables import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from auth import token_required
import os, base64, time

user_routes = Blueprint("user_routes", __name__)


@user_routes.route("/api/user/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    avatar_base64 = None

    if hasattr(current_user, "avatar_path") and current_user.avatar_path:
        avatar_path = current_user.avatar_path

        if os.path.exists(avatar_path):
            try:
                with open(avatar_path, "rb") as image_file:
                    avatar_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as e:
                print(f"Error reading avatar: {e}")
                avatar_base64 = None
    return (
        jsonify(
            {
                "user_id": current_user.id,
                "email": current_user.email,
                "name": current_user.name,
                "avatar": avatar_base64,
            }
        ),
        200,
    )


@user_routes.route("/api/user/update-password", methods=["PUT"])
@token_required
def update_password(current_user):
    data = request.json
    if not data or "oldPassword" not in data:
        return jsonify({"error": "Missing old password"}), 400
    if "newPassword" not in data:
        return jsonify({"error": "Missing new password"}), 400
    if not check_password_hash(current_user.password_hash, data["oldPassword"]):
        return jsonify({"error": "Invalid old password"}), 400
    current_user.password_hash = generate_password_hash(data["newPassword"])
    db.session.commit()
    current_user.password = generate_password_hash(data["newPassword"])
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), 200


@user_routes.route("/api/user/update-avatar", methods=["POST"])
@token_required
def update_avatar(current_user):
    try:
        avatar_data = None

        # Check if request contains files
        if request.files and "avatar" in request.files:
            # Handle file upload
            avatar_file = request.files["avatar"]
            if avatar_file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            # Check file type
            allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
            file_ext = (
                avatar_file.filename.rsplit(".", 1)[1].lower()
                if "." in avatar_file.filename
                else ""
            )

            if file_ext not in allowed_extensions:
                return (
                    jsonify(
                        {
                            "error": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                        }
                    ),
                    400,
                )

            # Read the file data
            file_data = avatar_file.read()
            avatar_data = base64.b64encode(file_data).decode("utf-8")

        # Check if request contains JSON data
        elif request.content_type and "application/json" in request.content_type:
            # Handle JSON request
            if not request.json or "avatar" not in request.json:
                return jsonify({"error": "Avatar data is required"}), 400

            avatar_data = request.json["avatar"]

            # Handle base64 data with content type prefix
            if avatar_data.startswith("data:image/"):
                avatar_data = avatar_data.split(",")[1]
        else:
            return (
                jsonify(
                    {
                        "error": "Invalid request format. Send either a file upload or base64 image data"
                    }
                ),
                400,
            )

        # Ensure we have avatar data at this point
        if not avatar_data:
            return jsonify({"error": "No avatar data provided"}), 400

        try:
            # Decode base64 data
            decoded_avatar = base64.b64decode(avatar_data)
        except Exception as e:
            return jsonify({"error": f"Invalid base64 data: {str(e)}"}), 400

        # Create avatars directory if it doesn't exist
        avatar_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "static", "avatars")
        )
        os.makedirs(avatar_dir, exist_ok=True)

        # Generate a unique filename with timestamp to avoid caching issues
        timestamp = int(time.time())
        avatar_filename = f"user_{current_user.id}_avatar_{timestamp}.png"
        avatar_path = os.path.join(avatar_dir, avatar_filename)

        # Save avatar to file
        with open(avatar_path, "wb") as avatar_file:
            avatar_file.write(decoded_avatar)

        # Update user's avatar path in database
        # First, delete old avatar file if it exists (and is not default.png)
        if hasattr(current_user, "avatar_path") and current_user.avatar_path:
            old_avatar_path = current_user.avatar_path
            if os.path.exists(old_avatar_path) and not old_avatar_path.endswith(
                "default.png"
            ):
                try:
                    os.remove(old_avatar_path)
                except Exception as e:
                    print(f"Warning: Could not delete old avatar: {e}")

        # Update user's avatar path
        current_user.avatar_path = avatar_path

        # If you store the avatar data directly in the user model as well, update that too
        if hasattr(current_user, "avatar"):
            current_user.avatar = avatar_data

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Avatar updated successfully",
                    "avatar": avatar_data,  # Return the avatar data for immediate display
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error updating avatar: {e}")
        return jsonify({"error": f"Failed to update avatar: {str(e)}"}), 500


@user_routes.route("/api/user/update", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.json
    if "email" in data:
        current_user.email = data["email"]
    if "name" in data:
        current_user.name = data["name"]
    if "avatar" in data:
        try:
            avatar_data = base64.b64decode(data["avatar"].split(",")[1])
            with open(current_user.avatar_path, "wb") as avatar_file:
                avatar_file.write(avatar_data)
        except Exception as img_error:
            print(f"Failed to save avatar: {img_error}")
            return jsonify({"error": "Failed to save avatar"}), 500

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Profile updated successfully",
                "user": {
                    "user_id": current_user.id,
                    "email": current_user.email,
                    "name": current_user.name,
                },
            }
        ),
        200,
    )


@user_routes.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([user.email for user in users])


@user_routes.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404
