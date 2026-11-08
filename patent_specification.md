# PATENT SPECIFICATION DOCUMENT

**TITLE OF INVENTION:**
SYSTEM AND METHOD FOR ADAPTIVE MULTI-TIERED CONVERSATIONAL MEMORY WITH DYNAMIC EBBINGHAUS DECAY, AUTOMATED CONTRADICTION RESOLUTION, AND HYBRID RAG RETRIEVAL

---

## ABSTRACT

An intelligent artificial intelligence memory operating system architecture for conversational agents comprises a dynamic, multi-tiered software memory pipeline. The system receives natural language user utterances, classifies semantic category and temporal permanence, filters ephemeral conversational noise via a Large Language Model (LLM) memory gate, extracts atomic factual assertions, and reconciles incoming knowledge against existing representations. Incoming facts that update or contradict prior knowledge trigger atomic lineage versioning (`SUPERSEDED` vs `ACTIVE` states). 

The memory storage is structured across a three-tier hierarchy comprising: (i) an in-memory Level-1 (L1) Working Memory FIFO buffer for immediate turn context; (ii) a persistent Level-2 (L2) Active Vector Store (ChromaDB) for dense semantic retrieval; and (iii) a Level-3 (L3) Cold Archive (SQLite disk database) for long-term retention of decayed, stale, or superseded historical memories. An asynchronous background Lifecycle Scheduler executes periodic sweeps to detect stale memories using an adaptive Ebbinghaus retention decay engine scaled by category persistence weights and logarithmic access reinforcement, while enforcing an important-memory protection rule. An archival-first Memory Compactor ensures L3 persistence succeeds before reclaiming L2 vector resources. 

A hybrid retrieval engine ranks active memories by synthesizing dense vector embedding similarity (0.45), sparse BM25 lexical relevance (0.20), adaptive retention decay (0.25), and semantic importance (0.10). When historically archived memories become relevant, the system promotes them from L3 back into active L2/L1 tiers. The system further provides pre-storage PII sanitization, user and tenant identity isolation, multimodal memory ingestion, dynamic persona synthesis, and prompt context compression, substantially mitigating catastrophic forgetting and context drift in multi-turn conversational AI.

---

## TECHNICAL FIELD

This invention relates generally to conversational artificial intelligence, natural language processing (NLP), knowledge representation, and retrieval-augmented generation (RAG) architectures. More specifically, the invention relates to computer-implemented systems and methods for managing persistent, decay-weighted, multi-tiered, and self-reconciling long-term memory structures for Large Language Models (LLMs).

> **Architectural Scope Note:**  
> The designation *"Memory Operating System"* is utilized herein strictly as a software architectural design pattern describing memory resource allocation, tiered caching, lifecycle scheduling, compaction, and access governance for conversational AI context. The invention does not encompass, claim, or require computer operating system kernel routines, CPU task dispatching, hardware interrupt controllers, hardware page tables, or physical memory virtualization.

---

## BACKGROUND AND PRIOR ART

Standard Large Language Model (LLM) conversational agents are inherently stateless across independent sessions. While fixed context windows allow agents to track immediate dialogue turns, long-term memory across days, weeks, or months requires external memory retrieval systems.

Existing conversational memory architectures suffer from several major technical deficiencies:
1. **Static Vector Representations & Lack of Temporal Decay**: Conventional vector databases store fixed embeddings without modeling temporal relevance decay. An ephemeral note recorded months prior is weighted identically to critical user facts acquired recently.
2. **The Memory Overwrite vs. Duplicate Rejection Dilemma**: Prior systems either blindly overwrite previous knowledge or discard incoming similar statements as duplicates. They lack mechanisms to identify evolutionary fact changes (e.g., a user relocating from Hyderabad to Bengaluru), resulting in contradictory context retrieved simultaneously.
3. **Keyword-Vector Mismatch (Vector Drift)**: Pure dense vector search frequently fails on exact alphanumeric, entity-specific, or keyword queries due to semantic smoothing in high-dimensional embedding space.
4. **Context Pollution & Prompt Bloat**: Storing uncurated conversational turns, transient queries, and polite acknowledgments pollutes retrieval indexes, diluting prompt relevance and inflating token consumption.
5. **Monolithic Storage Flatness**: Conventional RAG implementations store all records in a single database without differentiated access tiers, causing active search latencies to degrade as historical record counts grow.

---

## DETAILED DESCRIPTION OF INNOVATIONS & ARCHITECTURE

```text
                             USER INPUT
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   PII Sanitization    │ (Scrubbing emails, phones, credentials)
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
                     │   Persona Synthesis   │ (Dynamic persona extraction & context compression)
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

### 1. Three-Tier Hierarchical Memory Architecture

The system structures conversational data across three distinct tiers:

1. **Level-1 (L1) Working Memory (In-Memory RAM FIFO Buffer)**:
   - High-speed, in-memory ring buffer holding recent multi-turn conversational dialog and actively referenced hot memories.
   - Provides sub-millisecond retrieval latency for multi-turn coherence and anaphora resolution without incurring vector query overhead.
2. **Level-2 (L2) Active Vector Store (ChromaDB)**:
   - Persistent embedding collection storing currently active long-term memories.
   - Indexed for dense semantic similarity search and hybrid RAG scoring, partitioned strictly by `user_id` and `tenant_id`.
3. **Level-3 (L3) Cold Archive (SQLite Disk Storage)**:
   - Persistent relational database housing historical, decayed, stale, or superseded memories paged out from L2.
   - Retains complete lineage history, timestamps, and metadata without polluting active vector search indices.
   - Supports on-demand restoration back to L2/L1 when historical knowledge is queried.

---

### 2. Comprehensive Memory Lifecycle

Memory objects progress through a complete, eleven-stage lifecycle:

$$\text{Create} \longrightarrow \text{Validate} \longrightarrow \text{Distill} \longrightarrow \text{Deduplicate/Reconcile} \longrightarrow \text{Store} \longrightarrow \text{Retrieve} \longrightarrow \text{Reinforce} \longrightarrow \text{Decay} \longrightarrow \text{Archive} \longrightarrow \text{Compact/Reclaim} \longrightarrow \text{Restore/Promote}$$

1. **Create & Validate**: Input text is scrubbed of PII, evaluated for query-like patterns, classified into categories, scored for permanence, and passed through the LLM Memory Gate.
2. **Distill & Reconcile**: Validated utterances are normalized into third-person assertions and compared against existing memories to establish lineage relationships.
3. **Store**: Persisted as `ACTIVE` in L2 ChromaDB and promoted to L1 Working Memory.
4. **Retrieve & Reinforce**: Surfaced by hybrid retrieval during conversational queries. Memory access counts are incremented, dynamically reinforcing retention stability.
5. **Decay & Sweep**: Over elapsed time, non-reinforced memories experience retention decay. The background Lifecycle Scheduler identifies stale candidates.
6. **Archive & Reclaim**: Compactor writes candidates to L3 Cold Archive before deleting L2 vector records.
7. **Restore & Promote**: Queries targeting historical knowledge retrieve items from L3, promoting them back to L2 and L1.

---

### 3. Memory State Classifications and Lineage Tracking

The architecture distinguishes between **Storage Lifecycle State** and **Logical Lineage State**:

- **Storage States**:
  - `ACTIVE`: The memory resides in L2 (and optionally L1) and is eligible for real-time hybrid retrieval.
  - `COLD / ARCHIVED`: The memory has been paged out to L3 Cold Storage due to retention decay or supersession.
  - `RESTORED`: A previously archived L3 memory that has been re-indexed into L2/L1 upon receiving new query relevance.
- **Lineage States**:
  - `ACTIVE`: Represents current, undisputed factual knowledge.
  - `SUPERSEDED`: Represents historically valid knowledge that has been updated or contradicted by newer information (e.g., previous home address), linked to the successor memory via `superseded_by` metadata.

---

### 4. Adaptive Ebbinghaus Retention Decay Engine

Memory retention probability $R(\Delta t)$ is computed via an adapted Ebbinghaus exponential decay model:

$$\Delta t = \max\left(0.0, \frac{t - t_0}{3600.0}\right) \quad \text{(elapsed hours)}$$

Memory stability $S$ is dynamically determined by baseline permanence, category persistence weight, user feedback signals, and logarithmic access reinforcement:

$$\text{Base Stability} = \max(0.1, \text{Importance Score}) \times 48.0 \times W_{\text{category}} \times M_{\text{feedback}}$$

Where implemented category weights $W_{\text{category}}$ reflect intrinsic domain persistence:
- **Preference**: $2.5$ (highest persistence)
- **Skill**: $2.2$
- **Goal**: $1.8$
- **Project**: $1.5$
- **Fact**: $1.0$ (baseline)
- **Conversation**: $0.5$ (rapid decay)

Access count reinforcement scales logarithmically:

$$\text{Reinforcement} = 1.0 + \ln(1.0 + \max(0, \text{Access Count}))$$

$$S = \text{round}(\text{Base Stability} \times \text{Reinforcement}, 2)$$

The retentive recall probability $R(\Delta t) \in [0.0, 1.0]$ is:

$$R(\Delta t) = \exp\left( -\frac{\Delta t}{\max(0.1, S)} \right)$$

---

### 5. Background Memory Lifecycle Scheduler

The `MemoryLifecycleScheduler` operates as an asynchronous, non-blocking background loop decoupled from synchronous request-response cycles:
- **Periodic Lifecycle Sweeps**: Executes at configurable intervals (e.g., 60 seconds) without blocking FastAPI request handlers.
- **Stale Memory Identification**: Scans active records in L2 and flags memory $m_i$ for cold archival if:
  $$\text{Status}(m_i) = \text{SUPERSEDED} \quad \lor \quad \left( R(\Delta t) < 0.15 \ \land \ \text{Importance}(m_i) < 0.60 \right)$$
- **Decoupled Operation**: Guarantees memory lifecycle maintenance runs autonomously without user prompt dependency.

---

### 6. Important-Memory Protection Rule

To prevent inadvertent eviction of foundational knowledge, the scheduler enforces a strict preservation rule:

$$\text{PreserveInL2}(m_i) = \text{True} \quad \iff \quad \left( \text{Importance}(m_i) \ge 0.65 \ \lor \ \text{Access Count}(m_i) \ge 2 \right) \ \land \ \text{Status}(m_i) = \text{ACTIVE}$$

Memories meeting this criterion are immune from decay-driven archival to L3, ensuring durable core preferences and reinforced facts remain permanently active in vector RAM.

---

### 7. OS Memory Compactor & Archival-First Transactional Safety

The `OSMemoryCompactor` governs memory reclamation across tiers:
- **Archival-First Invariant**: Level-2 vector space is reclaimed **only after** successful persistence to Level-3 SQLite disk archive is confirmed:
  $$\text{ReclaimL2}(m_i) \iff \text{WriteL3}(m_i) = \text{SUCCESS}$$
- **Fault-Tolerant Safety**: If an L3 database write operation fails or times out, the active L2 copy is preserved, guaranteeing zero data loss during memory compaction cycles.

---

### 8. Retrieval-Driven Cold Memory Restoration

When a user query requires historical context that has been archived:
1. Fallback search queries the Level-3 SQLite Cold Archive.
2. Upon identification of a relevant cold record, the `MemoryTierManager` extracts the full document and embedding.
3. The record is re-inserted into Level-2 ChromaDB as an active vector representation.
4. The record is simultaneously promoted into Level-1 Working Memory RAM for immediate conversational synthesis.

---

### 9. Composite Hybrid RAG Retrieval Engine

When query $q$ is issued, candidates are retrieved and scored using the validated 4-factor hybrid interpolation:

$$\text{Score}(m_i, q) = \left( \frac{1}{1 + \text{Dist}(m_i, q)} \cdot 0.45 \right) + \left( \frac{\text{BM25}(m_i, q)}{\max \text{BM25}} \cdot 0.20 \right) + \left( R(\Delta t) \cdot 0.25 \right) + \left( \text{Importance}_i \cdot 0.10 \right)$$

Where:
- $\text{Dist}(m_i, q)$: Cosine/L2 embedding distance in dense vector space.
- $\text{BM25}(m_i, q)$: BM25 lexical relevance score normalized across candidate results.
- $R(\Delta t)$: Adaptive Ebbinghaus retention decay score.
- $\text{Importance}_i$: Permanence score of memory $m_i \in [0.0, 1.0]$.

Candidates failing a minimum relevance threshold are discarded, preventing context pollution.

---

### 10. Persona Synthesis & Dynamic Context Compression

- **Structured Persona Extraction**: The `PersonaSynthesizer` extracts durable user attributes (e.g., user name, geographic location, primary technical skills, active long-term goals) into an explicit persona profile.
- **Context Compression**: The `MemoryCompressor` condenses verbose retrieved memories into an integrated, deduplicated natural language prompt prefix, reducing prompt token payload by **approximately 36%** in validated benchmark scenarios while preserving core factual fidelity.

---

### 11. Privacy, PII Scrubbing, and Multi-Tenant Isolation

- **Pre-Storage PII Scrubbing**: The `PIIScrubber` scans raw input turns using regex patterns and heuristic filters, redacting sensitive identifiers (email addresses, phone numbers, social security numbers, credit card numbers, and API keys) prior to classification and vector embedding generation.
- **Identity Isolation**: All memory operations (ingestion, hybrid search, decay sweeps, L3 cold queries) strictly enforce multi-tenant isolation via mandatory metadata filtering on `user_id` and `tenant_id`.
- **Right-to-Forget Support**: Programmatic APIs allow immediate selective or total purging (`delete_user_memories`) of a user's memory records across L1, L2, and L3 tiers.

---

### 12. Multimodal Memory Processing

The `MultimodalMemoryProcessor` supports dual-modality memory ingestion:
- Ingests text accompanied by external image URLs or base64-encoded image buffers.
- Extracts visual summary descriptions and atomic factual assertions from images.
- Stores visual summaries alongside text representations in L2 ChromaDB with multimodal metadata (`modality="multimodal"`, `image_url`, `visual_summary`).

---

### 13. Conversational Context & Disambiguation

The `ConversationContextManager` and `WorkingMemory` maintain short-term turn buffers:
- **Reference Resolution & Anaphora**: Resolves elliptical or incomplete follow-ups (e.g., user asks *"capital for ?"* after previously discussing Karnataka) by combining immediate L1 dialog history with long-term memory retrieval.
- **Session Context Summaries**: Generates high-level summaries answering meta-conversational inquiries (*"What were we talking about?"*) directly from recent L1 ring buffers.

---

## 📊 EXEMPLARY EXPERIMENTAL RESULTS

The efficacy of the architecture was evaluated using the project's automated verification suite (`tests/run_evaluation.py`). The following results reflect performance observed within the standardized test environment and are presented as evidentiary demonstration of functional viability rather than universal performance guarantees:

### 1. Hybrid Retrieval Performance Benchmark

| Metric | Dense Vector Alone | BM25 Lexical Alone | Composite Hybrid Ranker |
| :--- | :---:| :---:| :---:|
| **Hit Rate@1** | 75% | 50% | **88%** |
| **Recall@5** | 100% | 62% | **100%** |
| **Precision@5** | 24% | 25% | **44%** |
| **Mean Reciprocal Rank (MRR)** | 0.88 | 0.56 | **0.94** |
| **Relevance Accuracy** | 80% | 50% | **90%** |

### 2. Functional Pipeline Validation Summary

- **Memory Ingestion Accuracy**: 100% (validated across diverse domain assertions)
- **Memory Rejection Accuracy**: 100% (ephemeral queries and small talk correctly filtered)
- **Duplicate Detection Accuracy**: 100% (exact duplicates correctly reinforced)
- **Lineage Update Accuracy**: 100% (superseding facts correctly linked and archived)
- **Tier Retrieval Accuracy**: 100% (L1 promotion, L2 persistence, and L3 search fallback)
- **Adaptive Decay Accuracy**: 100% (elapsed decay and stability scaling confirmed)
- **Lifecycle Scheduler Verification**: 100% (7 of 7 scheduler test cases passed including stale detection, important-memory protection, repeated stability, and error recovery)
- **Context Compression Effectiveness**: Approximately 36% prompt character/token reduction in the tested benchmark scenario.

---

## FORMAL PATENT CLAIMS

### Claim 1 (Independent Method Claim)
A computer-implemented method for maintaining persistent conversational memory across multi-session artificial intelligence interactions, the method comprising:
1. Receiving a natural language message from a user in a conversational session;
2. Scrubbing personally identifiable information (PII) from the received message to generate a sanitized input string;
3. Evaluating a semantic category and a temporal permanence score for the sanitized input string;
4. Evaluating the message with a Large Language Model (LLM) memory gate prompt configured to filter ephemeral conversation turns while approving durable user facts;
5. Extracting an atomic, third-person factual statement from the approved message;
6. Querying a Level-2 (L2) active vector storage system using an embedding of the atomic factual statement to identify nearest candidate existing memories scoped by user identity;
7. Reconciling the atomic factual statement against identified candidate memories by determining a semantic relationship selected from the group consisting of: `SUPERSEDES`, `REINFORCES`, `CONTRADICTS`, and `DISTINCT`;
8. Upon determining a `SUPERSEDES` relationship, updating a metadata status of a matched existing memory to `SUPERSEDED` and persisting the atomic factual statement as an `ACTIVE` memory linked via lineage metadata;
9. Promoting the active memory into a volatile Level-1 (L1) working memory buffer;
10. Periodically scanning active memories with an asynchronous background lifecycle scheduler to evaluate adaptive temporal decay scores and identify stale memories;
11. Transactionally archiving identified stale memories to a persistent Level-3 (L3) cold relational archive prior to deleting corresponding representations from the L2 active vector storage system; and
12. Constructing an augmented prompt for an LLM response generation by retrieving memories ranked via a composite hybrid score interpolating vector embedding similarity, lexical BM25 similarity, adaptive time-decay retention, and semantic importance.

---

### Claim 2 (Dependent Claim: Adaptive Category Decay)
The method of claim 1, wherein the adaptive time-decay retention calculates memory retention $R(\Delta t)$ as an exponential decay function of elapsed hours scaled by an adaptive stability score, wherein the adaptive stability score is computed from a baseline duration of approximately 48.0 hours multiplied by a category-specific persistence weight selected according to the evaluated semantic category, and scaled by a logarithmic access count reinforcement factor.

---

### Claim 3 (Dependent Claim: Category Weights)
The method of claim 2, wherein the category-specific persistence weight assigns higher stability multipliers to user preferences, skills, and long-term goals than to generic factual statements or conversational notes.

---

### Claim 4 (Dependent Claim: Important-Memory Protection Rule)
The method of claim 1, wherein the asynchronous background lifecycle scheduler enforces an important-memory protection rule wherein any active memory having an importance score greater than or equal to a predetermined importance threshold (0.65) or an access count greater than or equal to a predetermined access threshold (2) is shielded from decay-driven archival to the Level-3 (L3) cold relational archive.

---

### Claim 5 (Dependent Claim: Archival-First Transactional Safety)
The method of claim 1, wherein transactionally archiving stale memories comprises executing an archival-first safety protocol wherein vector space in the L2 active vector storage system is reclaimed only after successful write verification is returned from the L3 cold relational archive, preserving the L2 vector representation if the L3 archival write fails.

---

### Claim 6 (Dependent Claim: Cold Memory Restoration)
The method of claim 1, further comprising:
- Receiving a subsequent conversational query addressing historically archived information;
- Querying the Level-3 (L3) cold relational archive upon determining absence of sufficient relevance in the L2 active vector storage system; and
- Restoring an identified cold memory by re-indexing its vector representation into the L2 active vector storage system and promoting its text into the L1 working memory buffer.

---

### Claim 7 (Dependent Claim: Composite Hybrid Retrieval Weights)
The method of claim 1, wherein constructing the augmented prompt comprises scoring candidate memories according to a composite ranking function weighting dense vector similarity at approximately 45%, sparse BM25 lexical similarity at approximately 20%, adaptive time-decay retention at approximately 25%, and semantic importance at approximately 10%.

---

### Claim 8 (Dependent Claim: Persona Synthesis & Context Compression)
The method of claim 1, further comprising:
- Synthesizing an explicit user persona profile comprising core identity, location, and preference attributes extracted across active memories; and
- Compressing retrieved memory context into a deduplicated prompt prefix prior to dispatching the augmented prompt to an LLM.

---

### Claim 9 (Dependent Claim: Multimodal Ingestion)
The method of claim 1, wherein receiving the message comprises receiving image data in conjunction with text, and wherein extracting the atomic factual statement comprises generating a visual summary assertion of the image data and persisting the visual summary assertion with multimodal metadata in the L2 active vector storage system.

---

### Claim 10 (Dependent Claim: Privacy & Scoped Isolation)
The method of claim 1, wherein each memory stored in the L1 working memory buffer, L2 active vector storage system, and L3 cold relational archive is partitioned by a unique user identifier (`user_id`) and tenant identifier (`tenant_id`), and wherein hybrid retrieval and background lifecycle scheduling are strictly restricted to records matching the user identifier of the conversational session.

---

### Claim 11 (Dependent Claim: Conversational Context & Anaphora Resolution)
The method of claim 1, further comprising maintaining a recent multi-turn history buffer in the L1 working memory buffer, and resolving incomplete or elliptical user queries through contextual reference resolution against the recent multi-turn history buffer prior to executing long-term memory retrieval.

---

### Claim 12 (Independent System Claim)
A computing system comprising:
- One or more processors; and
- One or more non-transitory computer-readable media storing instructions that, when executed by the one or more processors, cause the computing system to perform operations comprising:
  1. Receiving a user utterance within a multi-turn conversational session;
  2. Filtering ephemeral conversational noise from the user utterance via a Large Language Model (LLM) memory gate;
  3. Distilling approved utterances into atomic third-person factual assertions;
  4. Performing semantic reconciliation against existing Level-2 (L2) vector records to identify superseding or reinforcing relationships;
  5. Managing storage across a hierarchy comprising a volatile Level-1 (L1) working memory buffer, an L2 active vector database, and a Level-3 (L3) cold relational database;
  6. Executing an asynchronous background lifecycle scheduler configured to detect stale memories using category-weighted adaptive Ebbinghaus decay while preserving memories satisfying an important-memory protection rule;
  7. Reclaiming L2 vector storage using an archival-first protocol requiring confirmed L3 persistence prior to L2 record deletion; and
  8. Generating conversational responses using an LLM supplied with an augmented prompt populated by hybrid retrieval interpolating dense vector similarity, BM25 lexical relevance, adaptive retention decay, and memory importance.

---

### Claim 13 (Independent Computer-Readable Storage Medium Claim)
A non-transitory computer-readable storage medium comprising computer-executable instructions that, when executed by one or more processors of a computing device, cause the computing device to execute the method of any one of Claims 1 through 11.
