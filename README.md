# LLMRoute 0.4.0 — Complete local development edition

Full backend and chalkboard-style Next.js frontend. No existing source files or Git repository required. Extract the entire archive into a NEW directory (e.g. Desktop\LLMRoute_Complete), never over the old LLMRoute project. The archive contains no credentials, model weights, node_modules, virtual environment, or database records.

## Windows setup
Prerequisites: Python 3.12–3.14 with package wheels available, Node.js 20.9+ (22 LTS recommended), Docker Desktop running, Ollama running. Stop previous LLMRoute Uvicorn/Next.js servers to free ports 8001 and 3005. Do not delete any old database volumes.

From the extracted directory in PowerShell:

```
powershell -ExecutionPolicy Bypass -File .\Setup.ps1 -ReuseExistingDb -SkipModels
```

Use this command for the original llmroute-db container at 5433 with the previously downloaded models (verify `ollama list` includes 1.5b, 3b, 7b and all-minilm:22m). The script recovers its password locally, applies additive schema statements, and keeps existing data. For a fresh isolated DB instead, run `powershell -ExecutionPolicy Bypass -File .\Setup.ps1` (new container and volume, port 5434). Fresh setup does not stop the old DB; stop it manually if necessary to free memory. Do not switch database modes in the same extracted directory without updating backend/.env. Existing env files are preserved.

Two separate terminals, both in the extracted directory:

```
powershell -ExecutionPolicy Bypass -File .\Start-Backend.ps1
powershell -ExecutionPolicy Bypass -File .\Start-Frontend.ps1
```

Open http://127.0.0.1:3005. Swagger: http://127.0.0.1:8001/docs. DB health: http://127.0.0.1:8001/health/db. Ollama health: http://127.0.0.1:8001/health/ollama.

## Features
- Persistent exact and semantic query caching, expiration, mode/budget isolation, heuristic safeguards.
- Three-tier Qwen routing, RAM checks, estimated per-request budget, hypothetical cost analytics.
- PDF/TXT/MD extraction, overlapping chunks, vector and lexical ranking, document-scoped RAG.
- RAG exact cache before embedding, semantic cache only with matching evidence, optional cache bypass, citation ID validation.
- Shared inference lock for chat, RAG and ingestion. Chalkboard playground, document library and analytics console.

## Verification and limitations
Run backend tests using `.venv\Scripts\python.exe -m pytest tests -q` from backend; frontend build using `npm.cmd run build` from frontend. The setup script runs backend unit tests and a real DB connection test. Test with a sample PDF or TXT and repeat a question to verify cache behavior. No actual API billing; prices are illustrative. Budget is an estimate, not a strict maximum. Cache similarity and citation IDs do not establish truth. RAG may abstain incorrectly or hallucinate; scanned PDFs are unsupported. The local-only API has no authentication; do not expose it publicly. Historical metrics omit failures and some abstentions. Old general cache namespaces may not be reused, but historical records are retained. Raw questions and document content are stored in PostgreSQL. This is a development edition, not a production-security release.
