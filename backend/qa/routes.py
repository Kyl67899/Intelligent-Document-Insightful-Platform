"""
qa/routes.py
------------
Semantic search + question-answering over a specific document.

POST /api/qa/ask
  body: { "document_id": "...", "question": "..." }
  1. Verify the document belongs to the requesting user and is ready.
  2. Run semantic search in the vector DB to retrieve the top-k most
     relevant text chunks for the question.
  3. Pass the question + retrieved context to the LLM to generate a
     grounded answer.
"""

import logging

from flask import Blueprint, jsonify, request

from models import Document
from services import llm_service, vector_service
from utils.decorators import token_required

logger = logging.getLogger(__name__)

qa_bp = Blueprint("qa", __name__, url_prefix="/api/qa")


@qa_bp.route("/ask", methods=["POST"])
@token_required
def ask(current_user):
    data = request.get_json(silent=True) or {}
    document_id = data.get("document_id")
    question = (data.get("question") or "").strip()

    if not document_id or not question:
        return jsonify({"error": "'document_id' and 'question' are required."}), 400

    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({"error": "Document not found."}), 404

    if document.status != "ready":
        return jsonify(
            {"error": f"Document is not ready for questions yet (status: {document.status})."}
        ), 409

    try:
        context_chunks = vector_service.semantic_search(document_id, question, top_k=5)
        answer = llm_service.answer_question(question, context_chunks)
    except Exception as exc:  # noqa: BLE001
        logger.exception("QA failed for document %s", document_id)
        return jsonify({"error": f"Failed to generate an answer: {exc}"}), 500

    return jsonify(
        {
            "question": question,
            "answer": answer,
            "sources_used": len(context_chunks),
        }
    ), 200
