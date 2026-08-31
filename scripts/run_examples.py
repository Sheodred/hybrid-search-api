"""Opt-in utility script: runs every rendered example in docs/search/ against a
local Elasticsearch and prints what came back.

The examples are snapshots of the builders in search/queries.py (kept in sync
by tests/test_config_snapshots.py). The test suite asserts their *shape*
without a cluster; this script is the other half - proof that Elasticsearch
actually accepts them, and a loop for trying edits by hand.

    docker compose up -d elasticsearch
    python scripts/seed_data.py --recreate
    python scripts/run_examples.py

Not wired into tests or CI - it needs a live cluster with seeded data.
"""

import json
from pathlib import Path

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client
from hybrid_search_api.search.embeddings import embed

EXAMPLES = Path(__file__).resolve().parent.parent / "docs" / "search"
# The rendered kNN example carries a 3-dim placeholder vector so the snapshot
# stays readable; a real search needs the model's actual 384 dims.
QUERY = "approximate nearest neighbor search"
SIZE = 3


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def show(label: str, resp: dict) -> None:
    hits = resp["hits"]["hits"]
    print(f"\n{label}: {resp['hits']['total']['value']} hit(s)")
    for hit in hits[:SIZE]:
        print(f"  {hit['_score']:>8.4f}  {hit['_source'].get('title', '')}")
        for fragment in hit.get("highlight", {}).get("content", []):
            print(f"            ...{fragment}")


def main() -> None:
    settings = get_settings()
    client = build_client(settings)
    index = settings.elasticsearch_index

    for name in ("example_query_text.json", "example_query_bm25_filtered.json"):
        show(name, client.search(index=index, query=load(name), size=SIZE))

    show(
        "example_function_score_recency.json",
        client.search(index=index, query=load("example_function_score_recency.json"), size=SIZE),
    )

    knn = load("example_query_knn_prefiltered.json")
    knn["query_vector"] = embed(QUERY)
    show("example_query_knn_prefiltered.json (real 384-dim vector)",
         client.search(index=index, knn=knn, size=SIZE))

    show(
        "example_highlight.json (with the text query)",
        client.search(
            index=index,
            query=load("example_query_text.json"),
            highlight=load("example_highlight.json"),
            size=SIZE,
        ),
    )

    resp = client.search(index=index, aggs=load("example_aggs_facets.json"), size=0)
    print("\nexample_aggs_facets.json:")
    for name, agg in resp["aggregations"].items():
        if "buckets" in agg:
            buckets = ", ".join(
                f"{b.get('key_as_string', b['key'])}={b['doc_count']}" for b in agg["buckets"]
            )
            print(f"  {name}: {buckets}")
        else:
            print(f"  {name}: {agg}")


if __name__ == "__main__":
    main()
