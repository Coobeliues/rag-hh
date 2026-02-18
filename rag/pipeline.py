"""
RAG pipeline: FAISS search + LLM answer generation.

Supports both OpenAI API and local Ollama models.
"""

import os
import requests
from rag.indexer import search

# --- Prompt templates ---

SYSTEM_PROMPT = """Ты — умный ассистент по вакансиям с hh.kz.
Отвечай на вопросы пользователя ТОЛЬКО на основе предоставленных вакансий.
Если в данных нет ответа — честно скажи об этом.
Отвечай структурированно, используй списки и таблицы где уместно.
Язык ответа: русский."""

RAG_PROMPT_TEMPLATE = """Вот релевантные вакансии из базы hh.kz:

{context}

---
Вопрос пользователя: {question}

Ответь на вопрос, опираясь ТОЛЬКО на вакансии выше. Приводи конкретные примеры (названия компаний, зарплаты, навыки)."""


def format_context(results: list[dict], max_chunks: int = 5) -> str:
    """Format search results into context string for LLM."""
    parts = []
    seen_ids = set()

    for r in results[:max_chunks]:
        vid = r.get("vacancy_id")
        if vid in seen_ids:
            continue
        seen_ids.add(vid)
        parts.append(f"[Вакансия: {r.get('vacancy_name')} | {r.get('employer')} | {r.get('area')}]\n{r['text']}\n")

    return "\n---\n".join(parts)


def answer_with_ollama(
    question: str,
    context: str,
    model: str = "qwen2.5:3b",
    base_url: str = "http://localhost:11434",
) -> str:
    """Generate answer using local Ollama model."""
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    resp = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["message"]["content"]
    except (KeyError, TypeError):
        raise ValueError(f"Unexpected Ollama response format: {str(data)[:200]}")


def answer_with_openai(
    question: str,
    context: str,
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
) -> str:
    """Generate answer using OpenAI API."""
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, TypeError, IndexError):
        raise ValueError(f"Unexpected OpenAI response format: {str(data)[:200]}")


def rag_query(
    question: str,
    index,
    embed_model,
    chunks: list[dict],
    llm_backend: str = "ollama",
    llm_model: str = "qwen2.5:3b",
    top_k: int = 10,
    **kwargs,
) -> dict:
    """
    Full RAG pipeline: search + generate answer.

    Args:
        question: User's question in natural language
        index: FAISS index
        embed_model: SentenceTransformer model
        chunks: List of chunk dicts
        llm_backend: "ollama" or "openai"
        llm_model: Model name for the chosen backend
        top_k: Number of chunks to retrieve

    Returns:
        dict with 'answer', 'sources', 'context'
    """
    # 1. Retrieve relevant chunks
    results = search(question, index, embed_model, chunks, top_k=top_k)

    # 2. Format context
    context = format_context(results)

    # 3. Generate answer
    if llm_backend == "ollama":
        answer = answer_with_ollama(question, context, model=llm_model, **kwargs)
    elif llm_backend == "openai":
        answer = answer_with_openai(question, context, model=llm_model, **kwargs)
    else:
        # Fallback: just return search results without LLM
        answer = f"(LLM not configured — showing raw search results)\n\n{context}"

    # 4. Extract unique sources
    seen = set()
    sources = []
    for r in results:
        vid = r.get("vacancy_id")
        if vid not in seen:
            seen.add(vid)
            sources.append({
                "name": r.get("vacancy_name"),
                "employer": r.get("employer"),
                "area": r.get("area"),
                "url": r.get("url"),
                "score": r.get("score"),
            })

    return {
        "answer": answer,
        "sources": sources,
        "context": context,
        "n_results": len(results),
    }
