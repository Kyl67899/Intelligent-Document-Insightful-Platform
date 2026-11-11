"""
app.py
------
Flask application factory + entrypoint.

Run locally with:
    python app.py
or with the Flask CLI:
    flask run
or in production behind gunicorn:
    gunicorn "app:create_app()"
"""

import logging
import os

from flask import Flask, jsonify

from config import config
from extensions import bcrypt, cors, db, sess

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    logging.basicConfig(level=logging.INFO)

    # --- Extensions ----------------------------------------------------
    db.init_app(app)
    bcrypt.init_app(app)

    # Session storage backed by the same SQL database (needs its table
    # created once - see `sess.app = app` init below).
    app.config["SESSION_SQLALCHEMY"] = db
    sess.init_app(app)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}},
        supports_credentials=True,
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Blueprints ------------------------------------------------------
    from auth.routes import auth_bp
    from documents.routes import documents_bp
    from qa.routes import qa_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(qa_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"service": "idip-backend", "status": "ok"}), 200

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify(
            {
                "error": "Method not allowed.",
                "allowed_methods": error.valid_methods or [],
            }
        ), 405

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "File too large."}), 413

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error."}), 500

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5050)),
        debug=app.config["DEBUG"],
    )

