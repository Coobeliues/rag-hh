#!/usr/bin/env python3
"""
CLI entry point for hh.kz vacancy parser.

Usage:
    # Parse Python vacancies in Almaty (default 500)
    python parse.py --query "Python developer" --area almaty

    # Parse 2000 Data Science vacancies across Kazakhstan
    python parse.py --query "Data Science" --area kazakhstan --max 2000

    # Quick parse without full descriptions (faster, less data)
    python parse.py --query "ML engineer" --no-details

    # Parse with experience filter
    python parse.py --query "Backend" --area almaty --experience between1And3
"""

import argparse
import logging
import sys

from config import AREAS, RAW_VACANCIES_FILE, PARSED_VACANCIES_FILE
from parser.hh_parser import collect_vacancies
from parser.storage import save_json, save_csv


def main():
    p = argparse.ArgumentParser(description="Parse vacancies from hh.kz / hh.ru API")
    p.add_argument("-q", "--query", type=str, default="", help="Search query (e.g. 'Python developer')")
    p.add_argument("-a", "--area", type=str, default="kazakhstan",
                   help=f"Region: {', '.join(AREAS.keys())} or numeric area ID")
    p.add_argument("-m", "--max", type=int, default=500, help="Max vacancies to collect (default: 500)")
    p.add_argument("--experience", type=str, default=None,
                   choices=["noExperience", "between1And3", "between3And6", "moreThan6"],
                   help="Experience filter")
    p.add_argument("--no-details", action="store_true",
                   help="Skip fetching full descriptions (faster but less data)")
    p.add_argument("--json-out", type=str, default=RAW_VACANCIES_FILE, help="Output JSON path")
    p.add_argument("--csv-out", type=str, default=PARSED_VACANCIES_FILE, help="Output CSV path")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve area
    if args.area.isdigit():
        area_id = int(args.area)
    else:
        area_id = AREAS.get(args.area.lower())
        if area_id is None:
            print(f"Unknown area '{args.area}'. Available: {', '.join(AREAS.keys())}")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  hh.kz Vacancy Parser")
    print(f"  Query: '{args.query}' | Area: {args.area} ({area_id})")
    print(f"  Max: {args.max} | Details: {not args.no_details}")
    print(f"{'='*60}\n")

    vacancies = collect_vacancies(
        text=args.query,
        area=area_id,
        max_vacancies=args.max,
        fetch_details=not args.no_details,
        experience=args.experience,
    )

    if not vacancies:
        print("No vacancies found!")
        sys.exit(0)

    save_json(vacancies, args.json_out)
    save_csv(vacancies, args.csv_out)

    # Quick stats
    with_salary = sum(1 for v in vacancies if v.get("salary_from") or v.get("salary_to"))
    companies = len(set(v.get("employer_name", "") for v in vacancies))
    print(f"\n--- Stats ---")
    print(f"Total vacancies: {len(vacancies)}")
    print(f"With salary: {with_salary} ({100 * with_salary // len(vacancies)}%)")
    print(f"Unique companies: {companies}")


if __name__ == "__main__":
    main()
