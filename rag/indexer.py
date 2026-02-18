"""
Build FAISS index from vacancy chunks using sentence-transformers embeddings.
"""

import json
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Model: truly multilingual, excellent for Russian/Kazakh text
MODEL_NAME = "intfloat/multilingual-e5-small"
INDEX_DIR = "data/index"


def build_index(
    chunks: list[dict],
    model_name: str = MODEL_NAME,
    index_dir: str = INDEX_DIR,
    batch_size: int = 64,
) -> tuple:
    """
    Embed chunks and build FAISS index.

    Returns (index, model, chunks) for querying.
    Saves index + metadata to disk.
    """
    os.makedirs(index_dir, exist_ok=True)

    print(f"Loading model: {model_name}...")
    model = SentenceTransformer(model_name)

    # multilingual-e5 requires "passage: " prefix for documents
    is_e5 = "e5" in model_name.lower()
    texts = [("passage: " + c["text"] if is_e5 else c["text"]) for c in chunks]
    print(f"Encoding {len(texts)} chunks (batch_size={batch_size})...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    # FAISS index — Inner Product (cosine similarity since embeddings are normalized)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    print(f"FAISS index built: {index.ntotal} vectors, dim={dim}")

    # Save to disk
    faiss.write_index(index, os.path.join(index_dir, "vacancies.index"))
    with open(os.path.join(index_dir, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)
    with open(os.path.join(index_dir, "config.json"), "w") as f:
        json.dump({"model_name": model_name, "dim": dim, "n_chunks": len(chunks), "is_e5": is_e5}, f)

    print(f"Index saved to {index_dir}/")
    return index, model, chunks


def load_index(index_dir: str = INDEX_DIR) -> tuple:
    """Load FAISS index, model, and chunks from disk."""
    with open(os.path.join(index_dir, "config.json"), "r") as f:
        config = json.load(f)

    index = faiss.read_index(os.path.join(index_dir, "vacancies.index"))
    with open(os.path.join(index_dir, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    model = SentenceTransformer(config["model_name"])
    # Store e5 flag on model for search to use
    model._is_e5 = config.get("is_e5", False)

    print(f"Loaded index: {index.ntotal} vectors, model={config['model_name']}")
    return index, model, chunks


def search(
    query: str,
    index: faiss.Index,
    model: SentenceTransformer,
    chunks: list[dict],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    """
    Search FAISS index with a text query + optional metadata filters.

    Args:
        query: Natural language query
        index, model, chunks: From load_index()
        top_k: Number of results to return
        filters: Optional dict with keys: city, salary_min, experience
            - city: str — filter by area name (e.g. "Алматы")
            - salary_min: int — minimum salary_from or salary_to
            - experience: str — filter by experience field substring

    Returns top_k chunks with similarity scores, after applying filters.
    """
    # e5 models need "query: " prefix
    is_e5 = getattr(model, "_is_e5", False)
    q = f"query: {query}" if is_e5 else query

    # If filters are active, retrieve more candidates then filter
    fetch_k = top_k * 5 if filters else top_k

    query_vec = model.encode([q], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(query_vec, min(fetch_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        chunk = chunks[idx].copy()
        chunk["score"] = float(score)

        # Apply filters
        if filters:
            if not _passes_filters(chunk, filters):
                continue

        results.append(chunk)
        if len(results) >= top_k:
            break

    return results


def _passes_filters(chunk: dict, filters: dict) -> bool:
    """Check if a chunk passes all metadata filters."""
    # City filter — exact match (case-insensitive)
    city = filters.get("city")
    if city and city.lower().strip() != (chunk.get("area") or "").lower().strip():
        return False

    # Salary filter
    salary_min = filters.get("salary_min")
    if salary_min:
        sal_from = chunk.get("salary_from") or 0
        sal_to = chunk.get("salary_to") or 0
        best_salary = max(sal_from, sal_to)
        if best_salary == 0 or best_salary < salary_min:
            return False

    # Experience filter — check metadata field first, fallback to text
    exp = filters.get("experience")
    if exp:
        chunk_exp = chunk.get("experience") or ""
        chunk_text = chunk.get("text") or ""
        if exp.lower() not in chunk_exp.lower() and exp.lower() not in chunk_text.lower():
            return False

    return True
