import math
import re
from typing import List, Dict


class BM25Retriever:
    """
    Lightweight BM25 Lexical Ranking algorithm for sparse keyword matching across stored memories.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r'\w+', str(text).lower())

    def score_documents(self, query: str, documents: List[Dict]) -> List[Dict]:
        """
        Computes BM25 lexical similarity scores for a list of document dicts.
        Each document dict must have 'id' and 'document' keys.
        """
        if not documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            for doc in documents:
                doc["bm25_score"] = 0.0
            return documents

        doc_tokens_list = [self._tokenize(doc.get("document", "")) for doc in documents]
        total_docs = len(documents)
        avg_doc_len = sum(len(tokens) for tokens in doc_tokens_list) / max(1, total_docs)

        # Calculate Document Frequency (DF) for query tokens
        df = {}
        for token in query_tokens:
            df[token] = sum(1 for tokens in doc_tokens_list if token in tokens)

        # Compute BM25 for each doc
        for idx, doc in enumerate(documents):
            tokens = doc_tokens_list[idx]
            doc_len = len(tokens)
            score = 0.0

            for token in query_tokens:
                if token not in df or df[token] == 0:
                    continue
                
                # Term Frequency in current doc
                tf = tokens.count(token)
                if tf == 0:
                    continue

                # Inverse Document Frequency (IDF)
                idf = math.log((total_docs - df[token] + 0.5) / (df[token] + 0.5) + 1.0)
                
                # BM25 Term Score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / max(1, avg_doc_len)))
                score += idf * (numerator / denominator)

            doc["bm25_score"] = round(score, 4)

        return documents
