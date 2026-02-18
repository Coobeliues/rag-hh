
import pytest
from rag.indexer import _passes_filters


class TestPassesFilters:

    def _chunk(self, **overrides):
        base = {
            "vacancy_id": "1",
            "vacancy_name": "Dev",
            "employer": "Co",
            "area": "Алматы",
            "salary_from": 400000,
            "salary_to": 600000,
            "salary_currency": "KZT",
            "experience": "От 1 до 3 лет",
            "text": "Вакансия: Dev\nОпыт: От 1 до 3 лет",
        }
        base.update(overrides)
        return base

    # --- City filter ---

    def test_city_exact_match(self):
        c = self._chunk(area="Алматы")
        assert _passes_filters(c, {"city": "Алматы"}) is True

    def test_city_case_insensitive(self):
        c = self._chunk(area="Алматы")
        assert _passes_filters(c, {"city": "алматы"}) is True

    def test_city_mismatch(self):
        c = self._chunk(area="Астана")
        assert _passes_filters(c, {"city": "Алматы"}) is False

    def test_city_empty_area(self):
        c = self._chunk(area="")
        assert _passes_filters(c, {"city": "Алматы"}) is False

    def test_city_none_area(self):
        c = self._chunk(area=None)
        assert _passes_filters(c, {"city": "Алматы"}) is False

    # --- Salary filter ---

    def test_salary_passes(self):
        c = self._chunk(salary_from=500000, salary_to=700000)
        assert _passes_filters(c, {"salary_min": 600000}) is True

    def test_salary_fails(self):
        c = self._chunk(salary_from=200000, salary_to=300000)
        assert _passes_filters(c, {"salary_min": 500000}) is False

    def test_salary_from_only(self):
        c = self._chunk(salary_from=600000, salary_to=None)
        assert _passes_filters(c, {"salary_min": 500000}) is True

    def test_salary_to_only(self):
        c = self._chunk(salary_from=None, salary_to=600000)
        assert _passes_filters(c, {"salary_min": 500000}) is True

    def test_salary_zero_means_not_specified(self):
        c = self._chunk(salary_from=None, salary_to=None)
        assert _passes_filters(c, {"salary_min": 100000}) is False

    # --- Experience filter ---

    def test_experience_match_metadata(self):
        c = self._chunk(experience="От 1 до 3 лет")
        assert _passes_filters(c, {"experience": "От 1 до 3 лет"}) is True

    def test_experience_mismatch(self):
        c = self._chunk(experience="Нет опыта", text="Вакансия: Dev\nОпыт: Нет опыта")
        assert _passes_filters(c, {"experience": "От 3 до 6 лет"}) is False

    def test_experience_fallback_to_text(self):
        c = self._chunk(experience="", text="Опыт: От 1 до 3 лет\nОписание")
        assert _passes_filters(c, {"experience": "От 1 до 3 лет"}) is True

    # --- Combined filters ---

    def test_all_filters_pass(self):
        c = self._chunk(area="Алматы", salary_from=600000, experience="От 1 до 3 лет")
        filters = {"city": "Алматы", "salary_min": 500000, "experience": "От 1 до 3 лет"}
        assert _passes_filters(c, filters) is True

    def test_one_filter_fails(self):
        c = self._chunk(area="Астана", salary_from=600000, experience="От 1 до 3 лет")
        filters = {"city": "Алматы", "salary_min": 500000}
        assert _passes_filters(c, filters) is False

    def test_no_filters(self):
        c = self._chunk()
        assert _passes_filters(c, {}) is True












 







