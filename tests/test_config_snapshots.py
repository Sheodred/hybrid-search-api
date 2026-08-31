"""Keep rendered JSON copies of the ES index body and query DSL in sync.

The Python builders in search/index_config.py and search/queries.py stay the
source of truth. This test renders their output to docs/search/*.json so the
index settings and query shapes can be reviewed at a glance without reading
Python. Edit the builders, not the JSON: a stale file fails this test once,
gets rewritten, and you commit it.

Every example uses one consistent scenario so the files can be read side by
side - see docs/search/README.md.
"""

import json
from pathlib import Path

import pytest

from hybrid_search_api.models import SearchFilters, SearchRequest
from hybrid_search_api.search.index_config import build_index_body
from hybrid_search_api.search.queries import (
    bm25_query,
    facet_aggs,
    highlight_config,
    knn_query,
    recency_boosted_query,
    text_query,
)

SNAPSHOT_DIR = Path(__file__).parent.parent / "docs" / "search"

QUERY = "approximate nearest neighbor search"
QUERY_VECTOR = [0.1, 0.2, 0.3]  # short placeholder; the real one is 384-dim
K = 10
# min_word_count is 30, not a rounder 40, on purpose: the demo corpus runs
# 30-38 words per document, so a threshold of 40 would make every filtered
# example return zero hits and demonstrate nothing.
FILTERS = SearchFilters(
    category=["vector-search"], published_after="2024-01-01", min_word_count=30
)

SNAPSHOTS = {
    "index_settings.json": build_index_body(),
    "example_search_request.json": SearchRequest(
        query="How does vector search work?", top_k=5, filters=FILTERS
    ).model_dump(mode="json"),
    "example_query_text.json": text_query(QUERY),
    "example_query_bm25_filtered.json": bm25_query(QUERY, FILTERS),
    "example_query_knn_prefiltered.json": knn_query(QUERY_VECTOR, K, FILTERS),
    "example_highlight.json": highlight_config(),
    "example_aggs_facets.json": facet_aggs(),
    "example_function_score_recency.json": recency_boosted_query(QUERY),
}


@pytest.mark.parametrize("filename, payload", SNAPSHOTS.items())
def test_snapshot_matches_builder(filename: str, payload: dict) -> None:
    path = SNAPSHOT_DIR / filename
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != rendered:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        pytest.fail(f"{path} was stale and has been regenerated - commit it")


def test_no_orphaned_snapshots() -> None:
    """A renamed or dropped builder must not leave a stale example behind -
    docs/search/ should contain exactly what SNAPSHOTS renders."""
    on_disk = {p.name for p in SNAPSHOT_DIR.glob("*.json")}
    assert on_disk == set(SNAPSHOTS), (
        f"unexpected: {sorted(on_disk - set(SNAPSHOTS))}, "
        f"missing: {sorted(set(SNAPSHOTS) - on_disk)}"
    )
