"""Configuration for hh.kz vacancy parser."""

# hh.ru API (works for hh.kz too — same backend)
BASE_URL = "https://api.hh.ru"
VACANCIES_URL = f"{BASE_URL}/vacancies"

# Request headers — hh.ru API requires User-Agent
HEADERS = {
    "User-Agent": "rag-hh-vacancy-parser/1.0 (keosido@github.com)",
}

# Default search parameters
DEFAULT_SEARCH_PARAMS = {
    "area": 40,           # 40 = Казахстан. 160 = Алматы, 159 = Астана
    "per_page": 100,      # max 100
    "page": 0,
}

# Area codes
AREAS = {
    "kazakhstan": 40,     # Весь Казахстан
    "almaty": 160,
    "astana": 159,
    "russia": 113,
    "moscow": 1,
    "spb": 2,
}

# Data paths
DATA_DIR = "data"
RAW_VACANCIES_FILE = f"{DATA_DIR}/vacancies_raw.json"
PARSED_VACANCIES_FILE = f"{DATA_DIR}/vacancies.csv"
