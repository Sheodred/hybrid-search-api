"""Opt-in utility script: downloads the NFCorpus subset of the BEIR benchmark
(https://github.com/beir-cellar/beir, ~3.6K medical documents) and indexes it
into its own Elasticsearch index - separate from the curated 10-doc sample set
in seed_data.py.

Why: the curated sample set is deliberately self-referential (it's about
search/RAG concepts), which makes for a clean demo but doesn't prove retrieval
works on topically unrelated content at more-than-trivial scale. NFCorpus is a
recognized IR benchmark that does. This script never touches the default
index and isn't wired into tests/CI - point the app at the result via
ELASTICSEARCH_INDEX when you want to try it.

Usage:
    python scripts/seed_nfcorpus.py
    python scripts/seed_nfcorpus.py --index documents_nfcorpus --limit 500
"""

import argparse
import json
import ssl
import urllib.request
import zipfile
from pathlib import Path

import certifi

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client, ensure_index
from hybrid_search_api.search.embeddings import embed_many

NFCORPUS_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "nfcorpus"
BATCH_SIZE = 256


def download_and_extract() -> Path:
    corpus_path = DATA_DIR / "nfcorpus" / "corpus.jsonl"
    if corpus_path.exists():
        return corpus_path

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "nfcorpus.zip"
    print(f"Downloading NFCorpus (~2.4MB) from {NFCORPUS_URL} ...")
    # Explicit certifi CA bundle: some local Python installs (esp. on Windows)
    # don't hook into the system trust store, so the default SSL context
    # fails cert verification even against a perfectly valid host.
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(NFCORPUS_URL, timeout=60, context=context) as resp:
        zip_path.write_bytes(resp.read())

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(DATA_DIR)
    zip_path.unlink()
    return corpus_path


def load_corpus(corpus_path: Path, limit: int | None) -> list[dict]:
    docs = []
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            docs.append({"title": row.get("title") or "Untitled", "content": row["text"]})
            if limit and len(docs) >= limit:
                break
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        default=None,
        help="Target ES index (default: '<ELASTICSEARCH_INDEX>_nfcorpus' - "
        "kept separate from the default demo index).",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Index only the first N documents (default: all ~3.6K)."
    )
    args = parser.parse_args()

    settings = get_settings()
    index_name = args.index or f"{settings.elasticsearch_index}_nfcorpus"

    corpus_path = download_and_extract()
    docs = load_corpus(corpus_path, args.limit)

    client = build_client(settings)
    ensure_index(client, index_name)

    print(f"Computing embeddings for {len(docs)} documents (a minute or two on CPU)...")
    for start in range(0, len(docs), BATCH_SIZE):
        batch = docs[start : start + BATCH_SIZE]
        vectors = embed_many([doc["content"] for doc in batch])
        for i, (doc, vector) in enumerate(zip(batch, vectors, strict=True), start=start + 1):
            client.index(index=index_name, id=str(i), document={**doc, "embedding": vector})
        print(f"  indexed {min(start + BATCH_SIZE, len(docs))}/{len(docs)}")

    client.indices.refresh(index=index_name)
    print(f"Indexed {len(docs)} NFCorpus documents (with embeddings) into '{index_name}'.")
    print(f"Try it: set ELASTICSEARCH_INDEX={index_name} and restart the API.")


if __name__ == "__main__":
    main()
