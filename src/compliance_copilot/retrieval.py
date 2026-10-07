"""Lexical candidate retrieval. Scores are similarities, not verdicts."""

import re

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import validate_clauses, validate_table


MATCH_COLUMNS = [
    "requirement_id",
    "requirement_title",
    "requirement_text",
    "rank",
    "swe_id",
    "clause_id",
    "clause_text",
    "srs_scope",
    "similarity_score",
    "retrieval_status",
]
STOP_WORDS = sorted(
    set(ENGLISH_STOP_WORDS)
    | {"shall", "software", "nasa", "sfmc", "requirement", "requirements", "project"}
)


def clean_text(text):
    return re.sub(r"\[SWE-\d+\]", "", str(text), flags=re.IGNORECASE)


class ClauseRetriever:
    def __init__(self, clauses):
        validate_clauses(clauses)
        self.clauses = clauses[clauses["srs_scope"] != "out"].copy().reset_index(drop=True)
        if self.clauses.empty:
            raise ValueError("No SRS-addressable clauses")
        # Sort once so ties are independent of CSV input order.
        self.clauses = self.clauses.sort_values(
            "clause_id", key=lambda s: s.map(lambda v: tuple(map(int, v.split("."))))
        ).reset_index(drop=True)
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=STOP_WORDS,
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",
        )
        self.clause_vectors = self.vectorizer.fit_transform(self.clauses["text"].map(clean_text))

    def retrieve(self, requirements, top_k=3):
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if requirements.empty:
            return pd.DataFrame(columns=MATCH_COLUMNS)
        validate_table(requirements, ["requirement_id", "title", "text"], ["requirement_id"])
        queries = requirements["title"] + " " + requirements["text"]
        vectors = self.vectorizer.transform(queries.map(clean_text))
        scores = cosine_similarity(vectors, self.clause_vectors)
        rows = []
        for query_index, requirement in enumerate(requirements.to_dict("records")):
            base = {
                "requirement_id": requirement["requirement_id"],
                "requirement_title": requirement["title"],
                "requirement_text": requirement["text"],
            }
            ranked = sorted(range(len(self.clauses)), key=lambda i: (-scores[query_index, i], i))
            selected = [i for i in ranked if scores[query_index, i] > 0][:top_k]
            if not selected:
                rows.append(
                    dict(
                        base,
                        rank=None,
                        swe_id=None,
                        clause_id=None,
                        clause_text=None,
                        srs_scope=None,
                        similarity_score=0.0,
                        retrieval_status="NO_LEXICAL_MATCH",
                    )
                )
            for rank, i in enumerate(selected, 1):
                clause = self.clauses.iloc[i]
                rows.append(
                    dict(
                        base,
                        rank=rank,
                        swe_id=clause.swe_id,
                        clause_id=clause.clause_id,
                        clause_text=clause.text,
                        srs_scope=clause.srs_scope,
                        similarity_score=float(scores[query_index, i]),
                        retrieval_status="CANDIDATE",
                    )
                )
        return pd.DataFrame(rows, columns=MATCH_COLUMNS)
