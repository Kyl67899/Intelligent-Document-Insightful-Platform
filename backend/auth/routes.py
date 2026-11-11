"""
auth/routes.py
---------------
Authentication endpoints: signup, login, logout, session refresh, and
"who am I". Passwords are hashed with bcrypt (never stored in plaintext).

Endpoints:
  POST /api/auth/signup   { email, password, name? } -> user + access_token
  POST /api/auth/login    { email, password }         -> user + access_token
  POST /api/auth/logout   (auth required)              -> clears session
  POST /api/auth/refresh  (session cookie required)    -> new access_token
  GET  /api/auth/me       (auth required)              -> current user
"""

import re

from flask import Blueprint, jsonify, request, session

from extensions import bcrypt, db
from models import User
from utils.decorators import encode_jwt, token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_credentials(email, password):
    if not email or not EMAIL_RE.match(email):
        return "A valid email address is required."
    if not password or len(password) < 8:
        return "Password must be at least 8 characters long."
    return None

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip() or None

    error = _validate_credentials(email, password)
    if error:
        return jsonify({"error": error}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(email=email, password_hash=password_hash, name=name)
    db.session.add(user)
    db.session.commit()

    # Establish server-side session + issue JWT, so the user is logged in
    # immediately after registering.
    session.permanent = True
    session["user_id"] = user.id

    token = encode_jwt(user.id)
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password."}), 401

    session.permanent = True
    session["user_id"] = user.id

    token = encode_jwt(user.id)
    return jsonify({"user": user.to_dict(), "access_token": token}), 200


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Issue a new short-lived access token as long as the server-side
    session (secure HttpOnly cookie) is still valid. This lets the
    frontend silently renew the JWT without asking the user to log in
    again every hour.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No active session."}), 401

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "User not found."}), 401

    token = encode_jwt(user.id)
    return jsonify({"access_token": token}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def me(current_user):
    return jsonify({"user": current_user.to_dict()}), 200
