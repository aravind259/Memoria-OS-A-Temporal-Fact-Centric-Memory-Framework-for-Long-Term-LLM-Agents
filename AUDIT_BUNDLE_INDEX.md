# AUDIT_BUNDLE_INDEX.md
# Memoria – Agentic Memory Operating System
## Complete Project Audit Bundle Index

**Generated:** 2026-11-08  
**Prepared for:** External Technical Review  
**Bundle Name:** `MEMORIA_COMPLETE_AUDIT_BUNDLE.zip`

---

## 1. Project Name and Purpose

**Project:** Memoria – Agentic Memory Operating System  
**Version:** V1 (eval-passed) + V2 (active development)  
**Short Description:**  
Memoria is an agentic, persistent memory layer for LLM-powered conversational AI. It ingests user conversations, extracts structured facts, reconciles them against existing knowledge, manages their lifecycle through tiered storage with decay and archival, and retrieves semantically and lexically relevant context at query time. The goal is to give AI assistants persistent, updateable, and relevance-ranked long-term memory.

**Research Reference:**  
The system references and extends concepts from the Memoria paper (Sarin et al., AIMLSystems 2025) and was benchmarked against LongMemEval.

---

## 2. Repository Folder Structure

```
major/                              ← Project root
├── app/                            ← Primary application package (V1 + V2)
│   ├── api/                        ← FastAPI route handlers
│   ├── core/                       ← Configuration, DI container, clock, metrics
│   ├── db/                         ← SQLAlchemy database layer
│   ├── embeddings/                 ← Sentence embedding encoder
│   ├── llm/                        ← Gemini LLM client + prompt dispatch
│   ├── memory/                     ← V1 memory engine (all core modules)
│   ├── memory_v2/                  ← V2 memory engine (fact-centric)
│   ├── models/                     ← (empty – reserved for Pydantic/ORM models)
│   ├── services/                   ← High-level orchestration services
│   └── main.py                     ← FastAPI application entry point
├── backups/
│   └── v1.0_eval_passed/           ← Frozen V1 snapshot that passed 100% eval
├── bench/                          ← LongMemEval benchmark harness
│   ├── systems/                    ← System adapters (v1, v2, memoria, full_context)
│   ├── data/                       ← LongMemEval dataset (longmemeval_s.json, 278 MB)
│   ├── results/                    ← JSONL result files per system
│   ├── judge.py                    ← LLM-as-judge evaluation logic
│   ├── longmemeval.py              ← Dataset loader and question iterator
│   ├── report.py                   ← Results reporting and CI computation
│   ├── run.py                      ← Benchmark entrypoint
│   ├── sample_ids.json             ← 30-question pilot sample IDs
│   ├── verify_extraction.py        ← Extraction verification utility
│   └── RESULTS.md                  ← Benchmark result report
├── Project_Documentation/          ← Full project documentation suite
│   ├── DOCUMENTATION.md            ← 124 KB comprehensive technical documentation
│   ├── Memoria_Documentation.docx  ← Word export
│   ├── Memoria_Documentation.pdf   ← PDF export
│   ├── chapters_1_to_7.py          ← Doc generation scripts (chapters 1–7)
│   ├── chapters_8_to_14.py         ← Doc generation scripts (chapters 8–14)
│   ├── chapters_15_to_20.py        ← Doc generation scripts (chapters 15–20)
│   ├── chapters_21_to_25.py        ← Doc generation scripts (chapters 21–25)
│   ├── build_all_docs.py           ← Master doc builder
│   ├── build_docx.py               ← DOCX builder
│   ├── build_pdf.py                ← PDF builder
│   └── generate_doc_text.py        ← Text-extraction utility
├── static/
│   └── index.html                  ← Single-page frontend UI (chat interface)
├── tests/
│   ├── evaluators/                 ← Named regression and integration evaluators
│   ├── dataset.py                  ← Evaluation dataset definitions
│   ├── run_evaluation.py           ← Evaluation runner (V1 + V2)
│   ├── test_v2_facts.py            ← V2 fact extraction/retrieval unit tests
│   └── __init__.py
├── scratch/
│   └── clean_cache.py              ← Utility to clean LLM cache DB
├── .env.example                    ← Environment variable template (safe to share)
├── .gitignore                      ← Git ignore rules
├── CHECKPOINT_V1_EVAL_PASSED.md    ← V1 evaluation milestone record
├── patent_specification.md         ← Patent specification draft
├── README.md                       ← Project README
├── requirements.txt                ← Python dependency lockfile (derived from .venv)
├── test_memory.py                  ← Root-level ad-hoc memory test script
├── memoria.db                      ← SQLite: early/prototype database
├── memory_os.db                    ← SQLite: V1 primary runtime database
├── memory_os_archive.db            ← SQLite: V1 archive database
├── memory_os_v2.db                 ← SQLite: V2 primary runtime database
├── test_facts_v2.db                ← SQLite: V2 test facts database
├── llm_cache.db                    ← SQLite: LLM response cache (1 MB)
└── memory_db/                      ← ChromaDB vector store (HNSW binary files)
```

---

## 3. Explanation of Each Major Directory

| Directory | Role |
|-----------|------|
| `app/` | Main Python package. All runtime application code lives here. |
| `app/api/` | FastAPI routers: `chat.py` (chat endpoint) and `memory.py` (CRUD + search endpoints). |
| `app/core/` | Cross-cutting concerns: `config.py` (env-based settings), `container.py` (dependency-injection-style singletons, scheduler wiring), `clock.py` (time abstraction for testability), `metrics.py` (simple counters/timers). |
| `app/db/` | SQLAlchemy engine (`database.py`) and ORM models (`models.py`). |
| `app/embeddings/` | Thin wrapper around `sentence-transformers` encoder for dense vector generation. |
| `app/llm/` | Gemini API client (`gemini.py`) with structured prompt templates, retry logic, response parsing, and optional LLM caching. |
| `app/memory/` | V1 memory engine: all lifecycle, retrieval, storage, ranking, decay and classification modules. |
| `app/memory_v2/` | V2 memory engine: fact-centric redesign with separate extract/write/retrieve phases. |
| `app/models/` | Reserved directory (currently empty). |
| `app/services/` | Thin orchestration: `conversation.py` (conversation context handler), `llm.py` (LLM service shim). |
| `backups/v1.0_eval_passed/` | Complete frozen snapshot of V1 at the point all 32 evaluator tests passed. |
| `bench/` | LongMemEval benchmark harness comparing system variants (v1, v2, memoria, full_context). |
| `bench/systems/` | System adapters wrapping each memory variant for uniform benchmark interface. |
| `bench/results/` | JSONL raw output per system run. |
| `Project_Documentation/` | Comprehensive documentation suite (Markdown, DOCX, PDF) plus doc-generation scripts. |
| `static/` | Single-page web frontend (HTML/JS/CSS). Served by FastAPI at `/`. |
| `tests/` | Evaluation and test suite for V1 and V2. |
| `tests/evaluators/` | Named regression test modules covering specific behaviors. |
| `scratch/` | Utility scripts not part of the main application. |
| `memory_db/` | ChromaDB persistent vector store (HNSW index binary files + SQLite metadata). |

---

## 4. V1 vs V2 Module Identification

### V1 – `app/memory/` (Holistic memory object store)
Coordinates retrieval across BM25, vector, and hybrid pipelines. Full lifecycle management.

| Module | Description |
|--------|-------------|
| `storage.py` | SQLite-backed persistent memory record store |
| `chroma.py` | ChromaDB vector store integration |
| `retriever.py` | Hybrid retrieval orchestrator (vector + BM25) |
| `bm25.py` | BM25 keyword search implementation |
| `ranker.py` | Multi-signal result re-ranking (recency, importance, tier) |
| `classifier.py` | Memory type classifier (episodic / semantic / procedural / emotional) |
| `reclassify.py` | Post-storage reclassification logic |
| `duplicate.py` | Near-duplicate detection and deduplication |
| `reconciler.py` | Fact reconciliation and conflict resolution |
| `decay.py` | Exponential decay scoring |
| `adaptive_decay.py` | Adaptive decay with interaction-based restoration |
| `tier_manager.py` | Hot/warm/cold tier promotion and demotion |
| `scheduler.py` | Background lifecycle scheduler (runs decay, tier, archive jobs) |
| `compactor.py` | Persona/memory compaction for context windows |
| `persona.py` | User persona extraction and management |
| `working_memory.py` | Short-term working memory buffer |
| `archive_storage.py` | Cold archive storage (separate SQLite DB) |
| `extractor.py` | LLM-driven fact/memory extraction from conversations |
| `gate.py` | Memory ingestion gate (relevance filter) |
| `importance.py` | Importance scoring |
| `pii.py` | PII detection and redaction |
| `multimodal.py` | Multimodal memory support (stub/experimental) |
| `prompt.py` | Prompt templates for memory-augmented generation |
| `manager.py` | Top-level V1 memory manager (coordinates all modules) |

### V2 – `app/memory_v2/` (Fact-centric design)
Redesigned around atomic `(entity, attribute, value, valid_from, valid_until)` facts.

| Module | Description |
|--------|-------------|
| `facts.py` | Fact schema definition and SQLite fact table interface |
| `extract.py` | LLM-driven fact extraction from conversations → structured facts |
| `write.py` | Fact write path: upsert, conflict resolution, temporal reconciliation |
| `retrieve.py` | Fact retrieval: semantic + keyword search, temporal filtering, ranking |
| `__init__.py` | Package init; exposes `MemoryV2` convenience class |

### V1 Backup Snapshot
- Located at: `backups/v1.0_eval_passed/`
- State: Frozen at September 9, 2026, all 32 evaluator tests passing.

### Benchmark System Adapters
- `bench/systems/v1.py` – V1 adapter
- `bench/systems/v2.py` – V2 adapter
- `bench/systems/memoria.py` – Memoria paper reimplementation adapter
- `bench/systems/full_context.py` – Full-context baseline

---

## 5. Main Application Entry Points

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application factory. Mounts routers, starts/stops lifecycle scheduler, serves static frontend. Run with: `uvicorn app.main:app --reload` |
| `tests/run_evaluation.py` | Evaluation runner. Executes all test evaluators in `tests/evaluators/`. |
| `bench/run.py` | LongMemEval benchmark runner. Accepts system name and sample config. |
| `test_memory.py` | Root-level ad-hoc integration test script. |

---

## 6. Important APIs and Services

### REST API Endpoints (FastAPI)

**Chat API** – `app/api/chat.py`
- `POST /chat` – Send a user message; retrieves memory context, generates LLM response, ingests new memories.

**Memory API** – `app/api/memory.py`
- `GET /memories` – List all memories (with optional filters)
- `POST /memories` – Manual memory ingestion
- `GET /memories/search` – Search memories by query
- `DELETE /memories/{id}` – Delete a memory
- `GET /persona` – Retrieve user persona summary
- `GET /health` – Health check (`app/main.py`)

### Internal Services
- **Lifecycle Scheduler** (`app/memory/scheduler.py`, wired in `app/core/container.py`): Background thread that periodically runs decay scoring, tier promotion/demotion, and archival.
- **Gemini LLM Client** (`app/llm/gemini.py`): Wraps Google Generative AI SDK with structured prompt dispatch, response parsing, caching, and retry logic.
- **ChromaDB Vector Store** (`app/memory/chroma.py`): Manages HNSW vector index for semantic similarity search.

---

## 7. Database Technologies and Schema Locations

| Database | Technology | Purpose | Schema Location |
|----------|-----------|---------|----------------|
| `memory_os_v2.db` | SQLite (SQLAlchemy) | V2 primary runtime (facts table) | `app/memory_v2/facts.py`, `app/db/models.py` |
| `memory_os.db` | SQLite (SQLAlchemy) | V1 primary runtime (memory records) | `app/db/models.py` |
| `memory_os_archive.db` | SQLite | V1 cold archive storage | `app/memory/archive_storage.py` |
| `memoria.db` | SQLite | Early/prototype schema | (legacy) |
| `test_facts_v2.db` | SQLite | V2 test facts database | `tests/test_v2_facts.py` |
| `llm_cache.db` | SQLite | LLM response cache | `app/llm/gemini.py` |
| `memory_db/` | ChromaDB (HNSW + SQLite) | Vector embeddings store | `app/memory/chroma.py` |

No database migrations framework is in use. Schemas are created programmatically via SQLAlchemy `create_all()` and ChromaDB collection initialization.

---

## 8. Retrieval and Memory Lifecycle Components

### Retrieval Pipeline (V1)
1. **Query embedding** → `app/embeddings/encoder.py`
2. **Vector search** → `app/memory/chroma.py` (ChromaDB HNSW)
3. **BM25 keyword search** → `app/memory/bm25.py`
4. **Hybrid fusion** → `app/memory/retriever.py`
5. **Re-ranking** → `app/memory/ranker.py` (recency, importance, tier, relevance signals)

### Retrieval Pipeline (V2)
1. **Fact embedding + semantic search** → `app/memory_v2/retrieve.py`
2. **Keyword search over fact store** → `app/memory_v2/retrieve.py`
3. **Temporal filtering** (valid_from / valid_until ranges)
4. **Ranked fact list** returned to chat handler

### Memory Lifecycle (V1)
- **Ingestion** → `app/memory/gate.py` (relevance gate) → `app/memory/extractor.py` → `app/memory/duplicate.py` → `app/memory/reconciler.py` → `app/memory/storage.py`
- **Classification** → `app/memory/classifier.py` (episodic/semantic/procedural/emotional)
- **Importance Scoring** → `app/memory/importance.py`
- **Decay** → `app/memory/decay.py` (base) + `app/memory/adaptive_decay.py` (adaptive)
- **Tier Management** → `app/memory/tier_manager.py` (hot/warm/cold)
- **Archival** → `app/memory/archive_storage.py`
- **Compaction** → `app/memory/compactor.py`
- **Background Scheduling** → `app/memory/scheduler.py`

### Memory Lifecycle (V2)
- **Extraction** → `app/memory_v2/extract.py` (LLM extracts atomic facts from conversation turn)
- **Write / Reconcile** → `app/memory_v2/write.py` (temporal conflict resolution, upsert)
- **Retrieval** → `app/memory_v2/retrieve.py`

---

## 9. Benchmark and Testing Locations

### Evaluation Suite (V1 + V2)
| File | Tests |
|------|-------|
| `tests/run_evaluation.py` | Master runner; executes all evaluators |
| `tests/dataset.py` | Shared synthetic evaluation dataset |
| `tests/test_v2_facts.py` | V2 fact extraction + retrieval unit tests (untracked) |
| `tests/evaluators/test_e2e_chat.py` | End-to-end chat flow |
| `tests/evaluators/test_ingestion_rejection.py` | Ingestion gate accept/reject logic |
| `tests/evaluators/test_persona_compression.py` | Persona compaction quality |
| `tests/evaluators/test_retrieval_performance.py` | Vector/BM25/Hybrid retrieval metrics |
| `tests/evaluators/test_tiers_decay.py` | Tier transitions and decay scoring |
| `tests/evaluators/test_bengaluru_regression.py` | City-based regression (entity resolution) |
| `tests/evaluators/test_chennai_reconciliation_regression.py` | Reconciliation regression test |
| `tests/evaluators/test_conversation_context.py` | Conversation context injection |
| `tests/evaluators/test_lifecycle_scheduler.py` | Background scheduler behavior |
| `tests/evaluators/test_memory_classification.py` | Memory type classification accuracy |

### Benchmark Suite (LongMemEval)
| File | Role |
|------|------|
| `bench/run.py` | Main benchmark runner |
| `bench/longmemeval.py` | Dataset loader |
| `bench/judge.py` | LLM-as-judge evaluation |
| `bench/report.py` | Results analysis and CI computation |
| `bench/systems/v1.py` | V1 system adapter |
| `bench/systems/v2.py` | V2 system adapter |
| `bench/systems/memoria.py` | Memoria paper reimplementation |
| `bench/systems/full_context.py` | Full-context baseline |
| `bench/results/v1.jsonl` | V1 benchmark results (83 KB) |
| `bench/results/v2.jsonl` | V2 benchmark results (23 KB) |
| `bench/results/memoria.jsonl` | Memoria adapter results (135 KB) |
| `bench/results/full_context.jsonl` | Full-context baseline results (1.2 KB) |
| `bench/RESULTS.md` | Human-readable benchmark report |

**V1 Evaluation Results (from CHECKPOINT_V1_EVAL_PASSED.md):**
- Memory Ingestion/Rejection/Duplicate/Update Accuracy: 100%
- Retrieval Recall@5: 100%, Precision@5: 94%, MRR: 1.00
- Hybrid Hit Rate@1: 100%

---

## 10. Dependency and Execution Instructions

### Prerequisites
- Python 3.12+ (project uses Python 3.14 based on `.pyc` naming)
- A Google Gemini API key

### Setup
```bash
# 1. Clone / extract repository
cd major/

# 2. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_actual_key
```

### Running the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Frontend available at: http://localhost:8000
# API docs at:           http://localhost:8000/docs
```

### Running Tests
```bash
python -m pytest tests/ -v
# Or run the evaluation runner directly:
python tests/run_evaluation.py
```

### Running Benchmarks
```bash
# Run v2 system on pilot sample
python bench/run.py --system v2 --sample bench/sample_ids.json

# Generate report from existing results
python bench/report.py
```

---

## 11. Files Intentionally Excluded

| Excluded Item | Reason |
|--------------|--------|
| `.venv/` | Python virtual environment – reviewer creates their own |
| `__pycache__/` | Compiled Python bytecode – not source code |
| `app/api/__init__.py/chat.cpython-314.pyc` | Python bytecode artifact inside misnamed directory |
| `app/llm/__init__.py/gemini.cpython-314.pyc` | Python bytecode artifact |
| `app/core/__init__.py/config.cpython-314.pyc` | Python bytecode artifact |
| `app/models/` | Empty directory – nothing to include |
| `backend/` | Empty directory – nothing to include |
| `.env` (root) | Contains real `GEMINI_API_KEY` credential |
| `app/llm/.env` | Contains real `GEMINI_API_KEY` credential |
| `backups/v1.0_eval_passed/app/llm/.env` | Contains real `GEMINI_API_KEY` credential |
| `bench/data/longmemeval_s.json` | 278 MB dataset file – too large; download from LongMemEval authors |
| `bench/data/longmemeval_s` (dir) | Same 278 MB dataset – excluded for size |
| `memory_db/` (binary files) | ChromaDB HNSW binary vector index – runtime artifact, not source |
| `memoria.db` | Prototype/legacy SQLite runtime DB – not schema source |
| `memory_os.db` | V1 runtime SQLite DB – contains user/runtime data |
| `memory_os_archive.db` | V1 archive runtime DB – contains user/runtime data |
| `llm_cache.db` | LLM response cache – contains generated content, not source |
| `node_modules/` | Not present in this project |
| `.pytest_cache/` | Pytest cache – not source code |

> **Note on runtime databases:** `memory_os_v2.db` and `test_facts_v2.db` are small (20–340 KB) and included as they contain representative V2 fact schemas and synthetic test data.

---

## 12. Known Incomplete or Experimental Modules

| Module | Status | Notes |
|--------|--------|-------|
| `app/memory/multimodal.py` | Experimental | Multimodal memory stub; not wired into main pipeline |
| `app/models/` | Empty | Reserved for Pydantic request/response schemas; not yet populated |
| `backend/` | Empty | Reserved directory; no content yet |
| `app/memory_v2/` | Active development | V2 is functional but under active iteration; not all V1 features ported |
| `bench/systems/v2.py` | Partial results | V2-no-decay and V2-memoria-decay variants show 0.0s / N/A in RESULTS.md, indicating incomplete run |
| `app/memory/reclassify.py` | Experimental | Post-ingestion reclassification; integration status unclear |
| `Project_Documentation/*.py` | Build scripts | Used to generate documentation; not part of runtime |
| `scratch/clean_cache.py` | Utility | Ad-hoc cache-cleaning script; not part of main application |

---

## 13. Git Branch and Latest Commit Hash

| Property | Value |
|----------|-------|
| Branch | `master` |
| Latest Commit Hash | `eb67b14adf39d35b4dc7b1c0f0a4678834118b2e` |
| Latest Commit Message | `pre-v2` |
| Previous Commit | `b962eef` – `Checkpoint v1.0: Evaluation suite passing 32/32 tests with 100% Hybrid HR@1, Recall@5, Relevance Acc, 94% Precision@5, 1.00 MRR` |
| Tagged Version | `v1.0-eval-passed` (references b962eef) |

---

## 14. Uncommitted and Untracked Source Files Included in This Package

The following files are present in the repository directory but have NOT been committed to git. They are included in this audit bundle because they are part of the current implementation.

### Modified (tracked files with uncommitted changes):
| File | Description |
|------|-------------|
| `app/llm/gemini.py` | LLM client – modified since last commit (pre-v2 work) |
| `app/memory/adaptive_decay.py` | Adaptive decay – modified since last commit |
| `app/memory/archive_storage.py` | Archive storage – modified since last commit |
| `app/memory/chroma.py` | ChromaDB integration – modified since last commit |
| `app/memory/decay.py` | Base decay – modified since last commit |
| `app/memory/ranker.py` | Ranker – modified since last commit |
| `app/memory/retriever.py` | Retriever – modified since last commit |
| `app/memory/scheduler.py` | Lifecycle scheduler – modified since last commit |
| `app/memory/tier_manager.py` | Tier manager – modified since last commit |
| `app/memory/working_memory.py` | Working memory – modified since last commit |
| `tests/run_evaluation.py` | Evaluation runner – modified since last commit |

### Untracked (new files not yet added to git):
| File/Directory | Description |
|----------------|-------------|
| `Project_Documentation/` | Full documentation suite (added after last commit) |
| `app/core/clock.py` | Time abstraction module (new, untracked) |
| `app/core/metrics.py` | Metrics module (new, untracked) |
| `app/memory_v2/` | Entire V2 memory engine (new, untracked) |
| `bench/` | Entire benchmark harness (new, untracked) |
| `scratch/` | Utility scripts (new, untracked) |
| `tests/test_v2_facts.py` | V2 fact tests (new, untracked) |

---

## Secrets and Security Notes

- **Two `.env` files were detected** containing real `GEMINI_API_KEY` credentials:
  - `.env` (project root)
  - `app/llm/.env`
  - `backups/v1.0_eval_passed/app/llm/.env`
- **All three are EXCLUDED** from this audit bundle.
- Sanitized `.env.example` files with placeholder values are included instead.
- No hardcoded API keys were detected inside Python source files. The key is loaded via `os.getenv()` / `python-dotenv`.

---

*This index was derived from actual source code inspection. No implementation details were invented.*
