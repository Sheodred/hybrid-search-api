# hybrid-search-api

Portfolio-Projekt fuer Bewerbungen (Backend + KI-Integration + Elasticsearch-
Spezialist). Elasticsearch Hybrid Search (BM25 + kNN via RRF) mit einer
LLM-Schicht fuer RAG-Antworten. Siehe README.md und docs/architecture.md fuer
Architektur/Setup - bitte vor groesseren Aenderungen lesen.

## Stack
- Python 3.11+ (lokal getestet auf 3.14), FastAPI, Elasticsearch 8.x
- LLM ueber OpenAI-kompatiblen Endpunkt (LLM_* Env-Vars in .env) - kein
  direkter Anthropic-API-Call
- Docker Compose fuer Elasticsearch + API-Container
- Windows/PowerShell als primaere Dev-Umgebung

## Bekannte Stolperer (bitte nicht wiederholen)
- venv gilt nur pro Terminal-Sitzung - vor jedem Befehl pruefen, ob `(.venv)`
  im Prompt steht, sonst `.\.venv\Scripts\Activate.ps1`.
- Der Docker-Container zieht Code-Aenderungen NICHT automatisch - nach jeder
  Aenderung `docker compose up -d --build api`, sonst laeuft der alte Stand
  unbemerkt weiter.
- Nach Aenderungen an `search/index_config.py` (Analyzer/Mapping) muss der
  ES-Index geloescht und neu geseedet werden, sonst greift die neue Mapping
  nicht:
  `Invoke-RestMethod -Method Delete -Uri http://localhost:9200/documents`
  dann `python scripts/seed_data.py`.
- PowerShell: `Invoke-RestMethod` verwenden, nicht curl-Syntax.
- Git-Autor durchgaengig "Adrian K. <92444350+Sheodred@users.noreply.github.com>".
- Vor jedem `git push`: kurz `git log --oneline -5` und `git status` pruefen,
  ob die lokale History wirklich linear zum Remote steht (einmal gab es eine
  Divergenz durch parallele Copilot-Commits).

## Nuetzliche Commands
- `/verify` - Tests + Lint lokal durchlaufen lassen
- `/rebuild` - Docker-API-Container mit aktuellem Code neu bauen
