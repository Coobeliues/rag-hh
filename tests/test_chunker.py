"""Tests for rag/chunker.py."""

from rag.chunker import vacancy_to_document, chunk_documents


class TestVacancyToDocument:
    def test_basic_fields(self, sample_vacancy):
        doc = vacancy_to_document(sample_vacancy)
        assert "Python Developer" in doc
        assert "ТОО Тест" in doc
        assert "Алматы" in doc

    def test_salary_range(self, sample_vacancy):
        doc = vacancy_to_document(sample_vacancy)
        assert "500000" in doc
        assert "800000" in doc
        assert "KZT" in doc

    def test_salary_from_only(self):
        v = {"salary_from": 300000, "salary_to": None, "salary_currency": "KZT"}
        doc = vacancy_to_document(v)
        assert "от 300000" in doc
        assert "до" not in doc.split("Зарплата:")[1].split("\n")[0]

    def test_salary_to_only(self):
        v = {"salary_from": None, "salary_to": 500000, "salary_currency": "KZT"}
        doc = vacancy_to_document(v)
        assert "до 500000" in doc

    def test_no_salary(self):
        v = {"name": "Dev", "employer_name": "Co"}
        doc = vacancy_to_document(v)
        assert "Зарплата" not in doc

    def test_experience_included(self, sample_vacancy):
        doc = vacancy_to_document(sample_vacancy)
        assert "От 1 до 3 лет" in doc

    def test_skills_included(self, sample_vacancy):
        doc = vacancy_to_document(sample_vacancy)
        assert "Python, Django, PostgreSQL, REST API" in doc

    def test_description_included(self, sample_vacancy):
        doc = vacancy_to_document(sample_vacancy)
        assert "Python-разработчика" in doc

    def test_gross_salary_note(self):
        v = {"salary_from": 100000, "salary_gross": True, "salary_currency": "KZT"}
        doc = vacancy_to_document(v)
        assert "до вычета налогов" in doc

    def test_empty_vacancy(self):
        doc = vacancy_to_document({})
        assert "Вакансия:" in doc  # header always present


class TestChunkDocuments:
    def test_single_vacancy_single_chunk(self, sample_vacancy):
        chunks = chunk_documents([sample_vacancy])
        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0

    def test_metadata_preserved(self, sample_vacancy):
        chunks = chunk_documents([sample_vacancy])
        c = chunks[0]
        assert c["vacancy_id"] == "12345"
        assert c["vacancy_name"] == "Python Developer"
        assert c["employer"] == "ТОО Тест"
        assert c["area"] == "Алматы"
        assert c["url"] == "https://hh.kz/vacancy/12345"
        assert c["salary_from"] == 500000
        assert c["salary_to"] == 800000
        assert c["salary_currency"] == "KZT"
        assert c["experience"] == "От 1 до 3 лет"

    def test_multiple_vacancies(self, sample_vacancies):
        chunks = chunk_documents(sample_vacancies)
        ids = {c["vacancy_id"] for c in chunks}
        assert ids == {"12345", "67890", "11111"}

    def test_long_text_splits(self):
        v = {
            "id": "999",
            "name": "Long Vacancy",
            "employer_name": "BigCo",
            "description": "A" * 3000,
        }
        chunks = chunk_documents([v], max_chunk_length=500, overlap=100)
        assert len(chunks) > 1
        # All chunks share the same vacancy_id
        assert all(c["vacancy_id"] == "999" for c in chunks)
        # chunk_index increments
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_overlap_content(self):
        desc = "ABCDEFGHIJ" * 200  # 2000 chars
        v = {"id": "1", "name": "X", "employer_name": "Y", "description": desc}
        chunks = chunk_documents([v], max_chunk_length=500, overlap=100)
        # Overlapping chunks should share some text
        if len(chunks) >= 2:
            end_of_first = chunks[0]["text"][-100:]
            assert end_of_first in chunks[1]["text"]

    def test_empty_list(self):
        assert chunk_documents([]) == []
