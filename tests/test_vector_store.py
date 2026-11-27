"""Tests for the Chroma vector search (issue #24). Fake embeddings: no GPU, no model download."""

import hashlib
import re
import uuid

import numpy as np
import pytest

chromadb = pytest.importorskip("chromadb")

from compliance_copilot.vector_store import VectorStore, check_query, format_query

DIMENSIONS = 64


def fake_embed(text):
    """A word-count vector: each word adds 1 to a position chosen by a fixed hash, then the vector is normalized."""
    vector = np.zeros(DIMENSIONS, dtype="float32")
    for word in re.findall(r"[a-z]+", text.lower()):
        # hashlib gives the same position on every run (Python's hash() changes between runs)
        vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSIONS] += 1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def make_store(name=None):
    # A unique name per test, so tests never see each other's collections
    return VectorStore(
        chromadb.EphemeralClient(),
        name or "test-" + uuid.uuid4().hex[:8],
        embed_documents=lambda texts: np.array([fake_embed(t) for t in texts]),
        embed_query=fake_embed,
    )


CLAUSES = [
    ("SWE-050:text", "software requirements shall be identified and approved", {"swe_id": "SWE-050", "kind": "text"}),
    ("SWE-050:note1", "requirements include reused components", {"swe_id": "SWE-050", "kind": "note"}),
    ("SWE-052:text", "bidirectional traceability between requirements and design", {"swe_id": "SWE-052", "kind": "text"}),
    ("SWE-184:text", "safety constraints controls and mitigations between hardware operator and software", {"swe_id": "SWE-184", "kind": "text"}),
    ("SWE-157:text", "access control and authentication for communications", {"swe_id": "SWE-157", "kind": "text"}),
]


def build(store, rows=CLAUSES):
    ids, documents, metadatas = zip(*rows)
    return store.build(list(ids), list(documents), list(metadatas))


def test_returns_exactly_k_best_first_with_tags():
    """retrieve() returns exactly k matches, the most similar first, each carrying its document's tags."""
    store = build(make_store())
    matches = store.retrieve("traceability between requirements and design", k=3)
    assert len(matches) == 3
    assert matches[0]["id"] == "SWE-052:text"
    assert matches[0]["swe_id"] == "SWE-052"
    similarities = [m["similarity"] for m in matches]
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.parametrize("query, k", [("", 5), ("   ", 5), (None, 5), ("x", 0), ("x", -1), ("x", True), ("x", 1.5)])
def test_invalid_inputs_are_rejected(query, k):
    """An empty or blank query, a missing query, or a k that is not a positive whole number raises ValueError."""
    with pytest.raises(ValueError):
        check_query(query, k)
    store = build(make_store())
    with pytest.raises(ValueError):
        store.retrieve(query, k)


def test_ties_at_the_cutoff_are_broken_by_id_whatever_the_insertion_order():
    """Exactly tied documents at the cut-off are ordered by ID, however the documents were added."""
    # Four documents with identical text are exactly tied; only 2 fit in the top k
    tied = [(doc_id, "safety inhibit", {"swe_id": doc_id}) for doc_id in ["d", "b", "a", "c"]]
    first = build(make_store(), tied).retrieve("safety inhibit", k=2)
    second = build(make_store(), list(reversed(tied))).retrieve("safety inhibit", k=2)
    assert [m["id"] for m in first] == ["a", "b"]
    assert [m["id"] for m in second] == ["a", "b"]


def test_rebuilding_from_scratch_gives_the_same_results():
    """Building the collection again from scratch, in a different order, returns the same top results."""
    store = build(make_store())
    before = [m["id"] for m in store.retrieve("software requirements", k=4)]
    # Build again under the same name: the old collection is deleted, and the documents are added in another order
    build(store, list(reversed(CLAUSES)))
    after = [m["id"] for m in store.retrieve("software requirements", k=4)]
    assert store.count() == len(CLAUSES)
    assert before == after


def test_k_larger_than_the_collection_returns_every_document():
    """Asking for more results than there are documents returns every document instead of failing."""
    store = build(make_store())
    assert len(store.retrieve("requirements", k=1000)) == len(CLAUSES)


def test_unique_keeps_one_chunk_per_clause_and_respects_the_allowed_list():
    """retrieve_unique() returns one chunk per clause, and only clauses in the allowed list when one is given."""
    store = build(make_store())
    unique = store.retrieve_unique("requirements", k=3)
    assert len({m["swe_id"] for m in unique}) == len(unique) == 3
    core = store.retrieve_unique("requirements", k=5, allowed=["SWE-050", "SWE-184"])
    # Only the two allowed clauses come back, once each, even though k=5
    core_ids = [m["swe_id"] for m in core]
    assert len(core_ids) == len(set(core_ids)) == 2
    assert set(core_ids) == {"SWE-050", "SWE-184"}


def test_where_filter_limits_the_search():
    """A metadata filter (like the notebook's Handbook section filter) limits which documents are searched."""
    store = build(make_store())
    matches = store.retrieve("requirements", k=5, where={"kind": {"$in": ["note"]}})
    assert [m["id"] for m in matches] == ["SWE-050:note1"]


def test_build_rejects_mismatched_or_duplicate_inputs():
    """build() refuses inputs of different lengths and repeated document IDs."""
    store = make_store()
    with pytest.raises(ValueError):
        store.build(["a", "b"], ["only one document"], [{}, {}])
    with pytest.raises(ValueError):
        store.build(["a", "a"], ["x", "y"], [{}, {}])


def test_format_query_matches_the_notebook():
    """Queries are written in the same instruction-then-query form the notebook uses for Qwen3."""
    assert format_query("Find clauses.", "  The SFMC shall log faults. ") == "Instruct: Find clauses.\nQuery: The SFMC shall log faults."
