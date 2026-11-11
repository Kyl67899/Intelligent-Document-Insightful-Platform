"""
extensions.py
-------------
Flask extension instances live here, separate from app.py, so that
blueprints/services can `from extensions import db` without triggering
circular imports with the app factory.
"""

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()
sess = Session()
