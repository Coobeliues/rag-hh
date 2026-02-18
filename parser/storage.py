import json
import os
import pandas as pd
from typing import Optional


def save_json(vacancies: list[dict], filepath: str) -> None:

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(vacancies)} vacancies to {filepath}")


def save_csv(vacancies: list[dict], filepath: str) -> None:

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(vacancies)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compatibility
    print(f"Saved {len(vacancies)} vacancies to {filepath}")


def load_json(filepath: str) -> list[dict]:

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(filepath: str) -> pd.DataFrame:


    return pd.read_csv(filepath)
