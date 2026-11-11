"""
documents/routes.py
---------------------
Document upload + the analysis pipeline.

Pipeline for each uploaded PDF (run synchronously per-file inside the
request for simplicity/demo purposes - see the note in README about
moving this to a background task queue for production use):

  1. Save the file (local disk or S3, see services/storage_service.py)
  2. Extract text per page with PyMuPDF, OCR fallback for scanned pages
     (services/ocr_service.py)
  3. Ask the LLM for a summary, 3-5 key insights, and a category
     (services/llm_service.py)
  4. Chunk the extracted text and embed + store it in the vector DB so
     it's ready for semantic search / QA (services/vector_service.py)
  5. Persist everything to the Document row.

Endpoints:
  POST   /api/documents/upload   (multipart, one or more "files")
  GET    /api/documents          -> list current user's documents
  GET    /api/documents/<id>     -> single document detail
  DELETE /api/documents/<id>     -> remove document + its vectors
"""

import logging

from flask import Blueprint, current_app, jsonify, request

from extensions import db
from models import Document
from services import llm_service, ocr_service, storage_service, vector_service
from utils.decorators import token_required

logger = logging.getLogger(__name__)

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]

def _process_document(document: Document) -> None:
    """Run the full OCR -> LLM -> vector-index pipeline for one document."""
    try:
        local_path = storage_service.get_local_path(document.storage_path)
        extraction = ocr_service.extract_text_from_pdf(local_path)
        full_text = extraction["full_text"]

        if not full_text.strip():
            raise ValueError(
                "No extractable text found in this PDF (even after OCR fallback)."
            )

        analysis = llm_service.analyze_document(full_text)

        chunks = ocr_service.chunk_text(full_text)
        vector_service.index_document_chunks(document.id, document.user_id, chunks)

        document.page_count = extraction["page_count"]
        document.summary = analysis["summary"]
        document.key_insights = analysis["key_insights"]
        document.category = analysis["category"]
        document.status = "ready"

    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        logger.exception("Document processing failed for %s", document.id)
        document.status = "failed"
        document.error_message = str(exc)

    finally:
        from datetime import datetime, timezone

        document.processed_at = datetime.now(timezone.utc)
        db.session.commit()

@documents_bp.route("/upload", methods=["POST"])
@token_required
def upload_documents(current_user):
    files = request.files.getlist("files") or request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files provided. Attach one or more PDFs under 'files'."}), 400

    created = []
    rejected = []

    for file_storage in files:
        if not file_storage or not file_storage.filename:
            continue
        if not _allowed_file(file_storage.filename):
            rejected.append({"filename": file_storage.filename, "reason": "Only PDF files are supported."})
            continue

        stored_name, storage_path = storage_service.save_file(file_storage)

        document = Document(
            user_id=current_user.id,
            filename=file_storage.filename,
            storage_path=storage_path,
            status="processing",
        )
        db.session.add(document)
        db.session.commit()

        # Synchronous processing keeps this demo self-contained (no extra
        # infra). For production, enqueue this onto Celery/RQ and let the
        # client poll GET /api/documents/<id> for status updates.
        _process_document(document)

        created.append(document.to_dict())

    if not created and rejected:
        return jsonify({"error": "No valid files were processed.", "rejected": rejected}), 400

    return jsonify({"documents": created, "rejected": rejected}), 201

@documents_bp.route("", methods=["GET"])
@token_required
def list_documents(current_user):
    docs = (
        Document.query.filter_by(user_id=current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return jsonify({"documents": [d.to_dict() for d in docs]}), 200

@documents_bp.route("/<document_id>", methods=["GET"])
@token_required
def get_document(current_user, document_id):
    doc = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    return jsonify({"document": doc.to_dict()}), 200

@documents_bp.route("/<document_id>", methods=["DELETE"])
@token_required
def delete_document(current_user, document_id):
    doc = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404

    vector_service.delete_document_vectors(doc.id)
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"message": "Document deleted."}), 200
