"""
models.py
---------
SQLAlchemy ORM models.

User      - registered account, password stored as a bcrypt hash.
Document  - one uploaded PDF and the AI-generated analysis attached to it.
            The raw extracted text is NOT duplicated here in full (it lives
            in the vector DB as chunks); we keep a short preview + the
            structured analysis (summary / insights / category).
"""

import uuid
from datetime import datetime, timezone

from extensions import db

def _uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    documents = db.relationship(
        "Document", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    filename = db.Column(db.String(512), nullable=False)
    storage_path = db.Column(db.String(1024), nullable=False)
    page_count = db.Column(db.Integer, default=0)

    # Processing lifecycle: uploaded -> processing -> ready -> failed
    status = db.Column(db.String(32), default="uploaded", nullable=False)
    error_message = db.Column(db.Text, nullable=True)

    # AI-generated analysis
    summary = db.Column(db.Text, nullable=True)
    key_insights = db.Column(db.JSON, nullable=True)  # list[str]
    category = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "error_message": self.error_message,
            "page_count": self.page_count,
            "summary": self.summary,
            "key_insights": self.key_insights or [],
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
