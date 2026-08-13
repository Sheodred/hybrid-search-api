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

> Keep this lean. Add a term only once it's actually resolved — `/mattpocock-skills:domain-modeling`
> fills this in lazily. Empty glossary is fine for a fresh project.
