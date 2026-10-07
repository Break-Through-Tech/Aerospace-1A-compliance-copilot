import pandas as pd
import pytest

from compliance_copilot.retrieval import ClauseRetriever


def corpus(texts):
    return pd.DataFrame(
        [
            {
                "swe_id": "SWE-{:03d}".format(i + 1),
                "clause_id": "4.1.{}".format(i + 1),
                "text": text,
                "srs_scope": "direct",
            }
            for i, text in enumerate(texts)
        ]
    )


def query(text, title="Example"):
    return pd.DataFrame([{"requirement_id": "SFMC-REQ-001", "title": title, "text": text}])


def test_distinctive_term_beats_shared_boilerplate():
    retriever = ClauseRetriever(
        corpus(
            [
                "The software shall authenticate users.",
                "The software shall record errors.",
                "The software shall maintain traceability.",
            ]
        )
    )
    matches = retriever.retrieve(query("The software shall authenticate the pilot."))
    assert list(matches.swe_id) == ["SWE-001"]
    assert matches.iloc[0].similarity_score > 0


@pytest.mark.parametrize("text", ["xylophone", "The software shall NASA [SWE-001] 4.1.1"])
def test_no_match_keeps_requirement_without_fabricating_citation(text):
    retriever = ClauseRetriever(corpus(["authenticate users", "record errors"]))
    match = retriever.retrieve(query(text, title="SFMC"))
    assert len(match) == 1
    assert match.iloc[0].retrieval_status == "NO_LEXICAL_MATCH"
    assert pd.isna(match.iloc[0].swe_id)
    assert match.iloc[0].similarity_score == 0


def test_ties_follow_numeric_clause_order_even_if_input_is_reversed():
    clauses = corpus(["authenticate users"] * 10).iloc[::-1]
    matches = ClauseRetriever(clauses).retrieve(query("authenticate users"), top_k=3)
    assert list(matches.clause_id) == ["4.1.1", "4.1.2", "4.1.3"]


def test_query_does_not_change_vocabulary_or_idf():
    retriever = ClauseRetriever(corpus(["authenticate users", "record errors"]))
    vocabulary = dict(retriever.vectorizer.vocabulary_)
    weights = retriever.vectorizer.idf_.copy()
    retriever.retrieve(query("authenticate xylophone"))
    assert retriever.vectorizer.vocabulary_ == vocabulary
    assert (retriever.vectorizer.idf_ == weights).all()


@pytest.mark.parametrize("top_k", [0, -1, True, 1.5])
def test_invalid_top_k_is_rejected(top_k):
    with pytest.raises(ValueError):
        ClauseRetriever(corpus(["authenticate users"])).retrieve(query("users"), top_k)
