"""

hh.ru API docs: https://github.com/hhru/api
"""

import time
import logging
import requests
from typing import Optional
from bs4 import BeautifulSoup

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import VACANCIES_URL, HEADERS, DEFAULT_SEARCH_PARAMS

logger = logging.getLogger(__name__)


def clean_html(html_text: Optional[str]) -> str:
    if not html_text:
        return ""
    return BeautifulSoup(html_text, "html.parser").get_text(separator="\n", strip=True)


def parse_salary(salary: Optional[dict]) -> dict:
    if not salary:
        return {"salary_from": None, "salary_to": None, "salary_currency": None, "salary_gross": None}
    return {
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "salary_currency": salary.get("currency"),
        "salary_gross": salary.get("gross"),  # True = до вычета налогов
    }


def fetch_vacancy_ids(
    text: str = "",
    area: Optional[int] = None,
    experience: Optional[str] = None,
    max_pages: int = 20,
    per_page: int = 100,
    search_fields: Optional[list] = None,
) -> list[dict]:
    """
    Search vacancies and return list of short vacancy dicts (id, name, url, salary, employer, area).

    Args:
        text: Search query (e.g. "Python developer")
        area: Region code (159=Almaty, 160=Kazakhstan, 113=Russia, 1=Moscow)
        experience: "noExperience", "between1And3", "between3And6", "moreThan6"
        max_pages: Max pages to fetch (each page = per_page items, API limit = 2000 items total)
        per_page: Items per page (max 100)
        search_fields: Where to search - ["name", "description", "company_name"]
    """

    params = {
        **DEFAULT_SEARCH_PARAMS,
        "per_page": per_page,
    }
    if text:
        params["text"] = text
    if area is not None:
        params["area"] = area
    if experience:
        params["experience"] = experience
    if search_fields:
        params["search_field"] = search_fields

    all_items = []

    for page in range(max_pages):
        params["page"] = page

        try:
            resp =  requests.get(VACANCIES_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            break

        data =  resp.json()
        items  = data.get("items", [])
        total_pages = data.get("pages", 0)
        found = data.get("found", 0)

        if page == 0:
            logger.info(f"Found {found} vacancies, {total_pages} pages")

        all_items.extend(items)
        logger.info(f"Page {page + 1}/{min(max_pages, total_pages)}: got {len(items)} items (total: {len(all_items)})")

        if page + 1 >= total_pages:
            break

        # Rate limiting — be polite to API
        time.sleep(0.25)

    return all_items


def fetch_vacancy_detail(vacancy_id: str) -> Optional[dict]:

    url = f"{VACANCIES_URL}/{vacancy_id}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching vacancy {vacancy_id}: {e}")
        return None


def parse_vacancy(raw: dict, detail: Optional[dict] = None) -> dict:

    salary = parse_salary(raw.get("salary"))

    employer =  raw.get("employer") or {}
    area = raw.get("area") or {}
    schedule = raw.get("schedule") or {}
    employment = raw.get("employment") or {}

    result = {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "url":raw.get("alternate_url"),  # human-readable URL
        "employer_name": employer.get("name"),
        "employer_url": employer.get("alternate_url"),
        "area": area.get("name"),
        "published_at": raw.get("published_at"),
        "schedule": schedule.get("name"),
        "employment" : employment.get("name"),
        **salary,
    }

    # If we have full detail — add description & skills
    if detail:
        result["description"] = clean_html(detail.get("description"))
        result["key_skills"] = ", ".join(
            skill["name"] for skill in detail.get("key_skills", [])
        )
        experience = detail.get("experience") or {}
        result["experience"] = experience.get("name")
    else:
        result["description"] = raw.get("snippet", {}).get("requirement", "") or ""
        result["key_skills"] = ""
        result["experience"] = ""

    return result


def collect_vacancies(
    text: str = "",
    area: Optional[int] = None,
    experience: Optional[str] = None,
    max_vacancies: int = 500,
    fetch_details: bool = True,
    detail_delay: float = 0.3,

) -> list[dict]:
    """
    Main function: search vacancies and optionally fetch full details for each.

    Args:
        text: Search query
        area: Region code
        experience: Experience level filter
        max_vacancies: Max number of vacancies to collect
        fetch_details: If True, fetch full description for each vacancy (slower but richer data)
        detail_delay: Delay between detail requests (seconds)

    Returns:
        List of parsed vacancy dicts
    """
    max_pages = (max_vacancies // 100) + 1

    logger.info(f"Searching: text='{text}', area={area}, max={max_vacancies}")
    raw_items = fetch_vacancy_ids(text=text, area=area, experience=experience, max_pages=max_pages)

    # Trim to requested max
    raw_items = raw_items[:max_vacancies]
    logger.info(f"Collected {len(raw_items)} vacancy summaries")

    parsed = []
    for i, item in enumerate(raw_items):
        detail = None
        if fetch_details:
            detail = fetch_vacancy_detail(item["id"])
            if detail_delay > 0:
                time.sleep(detail_delay)

        vacancy = parse_vacancy(item, detail)
        parsed.append(vacancy)

        if (i + 1) % 50 == 0:
            logger.info(f"Parsed {i + 1}/{len(raw_items)} vacancies")

    logger.info(f"Done! Parsed {len(parsed)} vacancies total")


    return parsed
