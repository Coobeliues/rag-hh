"""
Chunking vacancies for RAG.

Each vacancy becomes 1 chunk (structured text document).
For very long descriptions we split into overlapping chunks.
"""


def vacancy_to_document(vacancy: dict) -> str:
    """
    Convert a vacancy dict into a structured text document for embedding.
    Combines all fields into a searchable text block.
    """
    parts = []

    name = vacancy.get("name", "")
    employer = vacancy.get("employer_name", "")
    area = vacancy.get("area", "")
    parts.append(f"Вакансия: {name}")
    parts.append(f"Компания: {employer}")
    parts.append(f"Город: {area}")

    # Salary
    sal_from = vacancy.get("salary_from")
    sal_to = vacancy.get("salary_to")
    currency = vacancy.get("salary_currency", "")
    if sal_from or sal_to:
        sal_str = ""
        if sal_from and sal_to:
            sal_str = f"от {sal_from} до {sal_to} {currency}"
        elif sal_from:
            sal_str = f"от {sal_from} {currency}"
        elif sal_to:
            sal_str = f"до {sal_to} {currency}"
        gross = vacancy.get("salary_gross")
        if gross:
            sal_str += " (до вычета налогов)"
        parts.append(f"Зарплата: {sal_str}")

    exp = vacancy.get("experience", "")
    if exp:
        parts.append(f"Опыт: {exp}")

    schedule = vacancy.get("schedule", "")
    employment = vacancy.get("employment", "")
    if schedule:
        parts.append(f"График: {schedule}")
    if employment:
        parts.append(f"Занятость: {employment}")

    skills = vacancy.get("key_skills", "")
    if skills:
        parts.append(f"Ключевые навыки: {skills}")

    desc = vacancy.get("description", "")
    if desc:
        parts.append(f"\nОписание:\n{desc}")

    return "\n".join(parts)


def chunk_documents(
    vacancies: list[dict],
    max_chunk_length: int = 1500,
    overlap: int = 200,
) -> list[dict]:
    """
    Convert vacancies into chunks for embedding.

    Returns list of dicts: {text, vacancy_id, vacancy_name, employer, chunk_index}

    Most vacancies fit in one chunk. Long descriptions get split with overlap.
    """
    chunks = []

    for v in vacancies:
        full_text = vacancy_to_document(v)
        vacancy_meta = {
            "vacancy_id": v.get("id"),
            "vacancy_name": v.get("name", ""),
            "employer": v.get("employer_name", ""),
            "area": v.get("area", ""),
            "url": v.get("url", ""),
            "salary_from": v.get("salary_from"),
            "salary_to": v.get("salary_to"),
            "salary_currency": v.get("salary_currency"),
            "experience": v.get("experience", ""),
        }

        if len(full_text) <= max_chunk_length:
            chunks.append({"text": full_text, "chunk_index": 0, **vacancy_meta})
        else:
            # Split long text into overlapping chunks
            start = 0
            idx = 0
            while start < len(full_text):
                end = start + max_chunk_length
                chunk_text = full_text[start:end]
                chunks.append({"text": chunk_text, "chunk_index": idx, **vacancy_meta})
                start += max_chunk_length - overlap
                idx += 1

    return chunks
