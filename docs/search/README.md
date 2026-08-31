# Rendered index & query reference

Every `.json` here is generated from a Python builder by
`tests/test_config_snapshots.py`. **Edit the builder, not the JSON** - a stale
file fails that test once, gets rewritten, and you commit it.

The builders are the source of truth:

- `src/hybrid_search_api/search/index_config.py` - how documents are indexed
- `src/hybrid_search_api/search/queries.py` - how searches are phrased

All query examples use one scenario so they can be read side by side: the
query `"approximate nearest neighbor search"`, `k = 10`, and the filters
`category=["vector-search"]`, `published_after="2024-01-01"`,
`min_word_count=30`. The kNN example carries a 3-dimensional placeholder
vector to stay readable; the real one is 384-dimensional.

## Run them yourself

```powershell
docker compose up -d elasticsearch
python scripts/seed_data.py --recreate
python scripts/run_examples.py
```

`run_examples.py` POSTs each example to the local cluster and prints what came
back. The test suite proves the *shapes* are right without a cluster; this
proves Elasticsearch actually accepts them.

## The files

### `index_settings.json`
The complete index body: analysis chain plus field mappings.

| What to look at | Why it's there |
|---|---|
| `en_index` vs `en_search` | Documents are indexed **without** synonym expansion, queries analyzed **with** it. Keeps the index small and lets the synonym list change without a full reindex. |
| `domain_synonyms` | `synonym_graph`, not `synonym` - the multi-word entries ("approximate nearest neighbor") only work correctly in the graph form. Sits after `lowercase`/`en_possessive` and before `en_stop`/`en_stemmer`, so expansions get stopworded and stemmed like everything else. |
| `exact` analyzer | No stemming, no stopwords. This is what `match_phrase` on `content.exact` searches, so a phrase query means the literal wording. |
| `keyword_lower` normalizer | `keyword` fields aren't analyzed, so this is what makes `Vector-Search` and `vector-search` land in one aggregation bucket. |
| `term_vector: with_positions_offsets` on `content` | Lets the `unified` highlighter cut snippets without re-analyzing the field. |
| `embedding.index_options` | Explicit `int8_hnsw` - 4x smaller than raw float32 at essentially unchanged recall. Without it, ES 9.x picks `bbq_hnsw` at 384 dims. |
| `copy_to: all_text` | `title`, `content` and `tags` are copied into one catch-all field, so a query can match "anywhere" without listing every field. |
| `url.index: false` | Stored and returned for citation, never searched - no inverted index built for it. |
| `dynamic: strict` | A document with an undeclared field is **rejected**, not silently mapped. Declare fields here first; the seed scripts fail loudly otherwise. |

**Try changing:** swap `light_english` for `english` (Porter, more aggressive)
and re-run `run_examples.py` to see recall shift. Any change here needs
`python scripts/seed_data.py --recreate` - `ensure_index()` only creates a
missing index, it never updates one.

### `example_query_text.json`
The scoring half of a search. `most_fields` sums per-field scores rather than
taking the best one, which suits the same text being searchable through
`title`, `content` and `all_text`. `minimum_should_match: 75%` stops a long
fuzzy query from matching on one stray term.

The `should` clause is where `.exact` earns its place: the main fields are
stemmed, so a phrase query against them would match looser wording than the
user typed. `content.exact` keeps the literal tokens.

**Try changing:** `TITLE_BOOST`, or drop `fuzziness` for strict matching.

### `example_query_bm25_filtered.json`
The same query plus **filter context**. The distinction is the point:

- `must` / `should` ask *how well* a document matches and produce a score.
- `filter` asks *whether* it may match at all - no score contribution, and
  Elasticsearch caches the result.

All metadata narrowing belongs in `filter`. Note `terms` (a list) and `range`
(with ISO date bounds) side by side.

### `example_query_knn_prefiltered.json`
The vector half, with the **same** filter clauses as the BM25 side. Both
halves must see the identical subset or fusion merges two differently-scoped
result sets.

`filter` on a kNN query is a **pre-filter**: applied before the approximate
search, so `num_candidates` is drawn from the filtered subset. Post-filtering
would search the whole index and then throw most of it away, which can return
far fewer than `k` results.

**Try changing:** `KNN_CANDIDATE_MULTIPLIER` - higher is more accurate and
slower.

### `example_highlight.json`
`unified` highlighter over `content`, backed by the stored term vectors.
Returns up to 2 fragments of ~150 characters with matches wrapped in `<em>`.

These snippets do double duty: they go to the client as `hits[].highlights`,
**and** they become the RAG context in `search/answering.py`, so the model
reads the matching passages rather than whole documents. Hits found only by
the vector side have no snippet and fall back to full content.

### `example_aggs_facets.json`
Three aggregation shapes: `terms` for categorical buckets (`categories`,
`tags`), `date_histogram` for a time axis (`by_month`), `stats` for a numeric
summary (`word_count`).

**One caveat worth knowing:** aggregations ride on the BM25 call only. ES
computes them over everything matching that query under the active filters -
so the counts describe *the BM25 match set*, not the fused result set. Running
them on the kNN call too would just produce a second bucket set to reconcile.

### `example_function_score_recency.json`
**Reference only - not called by `/search`.** A `gauss` decay on `published`
multiplies relevance by a factor that falls off with age, so a
slightly-less-relevant recent document can outrank a stale one.

`scale` is the age at which the factor reaches `decay` (here: two years to
half). It has to match the corpus's actual age spread - at a more typical
`180d` every document in this 2023-2025 demo set decays to effectively zero
and the ranking becomes noise dressed up as recency.

Left out of the running path deliberately: recency bias is a product
decision, and this corpus has no freshness requirement.

### `example_search_request.json`
The API-level request body, not Elasticsearch DSL - what you'd POST to
`/search`. Shows where `filters` sits in the contract.

## The plain, unfiltered forms

`bm25_query(q)` and `knn_query(vec, k)` without filters produce the same
bodies minus the `filter` key entirely (not an empty list). Only the filtered
variants are rendered here, to keep the file count honest.
