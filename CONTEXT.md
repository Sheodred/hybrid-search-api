# Context — hybrid-search-api

One-paragraph description of what this project/context is and its boundary.

## Ubiquitous language

The glossary. One entry per domain term the code and issues should use. For each:
the canonical term, a one-line definition, and — where it matters — the synonyms
to avoid so language doesn't drift.

**Search Answering**: the deep module owning the `/search` request end to end —
builds the Elasticsearch client, embeds the query (falling back to BM25-only if
embedding fails), runs Hybrid Search, and synthesizes a RAG answer if requested.
Framework-agnostic: raises the LLM SDK's own exceptions rather than
`HTTPException`, leaving HTTP translation to the route.
`search/answering.py:answer_search()`. _Avoid_: search orchestration, the search
service (there's one function, not a service layer).

**Filter Context**: the clauses deciding *whether* a document may match, as
opposed to query context which decides *how well*. Contributes no score, is
cached by Elasticsearch, and is built once per request and handed to both the
BM25 and the kNN side. `search/queries.py:filter_clauses()`. _Avoid_: filters
as a synonym for "the query", or for the user-facing `SearchFilters` request
model — that's the input, this is what it compiles to.

**kNN Pre-Filter**: a filter applied *before* the approximate vector search, so
`num_candidates` is drawn from the filtered subset. _Avoid_: confusing with
post-filtering, which searches the whole index and discards afterwards and can
return far fewer than `k` results.

**Facet**: a bucket count over the match set, derived from an aggregation and
returned on `SearchResponse.facets`. In this project facets describe the BM25
match set under the active filters, not the fused ranking. _Avoid_:
aggregation (that's the Elasticsearch mechanism; a facet is what the response
carries).

**Passage-Based RAG**: passing the highlighted matching snippets to the LLM
rather than whole documents. Falls back to full content when a hit has no
highlights. `search/answering.py:_rag_context()`.

**Reciprocal Rank Fusion (RRF)**: merging two ranked lists by rank rather than
score — `score(doc) = Σ 1/(RRF_RANK_CONSTANT + rank)`. Runs in-process here;
Elasticsearch's native `rrf` retriever is license-gated (ADR-0003).
`search/hybrid_search.py:_reciprocal_rank_fusion()`.

> Keep this lean. Add a term only once it's actually resolved — `/mattpocock-skills:domain-modeling`
> fills this in lazily. Empty glossary is fine for a fresh project.
