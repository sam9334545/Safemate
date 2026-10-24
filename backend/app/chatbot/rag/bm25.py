"""Lightweight, deterministic BM25 lexical search engine with safety-domain synonym expansion."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from app.chatbot.rag.schemas import RetrievedChunk

# Common English stopwords that don't carry domain semantics
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
    "best", "good", "great", "better", "tell", "please", "can", "want", "like", "know",
    "get", "give", "make", "need", "also", "see", "way",
}

# Domain-specific synonym mappings to handle layperson phrasing in digital safety
SYNONYM_MAP: Dict[str, List[str]] = {
    "morph": ["deepfake", "synthetic", "ncii", "manipulated"],
    "morphed": ["deepfake", "synthetic", "ncii", "manipulated"],
    "deepfake": ["morph", "synthetic", "ai", "face"],
    "nude": ["intimate", "private", "ncii", "explicit"],
    "nudes": ["intimate", "private", "ncii", "explicit"],
    "sextortion": ["blackmail", "extortion", "threats", "financial"],
    "blackmailed": ["extortion", "blackmail", "threats"],
    "fir": ["police", "complaint", "zero", "station"],
    "police": ["fir", "reporting", "investigation"],
    "scam": ["fraud", "financial", "1930", "extortion"],
    "cheated": ["fraud", "financial", "1930", "scam"],
    "funds": ["financial", "money", "fraud", "1930"],
    "transferred": ["financial", "fraud", "transaction", "1930"],
    "extortionist": ["blackmail", "extortion", "financial"],
    "money": ["financial", "fraud", "1930"],
    "eve": ["teasing", "stalking", "harassment", "bns"],
    "teasing": ["stalking", "harassment", "bns"],
    "proof": ["evidence", "screenshot", "preservation", "bsa"],
    "screenshot": ["evidence", "preservation", "metadata", "proof"],
    "lawyer": ["legal", "aid", "nalsa", "ncw"],
    "portal": ["cybercrime", "online", "reporting"],
    "teen": ["minor", "child", "children", "ncmec"],
    "teenage": ["minor", "child", "children", "ncmec"],
    "daughter": ["minor", "child", "children", "ncmec"],
    "anonymous": ["anonymously", "confidential", "women"],
    "anonymously": ["anonymous", "confidential", "women"],
    "secretly": ["confidential", "anonymous"],
    "syber": ["cybercrime", "cyber"],
    "blakmail": ["blackmail", "extortion"],
}


def tokenize(text: str, expand_synonyms: bool = False) -> List[str]:
    """Tokenize and normalize text into clean words with optional synonym expansion."""
    if not text:
        return []
    raw_tokens = re.findall(r"\b[a-z0-9_]{2,}\b", text.lower())
    filtered = [t for t in raw_tokens if t not in STOPWORDS]

    if not expand_synonyms:
        return filtered

    expanded = list(filtered)
    for token in filtered:
        if token in SYNONYM_MAP:
            expanded.extend(SYNONYM_MAP[token])
    return expanded


class BM25Index:
    """Okapi BM25 implementation for local lexical ranking across safety documents."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks: List[RetrievedChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.corpus_size: int = 0
        self.chunk_term_freqs: List[Dict[str, int]] = []

    def build_index(self, chunks: List[RetrievedChunk]) -> None:
        """Index a list of approved knowledge chunks."""
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_lengths = []
        self.chunk_term_freqs = []
        self.doc_freqs = Counter()

        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        total_length = 0
        for chunk in chunks:
            # Combine title, section, and text for rich indexing
            full_text = f"{chunk.title} {chunk.section or ''} {chunk.text}"
            tokens = tokenize(full_text, expand_synonyms=False)
            t_len = len(tokens)
            self.doc_lengths.append(t_len)
            total_length += t_len

            tf = Counter(tokens)
            self.chunk_term_freqs.append(tf)

            for term in tf.keys():
                self.doc_freqs[term] += 1

        self.avg_doc_len = total_length / self.corpus_size

    def compute_idf(self, term: str) -> float:
        """Compute Robertson-Spärck Jones IDF with smoothing."""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        return math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def search(
        self,
        query: str,
        jurisdiction: str = "IN",
        topic: Optional[str] = None,
        top_k: int = 3,
        min_score: float = 1.2,
    ) -> List[Tuple[RetrievedChunk, float]]:
        """Score and return top matching chunks matching query and filters."""
        if self.corpus_size == 0:
            return []

        query_tokens = tokenize(query, expand_synonyms=True)
        if not query_tokens:
            return []

        norm_jurisdiction = jurisdiction.strip().upper()
        scores: List[Tuple[int, float]] = []

        for idx, chunk in enumerate(self.chunks):
            # Jurisdiction filter: match target jurisdiction or GLOBAL universal tools
            if chunk.jurisdiction != "GLOBAL" and chunk.jurisdiction != norm_jurisdiction:
                continue

            # Topic filter (optional)
            if topic and chunk.topic != topic:
                continue

            doc_len = self.doc_lengths[idx]
            tf_dict = self.chunk_term_freqs[idx]
            score = 0.0

            for term in query_tokens:
                if term not in tf_dict:
                    continue
                tf = tf_dict[term]
                idf = self.compute_idf(term)
                # BM25 term weighting
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                score += idf * (numerator / (denominator or 1.0))

            if score >= min_score:
                scores.append((idx, score))

        # Sort descending by BM25 score
        scores.sort(key=lambda x: x[1], reverse=True)

        results: List[Tuple[RetrievedChunk, float]] = []
        for idx, score in scores[:top_k]:
            results.append((self.chunks[idx], score))

        return results
