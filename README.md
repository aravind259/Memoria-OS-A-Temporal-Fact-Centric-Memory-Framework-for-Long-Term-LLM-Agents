# 🧠 AI Memory Operating System

**AI Memory Operating System** is an advanced conversational memory management architecture designed to govern long-term user memory across multi-turn, multi-session interactions. 

> **Architectural Scope Note:**  
> The term *"Operating System"* is employed as an architectural analogy for high-level memory resource allocation, lifecycle scheduling, multi-tier hierarchical caching, compaction/garbage collection, and access control. It does **not** function as or replace a computer operating system kernel, hardware scheduler, or low-level process manager.

---

## 📐 System Architecture

The end-to-end memory pipeline sanitizes, filters, distills, stores, schedules, and retrieves knowledge through dedicated lifecycle stages:

```text
                             USER INPUT
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   PII Sanitization    │ (Redaction of emails, phones, secrets)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Query / Question    │ (Filters transient queries & search questions)
                     │       Filtering       │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │Semantic Classification│ (Fact, Preference, Goal, Project, Skill)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Importance Scoring   │ (0.0 to 1.0 Permanence Estimation)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   LLM Memory Gate     │ (Rejects small talk & ephemeral interactions)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Fact Extraction /   │ (Distills raw turns into atomic 3rd-person assertions)
                     │     Distillation      │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Duplicate Detection & │ (Detects duplicates, reinforces, or records supersession)
                     │     Reconciliation    │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Multimodal Processing │ (Text + image extraction & visual summaries)
                     └───────────┬───────────┘
                                 │
                                 ▼
           ═════════════════════════════════════════════
                         MEMORY HIERARCHY
           ─────────────────────────────────────────────
            [L1] Working Memory (Fast RAM FIFO / Ring Buffer)
                 ▲                ▲
                 │ (Promote)      │ (Restore)
                 ▼                ▼
            [L2] Active Vector Store (ChromaDB Semantic RAM)
                 │
                 │ (Page Out / Decay Sweep)
                 ▼
            [L3] Cold Archive (Persistent SQLite Disk)
           ═════════════════════════════════════════════
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Adaptive Decay Engine │ (Category stability weights + access reinforcement)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Lifecycle Scheduler  │ (Background async loop: stale sweep & archival)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Compaction & Safe GC  │ (Transactional write-to-L3 before L2 slot reclaim)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Persona Synthesis   │ (Compresses active user profile by ~36%)
                     │     & Compression     │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Hybrid RAG Retrieval │
                     │  ├── Dense Vector (45%)
                     │  ├── BM25 Lexical (20%)
                     │  ├── Ebbinghaus (25%) 
                     │  └── Importance  (10%)
                     └───────────┬───────────┘
                                 │
                                 ▼
                            LLM RESPONSE
```

---

## 🗄️ Memory Hierarchy

The system organizes conversational memories into three tiers with distinct latency, capacity, and retention profiles:

1. **L1 — Working Memory (In-Memory RAM Buffer)**:
   - High-speed, in-memory volatile FIFO/ring buffer.
   - Stores active turn-by-turn context, recent assistant interactions, and promoted hot memories.
   - Provides sub-millisecond retrieval for immediate conversational coherence and reference resolution.

2. **L2 — Active Memory (Vector Store / ChromaDB)**:
   - Persistent vector embedding database for active long-term knowledge.
   - Supports dense semantic search, similarity scoring, and identity-scoped querying (`user_id`, `tenant_id`).
   - Serves as the primary operational tier for relevant memories currently retained in the user's active life.

3. **L3 — Cold Archive (Disk Storage / SQLite)**:
   - Structured, indexed relational cold storage.
   - Houses decayed, stale, or superseded historical memories that are no longer actively relevant in L2.
   - Supports full historical query fallbacks and on-demand restoration back to active tiers (L2/L1).

Memories migrate dynamically between tiers according to usage, recency, reinforcement, and lifecycle state.

---

## ✨ Features

### 1. Intelligent Memory Ingestion
- **Semantic Classification**: Maps input assertions into discrete domains (`Fact`, `Preference`, `Goal`, `Project`, `Skill`, and conversational notes).
- **Dynamic Importance Scoring**: Evaluates longevity and significance on a continuous scale ($0.0 \text{ to } 1.0$).
- **LLM Memory Gate**: Employs an intelligent decision gate that rejects chit-chat, ephemeral queries, and temporary interaction noise.
- **Fact Distillation**: Normalizes first-person expressions into atomic, unambiguous third-person statements.
- **Query / Question Rejection**: Prevents user questions and retrieval queries from being incorrectly recorded as permanent facts.

### 2. Duplicate Detection & Reconciliation Lineage
- **Embedding Proximity Matching**: Identifies potential duplicate or conflicting memories across active records.
- **Access Reinforcement**: Strengthens existing memories when identical information is repeated, incrementing access counters and stability.
- **Contradiction & Lineage Versioning**: Resolves evolving facts (e.g., location changes) by marking earlier records as `SUPERSEDED` and linking them directly to the active successor.

### 3. Adaptive Memory Decay
Extends classic exponential forgetting principles with category-specific stability factors and reinforcement dynamics:
- **Category Persistence Weights**:
  - `Preference`: **2.5** (high persistence)
  - `Skill`: **2.2**
  - `Goal`: **1.8**
  - `Project`: **1.5**
  - `Fact`: **1.0** (baseline)
  - `Conversation`: **0.5** (rapid decay)
- **Logarithmic Reinforcement**: Stability scales logarithmically with access frequency ($1 + \ln(1 + \text{AccessCount})$) and positive user validation.
- **Mathematical Foundation**: Retentive probability $R(\Delta t) = \exp(-\Delta t / S_{\text{adaptive}})$, ensuring critical user preferences persist while conversational ephemera decays naturally.

### 4. Memory Lifecycle Scheduler
- **Non-Blocking Background Loop**: Runs periodic maintenance cycles in an asynchronous loop without blocking incoming chat requests.
- **Stale Memory Detection**: Identifies memories whose retention score has decayed below the threshold (`retention < 0.15` with `importance < 0.60`).
- **Important-Memory Protection Rule**: Automatically shields high-value knowledge from cold archival if $\text{importance} \ge 0.65$ or $\text{access count} \ge 2$.
- **Restoration Support**: Supports automated and on-demand reactivation of cold L3 memories into active L2 and L1 tiers.

### 5. Compaction & Garbage Collection
- **Archival-First Transactional Safety**: Enforces strict transactional ordering—records must successfully persist to L3 Cold Archive before corresponding L2 vector slots are reclaimed.
- **Zero Data-Loss Recovery**: If cold archival encounters an error, the active L2 copy is preserved.

### 6. Persona Synthesis & Memory Compression
- **Structured Persona Extraction**: Synthesizes durable user profiles covering identity, location, active projects, and core preferences.
- **Dynamic Context Compression**: Reduces prompt token overhead by **approximately 36%** while maintaining fact preservation and response fidelity.

### 7. Hybrid RAG Retrieval
Combines lexical precision with semantic breadth through multi-factor score interpolation:
- **Hybrid Ranking Formulation**:
  $$\text{Score} = 0.45 \cdot \text{VectorScore} + 0.20 \cdot \text{BM25Score} + 0.25 \cdot \text{DecayScore} + 0.10 \cdot \text{Importance}$$
- **Relevance Filtering**: Drops low-confidence noise before prompt synthesis.

### 8. Conversational Context & Disambiguation
- **Turn History Tracking**: Maintains short-term dialog state for reference resolution and contextual follow-ups.
- **Anaphora Resolution**: Handles incomplete prompts (e.g., following up with *"capital for ?"* after discussing a state).
- **Session Summaries**: Provides contextual synthesis for meta-queries such as *"What were we talking about?"*.

### 9. Privacy, PII Scrubbing & User Isolation
- **Automatic PII Scrubbing**: Identifies and redacts sensitive data (emails, phone numbers, SSNs, credit card numbers, and API keys) prior to persistence.
- **Tenant & User Scoping**: Isolates memories by `user_id` and `tenant_id` at every layer of retrieval and storage.
- **Right-to-Forget**: Provides programmatic memory export and complete deletion mechanisms.

### 10. Multimodal Memory Processing
- Ingests text accompanied by image URLs or base64 payloads, extracting visual summaries and persisting dual-modality memory items.

### 11. Resilience & LLM Model Failover
- Incorporates automatic failover across multiple Gemini model identifiers to maintain continuity when individual endpoints experience rate limits (HTTP 429) or temporary outages.

---

## 🔄 Memory Lifecycle

Every knowledge item progresses through a structured lifecycle managed by the system:

```text
Create ──► Validate ──► Distill ──► Deduplicate / Reconcile ──► Store (L1/L2)
  ▲                                                                   │
  │                                                                   ▼
Restore ◄── Archive (L3) ◄── Compaction / GC ◄── Decay ◄── Reinforce / Retrieve
```

1. **Create & Validate**: Input is scrubbed for PII, inspected for query patterns, and evaluated by the Memory Gate.
2. **Distill & Deduplicate**: The fact is extracted into third-person form and matched against existing memories to reinforce, supersede, or create a new entry.
3. **Store**: Written to L2 ChromaDB and promoted to L1 Working Memory.
4. **Retrieve & Reinforce**: Relevant memories surfaced via Hybrid Search receive access count boosts, slowing future decay.
5. **Decay & Sweep**: Unaccessed, low-importance items decay. The Lifecycle Scheduler identifies items eligible for cold storage.
6. **Archive & Reclaim**: The Compactor commits items to L3 SQLite before freeing L2 vector slots.
7. **Restore**: When a user queries historic knowledge, cold items are promoted back into L2 and L1.

---

## 📊 Hybrid Retrieval Benchmark

Benchmarked against standardized evaluation queries, comparing standalone Dense Vector, standalone BM25 Lexical, and the integrated Hybrid ranker:

| Metric | Vector | BM25 | Hybrid |
| :--- | :---:| :---:| :---:|
| **Hit Rate@1** | 75% | 50% | **88%** |
| **Recall@5** | 100% | 62% | **100%** |
| **Precision@5** | 24% | 25% | **44%** |
| **MRR (Mean Reciprocal Rank)** | 0.88 | 0.56 | **0.94** |
| **Relevance Accuracy** | 80% | 50% | **90%** |

> **Analysis**: The hybrid approach demonstrates superior top-rank accuracy (**88% Hit Rate@1**, **0.94 MRR**) and broader domain recall (**100% Recall@5**). Precision@5 improves substantially over individual baselines to 44%, reflecting intentional retrieval breadth prior to final LLM context gating.

---

## 📈 System Evaluation Results

The system was evaluated using the project's automated verification suite across all core functional domains:

| Evaluation Area | Result |
| :--- | :---:|
| **Memory Ingestion Accuracy** | **100%** |
| **Memory Rejection Accuracy** | **100%** |
| **Duplicate Accuracy** | **100%** |
| **Update Accuracy** | **100%** |
| **Retrieval Recall@5** | **100%** |
| **Retrieval Precision@5** | **44%** |
| **Relevance Accuracy** | **90%** |
| **Tier Retrieval Accuracy** | **100%** |
| **Decay Accuracy** | **100%** |
| **Restoration Accuracy** | **100%** |
| **Compression Effectiveness** | **36%** |
| **Lifecycle Scheduler Accuracy** | **100%** (7/7 tests passed) |
| **Bengaluru Regression Accuracy** | **100%** |
| **Conversation Context Accuracy** | **100%** |

*All metrics derived from the test suite in `tests/run_evaluation.py`.*

---

## 🧪 Key Validated Scenarios

The test suite validates critical real-world interactive behaviors:

1. **User Identity Memory**:
   - *"My name is Aravind"* $\rightarrow$ Extracted and stored; accurately retrieved in subsequent sessions.
2. **Location Evolution & Lineage**:
   - *"I live in Hyderabad"* followed later by *"I moved to Bengaluru last week"* $\rightarrow$ Correctly marks the Hyderabad memory as `SUPERSEDED` and activates Bengaluru.
3. **Current-Location Query**:
   - *"Where do I live now?"* $\rightarrow$ Resolves to Bengaluru, suppressing outdated superseded facts.
4. **General Knowledge Isolation**:
   - *"What is the capital of India?"* $\rightarrow$ Answered using general reasoning without contaminating or confusing personal memory records.
5. **Contextual Follow-up & Anaphora**:
   - Discussing Telangana $\rightarrow$ followed by *"capital for ?"* $\rightarrow$ Resolves to Hyderabad.
   - Discussing Karnataka $\rightarrow$ followed by *"capital for ?"* $\rightarrow$ Resolves to Bengaluru.
6. **Temporary Interaction Filtering**:
   - Ephemeral queries and temporary travel requests are answered in conversation without being persisted to long-term memory.

---

## 🚀 Quick Start & Usage

### 1. Environment Activation
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Start Web Server
```powershell
$env:PYTHONPATH='C:\Users\Aravi\OneDrive\Desktop\major'
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser to interact with the web dashboard.

### 3. Run Verification & Evaluation

- **Comprehensive Evaluation Suite (All Evaluators)**:
  ```powershell
  $env:PYTHONPATH='C:\Users\Aravi\OneDrive\Desktop\major'
  .\.venv\Scripts\python.exe tests\run_evaluation.py
  ```

- **Basic Smoke Verification**:
  ```powershell
  $env:PYTHONPATH='C:\Users\Aravi\OneDrive\Desktop\major'
  .\.venv\Scripts\python.exe test_memory.py
  ```

---

## 📂 Project Structure

```text
major/
├── app/
│   ├── api/                  # FastAPI router endpoints & schemas
│   ├── core/                 # Configuration, settings, and dependency container
│   ├── embeddings/           # Embedding encoders (SentenceTransformers / local)
│   ├── llm/                  # LLM clients and multi-model failover chains
│   ├── memory/               # Core memory operating system components
│   │   ├── adaptive_decay.py # Category-weighted Ebbinghaus retention engine
│   │   ├── archive_storage.py# L3 Cold Storage SQLite interface
│   │   ├── bm25.py           # BM25 lexical retrieval engine
│   │   ├── chroma.py         # L2 ChromaDB vector store interface
│   │   ├── classifier.py     # Semantic category classifier
│   │   ├── compactor.py      # OS memory compactor & safe garbage collector
│   │   ├── duplicate.py      # Embedding-based duplicate detector
│   │   ├── extractor.py      # Third-person atomic fact distillation
│   │   ├── gate.py           # LLM memory gate filter
│   │   ├── importance.py     # Permanence scoring heuristic
│   │   ├── manager.py        # Top-level memory coordinator
│   │   ├── multimodal.py     # Multimodal processor for image & text memories
│   │   ├── persona.py        # Persona synthesizer & prompt context compressor
│   │   ├── pii.py            # PII scrubber and redaction filter
│   │   ├── ranker.py         # 4-factor hybrid reranking engine
│   │   ├── reconciler.py     # Contradiction, lineage, and supersession logic
│   │   ├── retriever.py      # Dense + lexical hybrid retriever
│   │   ├── scheduler.py      # Background async lifecycle scheduler
│   │   ├── storage.py        # Integrated ingestion & storage pipeline
│   │   ├── tier_manager.py   # Multi-tier memory movement (L1, L2, L3)
│   │   └── working_memory.py # L1 RAM fast buffer & conversational context
│   └── main.py               # FastAPI application entry point
├── static/                   # Web UI dashboard frontend assets
├── tests/                    # Automated benchmark evaluation suite
│   ├── evaluators/           # Domain-specific test evaluators
│   └── run_evaluation.py     # Master benchmark execution runner
├── patent_specification.md   # Patent application specification and claims
├── test_memory.py            # Basic smoke verification script
└── README.md                 # Project documentation
```

---

## 📑 Patent Documentation

Complete patent application specification, technical architecture descriptions, and claims are available in [patent_specification.md](file:///c:/Users/Aravi/OneDrive/Desktop/major/patent_specification.md).
