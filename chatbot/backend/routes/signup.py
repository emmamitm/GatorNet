from flask import Blueprint, request, jsonify, current_app as app
from database_tables import db, User
from werkzeug.security import generate_password_hash
import re
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

        # check if email and password are provided
        if "email" not in data or "password" not in data:
            return jsonify({"error": "Email and password are required"}), 400

        name = data.get("name")
        email = data["email"].lower().strip()
        password = data["password"]
        confirm_password = data.get("confirm_password")

        # validate email
        if not validate_email(email):
            return jsonify({"error": "Invalid email"}), 400

        # validate password
        if not validate_password(password):
            return (
                jsonify(
                    {
                        "error": "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit."
                    }
                ),
                400,
            )
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # check if email already registered
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email is already registered"}), 400

        # create new user
        new_user = User(
            email=email, password_hash=generate_password_hash(password), name=name
        )
        db.session.add(new_user)
        db.session.commit()

        # generate token
        token = generate_token(new_user.id)

        return (
            jsonify(
                {
                    "message": "User created successfully",
                    "token": token,
                    "user_id": new_user.id,
                    "email": new_user.email,
                    "name": new_user.name,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
