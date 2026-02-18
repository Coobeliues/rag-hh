
from parser.hh_parser import clean_html, parse_salary, parse_vacancy


class TestCleanHtml:
    def test_removes_tags(self):
        assert clean_html("<b>Bold</b> text") == "Bold\ntext"

    def test_none_input(self):
        assert clean_html(None) == ""

    def test_empty_string(self):
        assert clean_html("") == ""

    def test_nested_tags(self):
        html = "<div><p>Hello</p><ul><li>A</li><li>B</li></ul></div>"
        result = clean_html(html)
        assert "Hello" in result
        assert "A" in result
        assert "B" in result


class TestParseSalary:
    def test_full_salary(self):
        sal = {"from": 500000, "to": 800000, "currency": "KZT", "gross": True}
        result = parse_salary(sal)
        assert result["salary_from"] == 500000
        assert result["salary_to"] == 800000
        assert result["salary_currency"] == "KZT"
        assert result["salary_gross"] is True

    def test_none_salary(self):
        result = parse_salary(None)
        assert result["salary_from"] is None
        assert result["salary_to"] is None
        assert result["salary_currency"] is None

    def test_partial_salary(self):
        result = parse_salary({"from": 300000, "to": None, "currency": "KZT"})
        assert result["salary_from"] == 300000
        assert result["salary_to"] is None


class TestParseVacancy:
    def test_basic_parsing(self):
        raw = {
            "id": "123",
            "name": "Python Dev",
            "alternate_url": "https://hh.kz/vacancy/123",
            "employer": {"name": "TestCo", "alternate_url": "https://hh.kz/employer/1"},
            "area": {"name": "Алматы"},
            "salary": {"from": 500000, "to": 700000, "currency": "KZT", "gross": False},
            "published_at": "2025-01-01",
            "schedule": {"name": "Полный день"},
            "employment": {"name": "Полная занятость"},
        }
        detail = {
            "description": "<p>Описание</p>",
            "key_skills": [{"name": "Python"}, {"name": "Django"}],
            "experience": {"name": "От 1 до 3 лет"},
        }
        v = parse_vacancy(raw, detail)
        assert v["id"] == "123"
        assert v["name"] == "Python Dev"
        assert v["employer_name"] == "TestCo"
        assert v["area"] == "Алматы"
        assert v["salary_from"] == 500000
        assert v["description"] == "Описание"
        assert v["key_skills"] == "Python, Django"
        assert v["experience"] == "От 1 до 3 лет"

    def test_without_detail(self):
        raw = {
            "id": "456",
            "name": "Dev",
            "alternate_url": "https://hh.kz/vacancy/456",
            "employer": {"name": "Co"},
            "area": {"name": "Астана"},
            "salary": None,
            "snippet": {"requirement": "Знание Python"},
            "schedule": None,
            "employment": None,
        }
        v = parse_vacancy(raw)
        assert v["description"] == "Знание Python"
        assert v["key_skills"] == ""
        assert v["experience"] == ""

    def test_missing_fields_no_crash(self):
        raw = {"id": "1"}
        v = parse_vacancy(raw)
        assert v["id"] == "1"
        assert v["name"] is None
        assert v["salary_from"] is None




