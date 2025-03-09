#user.py
from flask import Blueprint, request, jsonify
from database_tables import db, User
from werkzeug.security import generate_password_hash
from auth import token_required
import os, base64

user_routes = Blueprint("user_routes", __name__)

@user_routes.route("/api/user/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    avatar_base64 = None

    if current_user.avatar:
        avatar_path = current_user.avatar

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
    if "password" in data:
        current_user.password_hash = generate_password_hash(data["password"])

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