import logging
import os
import uuid
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("factguard.rag")

class VectorStoreRAG:
    """
    RAG system using ChromaDB to store and retrieve evidence chunks,
    source metadata, embeddings, and historical claim evaluations.
    """
    def __init__(self):
        self.initialized = False
        self.client = None
        self.collection = None
        self._setup()

    def _setup(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            self.collection = self.client.get_or_create_collection(
                name="factguard_evidence",
                metadata={"description": "Evidence chunks and source metadata for fact checking"}
            )
            self.initialized = True
            logger.info("ChromaDB Vector Store initialized.")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Falling back to in-memory fallback RAG.")
            self.initialized = False
            self.fallback_storage: List[Dict[str, Any]] = []

    def add_evidence_chunks(
        self,
        claim_id: str,
        evidence_items: List[Dict[str, Any]]
    ) -> int:
        """
        Store evidence chunks with metadata into ChromaDB.
        """
        if not evidence_items:
            return 0

        added_count = 0
        documents = []
        metadatas = []
        ids = []

        for item in evidence_items:
            chunk_text = item.get("evidence_text") or item.get("excerpt") or ""
            if not chunk_text.strip():
                continue

            doc_id = str(uuid.uuid4())
            documents.append(chunk_text)
            metadatas.append({
                "claim_id": claim_id,
                "source_id": item.get("source_id", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "publisher": item.get("publisher", ""),
                "evidence_type": item.get("evidence_type", "contextual"),
                "evidence_strength": float(item.get("evidence_strength", 50.0))
            })
            ids.append(doc_id)

        if not documents:
            return 0

        if self.initialized and self.collection:
            try:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                added_count = len(documents)
            except Exception as e:
                logger.error(f"Error adding docs to ChromaDB: {e}")
        else:
            for d, m, i in zip(documents, metadatas, ids):
                self.fallback_storage.append({"id": i, "document": d, "metadata": m})
            added_count = len(documents)

        return added_count

    def search_similar_evidence(
        self,
        query: str,
        n_results: int = 5,
        claim_id_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant evidence chunks given a query claim.
        """
        results_list: List[Dict[str, Any]] = []

        if self.initialized and self.collection:
            try:
                where_clause = {"claim_id": claim_id_filter} if claim_id_filter else None
                query_kwargs = {"query_texts": [query], "n_results": n_results}
                if where_clause:
                    query_kwargs["where"] = where_clause

                query_res = self.collection.query(**query_kwargs)
                if query_res and query_res.get("documents"):
                    docs = query_res["documents"][0]
                    metas = query_res["metadatas"][0] if query_res.get("metadatas") else [{}] * len(docs)
                    distances = query_res["distances"][0] if query_res.get("distances") else [0.5] * len(docs)

                    for d, m, dist in zip(docs, metas, distances):
                        results_list.append({
                            "document": d,
                            "metadata": m,
                            "score": round(1.0 - (dist if dist < 1.0 else 0.5), 3)
                        })
            except Exception as e:
                logger.error(f"Error querying ChromaDB: {e}")

        if not results_list and hasattr(self, 'fallback_storage'):
            for item in self.fallback_storage:
                doc = item["document"]
                if any(word.lower() in doc.lower() for word in query.split() if len(word) > 3):
                    results_list.append({
                        "document": doc,
                        "metadata": item["metadata"],
                        "score": 0.8
                    })
                if len(results_list) >= n_results:
                    break

        return results_list

vector_rag = VectorStoreRAG()
