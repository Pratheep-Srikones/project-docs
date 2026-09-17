from dataclasses import dataclass

from db.qdrant import QdrantConnector
from indexer.embedder import DualEmbedder
from qdrant_client import models
from qdrant_client.http.models.models import ScoredPoint
from retriever.dense import RetrievalResult


@dataclass(kw_only=True)
class SparseRetrievalResult(RetrievalResult):
    pass


class SparseRetriever:
    def __init__(self, embedder: DualEmbedder, db: QdrantConnector):
        self.embedder = embedder
        self.db = db

    def retrieve(
        self, query: str, collection_name: str = "documents", limit: int = 20
    ) -> list[SparseRetrievalResult]:
        if not self.db.collection_exists(collection_name):
            print("collection not found aborting")
            return []

        sparse_vector = self.embedder.sparse_embed_query(query)
        sparse_results = []
        points = []
        if sparse_vector:
            sparse_query = models.SparseVector(
                indices=sparse_vector["indices"], values=sparse_vector["values"]
            )

            sparse_results = self.db.client.query_points(
                collection_name=collection_name,
                query=sparse_query,
                using="sparse",
                limit=limit,
            ).points

            for idx, res in enumerate(sparse_results):
                points.append(self._build_result(res, idx + 1))

        return points

    def _build_result(self, point: ScoredPoint, rank: int) -> SparseRetrievalResult:
        return SparseRetrievalResult(
            text=point.payload["text"],
            source=point.payload["source"],
            heading_path=point.payload["heading_path"],
            chunk_index=point.payload["chunk_id"],
            images=point.payload["images"],
            score=point.score,
            rank=rank,
            point_id=point.id,
        )
