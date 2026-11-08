import os
import sys
import re
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import chromadb

from app.core import clock
from app.embeddings.encoder import get_embedding
from app.llm.gemini import ask_gemini
from app.memory_v2.facts import get_connection, get_all_facts

# Chroma collection for facts_v2 and turns_v2
chroma_client = chromadb.PersistentClient(path="memory_db")
facts_collection = chroma_client.get_or_create_collection(name="facts_v2")
turns_collection = chroma_client.get_or_create_collection(name="turns_v2")


def _parse_datetime(dt_val: Any) -> datetime:
    if isinstance(dt_val, datetime):
        return dt_val
    if not dt_val:
        return clock.get_now()
    s = str(dt_val).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return clock.get_now()


class SimpleBM25:
    """
    Lightweight BM25 implementation for scoring facts over 'subject attribute value source_text'.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"\w+", str(text).lower())

    def rank(self, query: str, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not facts:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            for f in facts:
                f["bm25_score"] = 0.0
            return list(facts)

        doc_tokens = []
        for f in facts:
            text = f"{f.get('subject', '')} {f.get('attribute', '')} {f.get('value', '')} {f.get('source_text', '')}"
            doc_tokens.append(self._tokenize(text))

        total_docs = len(facts)
        avg_doc_len = sum(len(t) for t in doc_tokens) / max(1, total_docs)

        df = {}
        for q in query_tokens:
            df[q] = sum(1 for dt in doc_tokens if q in dt)

        scored = []
        for idx, f in enumerate(facts):
            tokens = doc_tokens[idx]
            doc_len = len(tokens)
            score = 0.0

            for q in query_tokens:
                if q not in df or df[q] == 0:
                    continue
                tf = tokens.count(q)
                if tf == 0:
                    continue
                idf = math.log((total_docs - df[q] + 0.5) / (df[q] + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / max(1, avg_doc_len)))
                score += idf * (numerator / denominator)

            f_copy = dict(f)
            f_copy["bm25_score"] = round(score, 4)
            scored.append(f_copy)

        scored.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored


def classify_question_intent(question: str) -> str:
    """
    One cheap LLM call to classify the question as:
      - 'current': asks about active/present user status, facts, preferences, identity.
      - 'historical': asks about previous/former states, timeline changes, prior locations, or past events.
      - 'general': general world knowledge, chitchat, or unrelated to user facts.
    """
    prompt = f"""You are a query intent classifier for an AI memory system.
Classify the following user message into EXACTLY ONE of these categories:
- current: The user asks about their active/present status, current role, location, personal facts, preferences, or traits.
- historical: The user asks about past history, previous/former states, prior locations, timeline changes, or past events/trips.
- general: The user asks about general world knowledge, explanations, public facts, greetings, or questions unrelated to personal facts.

User Message: "{question}"

Respond with ONLY one word: "current", "historical", or "general"."""

    response = ask_gemini(prompt, temperature=0.0)
    cleaned = response.strip().lower()

    if "historical" in cleaned:
        return "historical"
    elif "general" in cleaned:
        return "general"
    elif "current" in cleaned:
        return "current"

    # Default fallback heuristics if ambiguous
    q_lower = question.lower()
    if any(w in q_lower for w in ["before", "previously", "earlier", "past", "used to", "originally", "former", "prior"]):
        return "historical"
    if any(q_lower.startswith(w) for w in ["what is ", "who is ", "how do ", "explain ", "tell me about "]) and not any(p in q_lower for p in [" my ", " i ", " me "]):
        return "general"

    return "current"


def format_fact(fact: Dict[str, Any]) -> str:
    """
    Formats a fact as: '[valid_from -> valid_to or now] subject attribute: value'
    """
    valid_from = fact.get("valid_from") or "unknown"
    valid_to = fact.get("valid_to")
    end_time = valid_to if valid_to else "now"
    subject = fact.get("subject", "user")
    attribute = fact.get("attribute", "")
    value = fact.get("value", "")

    return f"[{valid_from} -> {end_time}] {subject} {attribute}: {value}"


def retrieve_facts(
    user_id: str,
    query: str,
    now: Optional[str] = None,
    db_path: Optional[str] = None,
    top_k: int = 15
) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    1. Candidate generation over ALL of the user's facts:
       BM25 over 'subject attribute value source_text', plus dense search in facts_v2 (top 50).
       Fuse them with Reciprocal Rank Fusion, k=60.
    2. One cheap LLM call classifies question as current, historical, or general.
       - current: returns only active facts.
       - historical: also includes superseded facts, sorted by valid_from.
       - general: returns no personal facts.
    3. Rerank top 30 fused results by 0.6 * rrf_normalized + 0.4 * retention, keep top 15.
       (Placeholder: retention = 1.0 until decay.py is implemented).
    4. Formats each fact as: '[valid_from -> valid_to or now] subject attribute: value'.

    Returns:
      (intent, formatted_facts_list, formatted_string_block)
    """
    now = now or clock.get_now().isoformat()

    # Step 1: Query intent classification (One cheap LLM call)
    intent = classify_question_intent(query)
    if intent == "general":
        return "general", [], "No personal facts relevant to general query."

    # Fetch all user facts from SQLite
    all_user_facts = get_all_facts(user_id, db_path=db_path)
    if not all_user_facts:
        return intent, [], "No memories recorded yet."

    # Filter facts by intent
    if intent == "current":
        candidate_facts = [f for f in all_user_facts if f.get("status") == "active"]
    else:  # historical
        candidate_facts = list(all_user_facts)

    if not candidate_facts:
        return intent, [], "No relevant facts found for query."

    # Step 2: Dense retrieval in Chroma facts_v2 (top 50)
    dense_ranked_ids: List[str] = []
    try:
        query_emb = get_embedding(query)
        dense_res = facts_collection.query(
            query_embeddings=[query_emb],
            n_results=min(50, len(candidate_facts)),
            where={"user_id": user_id}
        )
        if dense_res and dense_res.get("ids") and dense_res["ids"]:
            dense_ranked_ids = dense_res["ids"][0]
    except Exception as e:
        print(f"[MemoryV2 Retrieve] Dense query warning: {e}")

    # Step 3: BM25 candidate ranking over "subject attribute value source_text"
    bm25 = SimpleBM25()
    bm25_ranked = bm25.rank(query=query, facts=candidate_facts)

    # Step 4: Reciprocal Rank Fusion (k=60)
    rrf_k = 60
    rrf_scores: Dict[str, float] = {}

    # Accumulate BM25 ranks
    for rank_idx, doc in enumerate(bm25_ranked):
        fid = doc["id"]
        rrf_scores[fid] = rrf_scores.get(fid, 0.0) + (1.0 / (rrf_k + rank_idx + 1))

    # Accumulate Dense ranks
    for rank_idx, fid in enumerate(dense_ranked_ids):
        rrf_scores[fid] = rrf_scores.get(fid, 0.0) + (1.0 / (rrf_k + rank_idx + 1))

    # Lookup map
    fact_map = {f["id"]: f for f in candidate_facts}

    # Gather candidate list with RRF scores
    scored_candidates = []
    for fid, score in rrf_scores.items():
        if fid in fact_map:
            f_item = dict(fact_map[fid])
            f_item["rrf_score"] = score
            scored_candidates.append(f_item)

    if not scored_candidates:
        return intent, [], "No matching facts."

    # Top 30 fused results
    scored_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
    top_30 = scored_candidates[:30]

    # Normalize RRF scores of top 30 to [0.0, 1.0]
    max_rrf = max(item["rrf_score"] for item in top_30) if top_30 else 1.0
    decay_mode = (os.getenv("DECAY_MODE") or "default").strip().lower()

    if decay_mode == "none":
        # Ablation 1: No decay (pure RRF normalized score)
        for item in top_30:
            rrf_norm = item["rrf_score"] / max_rrf if max_rrf > 0 else 1.0
            retention = 1.0
            item["final_score"] = round(rrf_norm, 4)
    elif decay_mode == "memoria":
        # Ablation 2: Memoria decay formula: w_i = exp(-0.02 * x_i) where x is age in minutes normalized [0,1]
        now_dt = _parse_datetime(now)
        ages = []
        for item in top_30:
            ts = item.get("valid_from") or item.get("created_at") or now
            dt = _parse_datetime(ts)
            age_min = max(0.0, (now_dt - dt).total_seconds() / 60.0)
            item["_age_min"] = age_min
            ages.append(age_min)

        min_age = min(ages) if ages else 0.0
        max_age = max(ages) if ages else 0.0
        age_range = max_age - min_age

        for item in top_30:
            rrf_norm = item["rrf_score"] / max_rrf if max_rrf > 0 else 1.0
            if age_range > 0:
                x_i = (item["_age_min"] - min_age) / age_range
            else:
                x_i = 0.0
            retention = math.exp(-0.02 * x_i)
            item["final_score"] = round(0.6 * rrf_norm + 0.4 * retention, 4)
    else:
        # Default v2 behavior: retention = 1.0 placeholder until decay.py is implemented
        for item in top_30:
            rrf_norm = item["rrf_score"] / max_rrf if max_rrf > 0 else 1.0
            retention = 1.0
            item["final_score"] = round(0.6 * rrf_norm + 0.4 * retention, 4)

    # Sort top 30 by final score
    top_30.sort(key=lambda x: x["final_score"], reverse=True)
    top_15 = top_30[:top_k]

    # For historical queries, order selected facts chronologically by valid_from
    if intent == "historical":
        top_15.sort(key=lambda x: str(x.get("valid_from") or ""), reverse=False)

    # Step 5: Format each fact: '[valid_from -> valid_to or now] subject attribute: value'
    formatted_lines = [format_fact(f) for f in top_15]
    formatted_block = "\n".join(formatted_lines) if formatted_lines else "No specific memory facts found."

    return intent, top_15, formatted_block


def format_session_summary(session_turns: List[Dict[str, str]], max_turns: int = 6) -> str:
    """
    Formats recent conversation turns from the current session as a summary block.
    """
    if not session_turns:
        return "No recent conversation history in this session."

    lines = []
    for turn in session_turns[-max_turns:]:
        u = turn.get("user", "").strip()
        a = turn.get("assistant", "").strip()
        if u:
            lines.append(f"User: {u}")
        if a:
            lines.append(f"Assistant: {a}")

    return "\n".join(lines) if lines else "No recent conversation history in this session."


def retrieve_raw_turns(
    user_id: str,
    query: str,
    top_k: int = 5
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Retrieves top-k raw user dialogue turns for user_id using dense similarity + BM25 RRF fusion.
    """
    try:
        count = turns_collection.count()
        if count == 0:
            return [], "No conversation turns recorded."

        user_docs_res = turns_collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"]
        )
        if not user_docs_res or not user_docs_res.get("ids"):
            return [], "No conversation turns recorded."

        all_ids = user_docs_res["ids"]
        all_docs = user_docs_res["documents"]
        all_metas = user_docs_res["metadatas"]

        if not all_ids:
            return [], "No conversation turns recorded."

        # 1. Dense search
        dense_ids = []
        try:
            dense_res = turns_collection.query(
                query_embeddings=[get_embedding(query)],
                where={"user_id": user_id},
                n_results=min(25, len(all_ids))
            )
            if dense_res and dense_res.get("ids") and dense_res["ids"]:
                dense_ids = dense_res["ids"][0]
        except Exception as e:
            print(f"[MemoryV2 Retrieve] Dense query turns warning: {e}")

        # 2. BM25 search
        bm25 = SimpleBM25()
        turn_items = [
            {
                "id": tid,
                "document": doc,
                "timestamp": meta.get("timestamp", "") if meta else "",
                "role": meta.get("role", "user") if meta else "user",
                "source_text": doc,
                "subject": "",
                "attribute": "",
                "value": doc
            }
            for tid, doc, meta in zip(all_ids, all_docs, all_metas)
        ]
        bm25_ranked = bm25.rank(query=query, facts=turn_items)

        # 3. Reciprocal Rank Fusion (k=60)
        rrf_k = 60
        rrf_scores: Dict[str, float] = {}
        for rank_idx, doc in enumerate(bm25_ranked):
            tid = doc["id"]
            rrf_scores[tid] = rrf_scores.get(tid, 0.0) + (1.0 / (rrf_k + rank_idx + 1))
        for rank_idx, tid in enumerate(dense_ids):
            rrf_scores[tid] = rrf_scores.get(tid, 0.0) + (1.0 / (rrf_k + rank_idx + 1))

        doc_map = {item["id"]: item for item in turn_items}
        scored = []
        for tid, score in rrf_scores.items():
            if tid in doc_map:
                d = dict(doc_map[tid])
                d["rrf_score"] = score
                scored.append(d)

        scored.sort(key=lambda x: x["rrf_score"], reverse=True)
        top_turns = scored[:top_k]

        lines = []
        for t in top_turns:
            ts = t.get("timestamp", "")
            doc_text = t.get("document", "")
            lines.append(f"[{ts}] User: {doc_text}")

        formatted_block = "\n".join(lines) if lines else "No relevant conversation turns found."
        return top_turns, formatted_block
    except Exception as e:
        print(f"[MemoryV2 Retrieve] Error retrieving raw turns: {e}")
        return [], "No conversation turns available."
