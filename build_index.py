
import argparse
import json

from rag.chunker import chunk_documents
from rag.indexer import build_index


def main():
    p = argparse.ArgumentParser(description="Build FAISS index from vacancy data")
    p.add_argument("--input", type=str, default="data/vacancies_all.json", help="Input JSON file")
    p.add_argument("--index-dir", type=str, default="data/index", help="Output index directory")
    p.add_argument("--max-chunk-len", type=int, default=1500, help="Max chunk length in chars")
    args = p.parse_args()

    # Load vacancies
    with open(args.input, "r", encoding="utf-8") as f:
        vacancies = json.load(f)
    print(f"Loaded {len(vacancies)} vacancies from {args.input}")

    # Filter out vacancies without description
    vacancies = [v for v in vacancies if len(v.get("description", "")) > 30]
    print(f"After filtering: {len(vacancies)} with descriptions")

    # Chunk
    chunks = chunk_documents(vacancies, max_chunk_length=args.max_chunk_len)
    print(f"Created {len(chunks)} chunks")

    # Build index
    build_index(chunks, index_dir=args.index_dir)
    print("\nDone! Index ready for RAG queries.")


if __name__ == "__main__":
    main()

