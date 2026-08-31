"""Keep rendered JSON copies of the ES index body and query DSL in sync.

The Python builders in search/index_config.py and search/queries.py stay the
source of truth. This test renders their output to docs/search/*.json so the
index settings and query shapes can be reviewed at a glance without reading
Python. Edit the builders, not the JSON: a stale file fails this test once,
gets rewritten, and you commit it.
"""

import json
from pathlib import Path

import pytest

from hybrid_search_api.models import SearchRequest
from hybrid_search_api.search.index_config import build_index_body
from hybrid_search_api.search.queries import bm25_query, knn_query

SNAPSHOT_DIR = Path(__file__).parent.parent / "docs" / "search"

SNAPSHOTS = {
    "index_settings.json": build_index_body(),
    "example_query_bm25.json": bm25_query("Vektorsuche"),
    "example_query_knn.json": knn_query([0.1, 0.2, 0.3], k=10),
    "example_search_request.json": SearchRequest(
        query="How does vector search work?", top_k=5
    ).model_dump(),
}


@pytest.mark.parametrize("filename, payload", SNAPSHOTS.items())
def test_snapshot_matches_builder(filename: str, payload: dict) -> None:
    path = SNAPSHOT_DIR / filename
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != rendered:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        pytest.fail(f"{path} was stale and has been regenerated - commit it")
