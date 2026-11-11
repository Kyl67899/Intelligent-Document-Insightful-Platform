"""
utils/decorators.py
--------------------
Authentication helpers.

Auth model used in this app (hybrid, as requested):
  1. On login, the server issues a short-lived JWT access token. The
     frontend sends this as `Authorization: Bearer <token>` on every API
     call - this is what actually guards the API endpoints.
  2. The server ALSO establishes a server-side session (Flask-Session,
     backed by the DB) and sets a secure, HttpOnly session cookie. This
     lets us track/revoke logins server-side and is used by the
     `/auth/refresh` and `/auth/logout` endpoints, satisfying the
     "session based authentication" requirement alongside JWT.

`token_required` is the decorator every protected endpoint uses. It
verifies the JWT, loads the corresponding user, and also checks that a
valid server-side session still exists for that user (so a logout
immediately invalidates access even if a JWT hasn't expired yet).
"""

from functools import wraps

import jwt
from flask import current_app, jsonify, request, session

from models import User


def encode_jwt(user_id: str) -> str:
    """Create a signed, expiring JWT access token for a given user id."""
    import datetime

    payload = {
        "sub": user_id,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """Decode + verify a JWT, raising jwt exceptions on failure."""
    return jwt.decode(
        token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
    )


def token_required(f):
    """
    Decorator for protected routes. Expects `Authorization: Bearer <jwt>`.
    Injects the authenticated `current_user` as the first positional arg.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Access token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid access token"}), 401

        user_id = payload.get("sub")

        # Cross-check against the server-side session store so a logout
        # revokes access immediately, independent of JWT expiry.
        if session.get("user_id") != user_id:
            return jsonify({"error": "Session expired, please log in again"}), 401

        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 401

        return f(user, *args, **kwargs)

    return decorated
