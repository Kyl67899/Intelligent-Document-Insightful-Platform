"""
services/vector_service.py
----------------------------
Vector database integration using Chroma (persisted locally to disk).

Each document's text chunks are embedded with a sentence-transformers
model and stored in a single Chroma collection ("documents"), tagged with
metadata (`document_id`, `user_id`, `page_number`-ish chunk index) so we
can both:
  - scope semantic search to one document/user (for the QA endpoint), and
  - delete all vectors for a document when it's removed.
"""

import logging
import os
import threading

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client = None
_collection = None


def _get_collection():
    """Lazily initialize the Chroma client + collection (singleton)."""
    global _client, _collection
    if _collection is not None:
        return _collection

    with _lock:
        if _collection is None:
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
            os.makedirs(persist_dir, exist_ok=True)

            _client = chromadb.PersistentClient(path=persist_dir)

            embed_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embed_model
            )

            _collection = _client.get_or_create_collection(
                name="documents",
                embedding_function=embed_fn,
                metadata={"hnsw:space": "cosine"},
            )
    return _collection


def index_document_chunks(document_id: str, user_id: str, chunks: list[str]) -> int:
    """Embed and store text chunks for a document. Returns number stored."""
    if not chunks:
        return 0

    collection = _get_collection()
    ids = [f"{document_id}::{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "user_id": user_id, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def semantic_search(
    document_id: str, query: str, top_k: int = 5
) -> list[str]:
    """
    Retrieve the top_k most semantically relevant chunks for `query`,
    scoped to a single document.
    """
    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"document_id": document_id},
    )
    documents = results.get("documents") or [[]]
    return documents[0]


def delete_document_vectors(document_id: str) -> None:
    """Remove all stored chunks for a document (e.g. when it's deleted)."""
    collection = _get_collection()
    collection.delete(where={"document_id": document_id})
