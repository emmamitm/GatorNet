#auth.py
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app as app
from database_tables import User


def generate_token(user_id):
    payload = {"user_id": user_id, "exp": datetime.now() + timedelta(hours=24)}
    token = jwt.encode(payload, app.config["secret_key"], algorithm="HS256")
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, app.config["secret_key"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])

            if not current_user:
                return jsonify({"error": "User not found"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    return decorated
