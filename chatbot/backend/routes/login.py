# login.py
from flask import Blueprint, request, jsonify
from database_tables import User
from werkzeug.security import check_password_hash
import os, base64
from auth import generate_token

login_routes = Blueprint("login_routes", __name__)


@login_routes.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        user = User.query.filter_by(email=data["email"]).first()
        if user and check_password_hash(user.password_hash, data["password"]):
            # generate token
            token = generate_token(user.id)
            avatar_base64 = None

            if hasattr(user, "avatar_path") and user.avatar_path:
                avatar_path = user.avatar_path

                if os.path.exists(avatar_path):
                    try:
                        with open(avatar_path, "rb") as image_file:
                            avatar_base64 = base64.b64encode(image_file.read()).decode(
                                "utf-8"
                            )
                    except Exception as e:
                        print(f"Error reading avatar: {e}")
                        avatar_base64 = None
            return (
                jsonify(
                    {
                        "token": token,
                        "user_id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "avatar": avatar_base64,
                    }
                ),
                200,
            )

        else:
            return jsonify({"error": "Invalid email or password."}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 401
