---
description: Rebuild and restart the Docker API container with the latest code
---

The `api` Docker container does NOT pick up code changes automatically - it
needs an explicit rebuild. Run:

1. `docker compose up -d --build api`
2. Wait until it reports running/healthy.
3. Check `http://localhost:8000/health` to confirm it responds.
4. Check `git log --oneline -10 -- src/hybrid_search_api/search/index_config.py`
   - if that file changed recently, remind me to delete and reseed the
   Elasticsearch index (see CLAUDE.md) before testing search.
