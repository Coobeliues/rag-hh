#!/usr/bin/env python3

import json
import glob
import os


DATA_DIR = "data"
OUTPUT_JSON = f"{DATA_DIR}/vacancies_all.json"
OUTPUT_CSV = f"{DATA_DIR}/vacancies_all.csv"

 
def merge():
    files = glob.glob(f"{DATA_DIR}/*.json")
    # Exclude the output file itself and raw file
    files = [f for f in files if os.path.basename(f) not in ("vacancies_all.json", "vacancies_raw.json")]

    all_vacancies = []
    seen_ids = set()

    for filepath in sorted(files):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        before = len(all_vacancies)
        for v in data:
            vid = v.get("id")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_vacancies.append(v)

        added = len(all_vacancies) - before
        print(f"  {filepath}: {len(data)} total, {added} new (skipped {len(data) - added} duplicates)")

    # Save merged
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_vacancies, f, ensure_ascii=False, indent=2)

    import pandas as pd
    df = pd.DataFrame(all_vacancies)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\nMerged: {len(all_vacancies)} unique vacancies")
    print(f"  -> {OUTPUT_JSON}")
    print(f"  -> {OUTPUT_CSV}")  

    # Stats
    with_salary = sum(1 for v in all_vacancies if v.get("salary_from") or v.get("salary_to"))
    with_desc = sum(1 for v in all_vacancies if len(v.get("description", "")) > 50)
    companies = len(set(v.get("employer_name", "") for v in all_vacancies))


    print(f"\n--- Stats ---")
    print(f"With salary: {with_salary} ({100 * with_salary // max(len(all_vacancies), 1)}%)")
    print(f"With description: {with_desc}")  
    print(f"Unique companies: {companies}")



if __name__ == "__main__":
    merge()
