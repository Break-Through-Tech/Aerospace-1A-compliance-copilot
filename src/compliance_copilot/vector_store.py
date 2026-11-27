"""Vector search over NASA clauses and guidance with ChromaDB (issue #24).

A tested copy of the search used in notebooks/Aerospace_1A.ipynb (retrieve(), retrieve_unique_clauses() and
retrieve_handbook()). The embedding model is passed in as two functions, so the tests can use small fake
embeddings instead of downloading the Qwen3 model. If you change the search in the notebook, change it here too.
"""

import numpy as np

# Extra results fetched beyond k, so documents tied at the k-th place are sorted by ID before the list is cut
DEFAULT_TIE_BUFFER = 10


def format_query(instruction, query):
    """Write a search query the way Qwen3 embedding models expect: an instruction, then the query."""
    return "Instruct: {}\nQuery: {}".format(instruction, query.strip())


def check_query(query, k):
    """Reject an empty query or a k that is not a positive whole number, the same way the notebook does."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")
    # bool is a kind of int in Python, so True would otherwise count as k=1
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer.")


class VectorStore:
    """One Chroma collection plus the functions that embed its documents and the search queries."""

    def __init__(self, client, name, embed_documents, embed_query):
        # client: a Chroma client, e.g. chromadb.EphemeralClient() (in memory, nothing written to disk)
        self.client = client
        self.name = name
        # embed_documents(list of texts) -> one normalized vector per text
        self.embed_documents = embed_documents
        # embed_query(query text) -> one normalized vector
        self.embed_query = embed_query
        self.collection = None

    def build(self, ids, documents, metadatas):
        """Build the collection from scratch: any old collection with the same name is deleted first."""
        if not (len(ids) == len(documents) == len(metadatas)):
            raise ValueError("ids, documents and metadatas must have the same length.")
        if len(set(ids)) != len(ids):
            raise ValueError("Document IDs must be unique.")
        if self.name in [collection.name for collection in self.client.list_collections()]:
            self.client.delete_collection(self.name)
        # embedding_function=None: Chroma stores our vectors and never downloads its own model
        self.collection = self.client.create_collection(
            name=self.name, embedding_function=None, configuration={"hnsw": {"space": "cosine"}}
        )
        vectors = np.asarray(self.embed_documents(list(documents)), dtype="float32")
        # Chroma limits how many documents can be added in one call
        batch_size = self.client.get_max_batch_size()
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self.collection.add(
                ids=list(ids[start:end]),
                documents=list(documents[start:end]),
                metadatas=list(metadatas[start:end]),
                embeddings=vectors[start:end],
            )
        return self

    def count(self):
        """How many documents the collection holds."""
        return self.collection.count()

    def retrieve(self, query, k=5, where=None, tie_buffer=DEFAULT_TIE_BUFFER):
        """The k most similar documents, best first. Ties are broken by document ID, so the order is repeatable.

        where: an optional Chroma metadata filter, e.g. {"section_name": {"$in": ["Guidance"]}}.
        """
        check_query(query, k)
        if self.collection is None:
            raise RuntimeError("Call build() before retrieve().")
        vector = np.asarray(self.embed_query(query.strip()), dtype="float32").reshape(1, -1)
        results = self.collection.query(
            query_embeddings=vector.tolist(),
            # Fetch extra results so a tie at the k-th place is decided by ID below, not by Chroma
            n_results=min(k + tie_buffer, self.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        for doc_id, document, metadata, distance in zip(
            results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            # The document's own tags (e.g. swe_id, clause_id, section) plus its ID, text and similarity
            match = dict(metadata or {})
            match.update({"id": doc_id, "text": document, "similarity": 1.0 - float(distance)})
            matches.append(match)
        # Highest similarity first; the ID breaks ties
        matches.sort(key=lambda match: (-match["similarity"], match["id"]))
        # Keep the top k only after sorting
        return matches[:k]

    def retrieve_unique(self, query, k=3, key="swe_id", allowed=None):
        """The k best documents with different values of `key` (e.g. one chunk per SWE clause).

        allowed: if given, only documents whose `key` is in this list are considered (e.g. the six core SWEs).
        """
        check_query(query, k)
        # Rank every document (collections here are small), then keep the best one for each key
        ranked = self.retrieve(query, k=self.count())
        unique_matches, seen = [], set()
        for match in ranked:
            value = match.get(key)
            if allowed is not None and value not in allowed:
                continue
            if value in seen:
                continue
            seen.add(value)
            unique_matches.append(match)
            if len(unique_matches) == k:
                break
        return unique_matches
