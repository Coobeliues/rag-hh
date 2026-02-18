
import sys
import os
import pytest
 
# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_vacancy():
    """Single vacancy dict as returned by the parser."""
    return {
        "id": "12345",
        "name": "Python Developer",
        "employer_name": "ТОО Тест",
        "area": "Алматы",
        "url": "https://hh.kz/vacancy/12345",
        "salary_from": 500000,
        "salary_to": 800000,
        "salary_currency": "KZT",
        "salary_gross": False,
        "experience": "От 1 до 3 лет",
        "schedule": "Полный день",
        "employment": "Полная занятость",
        "key_skills": "Python, Django, PostgreSQL, REST API",
        "description": "Мы ищем опытного Python-разработчика для работы над внутренними продуктами.",
    }


@pytest.fixture
def sample_vacancies(sample_vacancy):
    v2 = {
        "id": "67890",
        "name": "Data Scientist",
        "employer_name": "DataCorp KZ",
        "area": "Астана",
        "url": "https://hh.kz/vacancy/67890",
        "salary_from": 700000,
        "salary_to": None,
        "salary_currency": "KZT",
        "salary_gross": True,
        "experience": "От 3 до 6 лет",
        "schedule": "Удалённая работа",
        "employment": "Полная занятость",
        "key_skills": "Python, Pandas, ML, TensorFlow",
        "description": "Ищем Data Scientist для построения ML-моделей.",
    }
    v3 = {
        "id": "11111",
        "name": "Junior Frontend",
        "employer_name": "WebStudio",
        "area": "Алматы",
        "url": "https://hh.kz/vacancy/11111",
        "salary_from": None,
        "salary_to": 350000,
        "salary_currency": "KZT",
        "salary_gross": False,
        "experience": "Нет опыта",
        "schedule": "Полный день",
        "employment": "Полная занятость",
        "key_skills": "JavaScript, React, CSS",
        "description": "Начинающий фронтенд-разработчик в дружную команду.",
    }


    return [sample_vacancy, v2, v3]
