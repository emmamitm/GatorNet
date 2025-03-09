from flask import Blueprint, request, jsonify
from database_tables import db, User, AVATAR_DIR
from werkzeug.security import generate_password_hash
import re
import base64
import os
from auth import generate_token

signup_routes = Blueprint("signup_routes", __name__)

def validate_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


def validate_password(password):
    if len(password) < 8:  # at least 8 characters
        return False
    if not re.search(r"[A-Z]", password):  # at least one uppercase letter
        return False
    if not re.search(r"[a-z]", password):  # at least one lowercase letter
        return False
    if not re.search(r"\d", password):  # at least one digit
        return False
    return True


@signup_routes.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.json

        if "email" not in data or "password" not in data:
            return jsonify({"error": "Email and password are required"}), 400

        name = data.get("name")
        email = data["email"].lower().strip()
        password = data["password"]
        confirm_password = data.get("confirm_password")
        avatar_base64 = data.get("avatar")  

        if not validate_email(email):
            return jsonify({"error": "Invalid email"}), 400

        if not validate_password(password):
            return jsonify({
                "error": "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit."
            }), 400

        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email is already registered"}), 400

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            avatar_path=os.path.join(AVATAR_DIR, "default.png"),  
        )

        db.session.add(new_user)
        db.session.commit()

        if avatar_base64:
            try:
                avatar_data = base64.b64decode(avatar_base64.split(",")[1])
                avatar_path = os.path.join(AVATAR_DIR, f"{new_user.id}.png")
                with open(avatar_path, "wb") as avatar_file:
                    avatar_file.write(avatar_data)

                # Update user avatar path in DB
                new_user.avatar_path = avatar_path
                db.session.commit()
            except Exception as img_error:
                print(f"Failed to save avatar: {img_error}")
                return jsonify({"error": "Failed to save avatar"}), 500



        token = generate_token(new_user.id)

        return jsonify({
            "message": "User created successfully",
            "token": token,
            "user_id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "avatar_path": f"/{new_user.avatar_path}"
        }), 201

    except Exception as e:
        print(f"Error creating user: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
