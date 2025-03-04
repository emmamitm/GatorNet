from flask import Blueprint, request, jsonify
from database_tables import User
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import jwt
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

            return (
                jsonify(
                    {
                        "token": token,
                        "user_id": user.id,
                        "email": user.email,
                        "name": user.name,
                    }
                ),
                200,
            )

        else:
            return jsonify({"error": "Invalid email or password."}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 401
