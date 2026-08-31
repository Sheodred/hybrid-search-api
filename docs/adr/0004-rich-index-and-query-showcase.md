# ADR-0004: A deliberately broad index mapping and query DSL

## Context

Before this change the search layer was three fields (`title`, `content`,
`embedding`), one custom analyzer, one `multi_match`, and one flat `knn`. It
worked. For a service that only had to answer "find me documents about X",
it was the right amount of code, and a reviewer optimizing for simplicity
would leave it alone.

But the project's stated purpose is to demonstrate Elasticsearch competence
for specialist roles, and the previous mapping demonstrated roughly two
concepts. There was also a concrete defect: the only custom analyzer was
**German** (`light_german`, `_german_` stopwords) while every seeded
document - the curated demo set and NFCorpus alike - is **English**. Stemming
English text with a German stemmer is close to not stemming it at all.

## Decision

Broaden the mapping and the query DSL to cover the concepts that actually
matter for hybrid search and RAG, and make each one observable rather than
decorative:

- Every concept is **exercised by a test** asserting its structural
  invariant, not merely present in a dict.
- Every builder is **rendered to `docs/search/*.json`** by
  `tests/test_config_snapshots.py` and explained in `docs/search/README.md` -
  what it shows, which mapping field makes it work, what to try changing.
- Filters, highlighting and facets are **wired into the running `/search`
  path** (new request/response fields), not left as reference material.
  `function_score` recency decay is the one deliberate exception, marked
  reference-only in its docstring and in the docs.

The analyzer chain moves to English in the same change, since the mapping was
being rewritten anyway and leaving a German stemmer on English text would
have made every retrieval-quality observation meaningless.

## Consequences

- **The mapping is `dynamic: strict`.** A document carrying an undeclared
  field is rejected rather than silently mapped. This is what makes the
  seed scripts trustworthy: a typo fails at index time instead of creating a
  phantom field. It also means every mapping change needs
  `python scripts/seed_data.py --recreate` - `ensure_index()` only creates a
  missing index, it never updates one.
- **NFCorpus documents are sparser than demo documents.** The BEIR rows carry
  `_id`, `title`, `text` and a `metadata.url`; there are no MeSH terms and no
  publication dates, so `tags` and `published` are simply absent there.
  `dynamic: strict` rejects *unknown* fields, not missing known ones, so both
  corpora validate against the same mapping - and the sparser one proves the
  mapping holds at ~3.6K documents.
- **Facet counts describe the BM25 match set, not the fused ranking.**
  Aggregations ride on the BM25 call only; computing them on the kNN call too
  would produce a second bucket set to reconcile for no real gain. Both calls
  share the same filter context, so the counts are well-defined - just scoped
  to the lexical half. Stated in `docs/search/README.md` rather than
  engineered around.
- **RAG context is now passage-based.** When highlighting produced snippets,
  those go to the LLM instead of full documents. Fewer tokens and better
  focus; hits found only by the vector side have no snippet and fall back to
  full content.
- **`_reciprocal_rank_fusion` had to start merging instead of overwriting.**
  It walked each ranked list assigning `docs[doc_id] = hit`, so a document
  present in both lists ended up holding the kNN copy - which carries no
  `highlight`, because only the BM25 call requests one. Every document
  ranking well on both sides, precisely the ones RRF promotes, would have
  silently lost its snippet. Now covered by a regression test.
- **Two demo-scenario values are tuned to this corpus, not round numbers.**
  The rendered filter example uses `min_word_count: 30` because the demo
  documents run 30-38 words, and a threshold of 40 would make every filtered
  example return zero hits. The `gauss` decay uses `scale: 730d` because at a
  more typical `180d` every document in a 2023-2025 corpus decays to
  effectively zero. Both were caught by actually running the examples.
- This is deliberately more configuration than a minimal service needs. That
  is the requirement here, not gold-plating - a later reader, or a
  simplification pass, should read this ADR before "cleaning it up".

## Not done

No autocomplete/completion suggester, `rank_features`, percolator, runtime
fields, or `search_after`/`collapse`/`_explain`. Those are a broad feature
tour rather than the hybrid-search + RAG story this project tells.

No live Elasticsearch in CI. Validation is three layers - snapshots,
structural invariants on builder output, and response parsing against
hand-built fixtures with a mocked client. `scripts/run_examples.py` is the
manual confirmation that a real cluster accepts the bodies.

The native `rrf` retriever remains unavailable - it is license-gated. See
[ADR-0003](0003-elasticsearch-9-upgrade.md).
