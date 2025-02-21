from flask import Blueprint, request, jsonify
from database_tables import db, User
from werkzeug.security import generate_password_hash
from auth import token_required

user_routes = Blueprint("user_routes", __name__)


@user_routes.route("/api/user/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    return (
        jsonify(
            {
                "user_id": current_user.id,
                "email": current_user.email,
                "name": current_user.name,
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
        current_user.avatar = data["avatar"]
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


# TODO: remove if not needed?
@user_routes.route("/api/users", methods=["POST"])
def add_user():
    try:
        data = request.json
        new_user = User(
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            name=data["name"],
            avatar=data.get("avatar", "default.png"),
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"success": True, "user_id": new_user.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_routes.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({"email": user.email, "avatar": user.avatar})
    return jsonify({"error": "User not found"}), 404


@user_routes.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404


@user_routes.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.json
        user.email = data.get("email", user.email)
        user.password_hash = data.get("password", user.password_hash)
        user.name = data.get("name", user.name)
        user.avatar = data.get("avatar", user.avatar)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404
