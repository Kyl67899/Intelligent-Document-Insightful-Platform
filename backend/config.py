"""
config.py
---------
Centralized application configuration, loaded from environment variables
(see .env.example). Keeping all config in one place makes it easy to see
every tunable knob and avoids scattering os.getenv() calls across the app.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

from dotenv import load_dotenv

# Load the backend's .env regardless of the shell's current directory.
load_dotenv(os.path.join(BASE_DIR, ".env"))

def _bool(env_val, default=False):
    """Parse a truthy/falsy environment string into a real bool."""
    if env_val is None:
        return default
    return str(env_val).lower() in ("1", "true", "yes", "on")

class Config:
    # --- Core Flask ---------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = _bool(os.getenv("DEBUG"), True)

    # --- Database --------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'idip.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth / JWT -----------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7))
    )

    # --- Session (server-side session backing the refresh-token /
    # "remember this browser" flow described in the spec) -----------
    SESSION_TYPE = "sqlalchemy"
    SESSION_SQLALCHEMY_TABLE = "sessions"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.getenv("SESSION_COOKIE_SECURE"), False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # --- CORS -----------------------------------------------------
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

    # --- File storage ------------------------------------------------
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 25)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}

    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # --- LLM --------------------------------------------------------
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")
    LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    # --- Vector DB ----------------------------------------------------
    CHROMA_PERSIST_DIR = os.path.join(
        BASE_DIR, os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
    )
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

config = Config()
