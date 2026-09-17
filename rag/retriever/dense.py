from dataclasses import dataclass

from db.qdrant import QdrantConnector
from indexer.chunker import DocumentChunk
from indexer.embedder import DualEmbedder
from qdrant_client.http.models.models import ScoredPoint


@dataclass(kw_only=True)
class RetrievalResult(DocumentChunk):
    point_id: str = None
    score: float = 0.0
    rank: int = 0


@dataclass(kw_only=True)
class DenseRetrievalResult(RetrievalResult):
    pass


class DenseRetriever:
    def __init__(self, embedder: DualEmbedder, db: QdrantConnector):
        self.embedder = embedder
        self.db = db

    def retrieve(
        self, query: str, collection_name: str = "documents", limit: int = 20
    ) -> list[DenseRetrievalResult]:
        if not self.db.collection_exists(collection_name):
            return []

        dense_vector = self.embedder.dense_embed_query(query)
        points = []
        dense_results = []
        if dense_vector:
            dense_results = self.db.client.query_points(
                collection_name=collection_name,
                query=dense_vector,
                using="dense",
                limit=limit,
            ).points

            for idx, res in enumerate(dense_results):
                points.append(self._build_result(res, idx + 1))

        return points

    def _build_result(self, point: ScoredPoint, rank: int) -> DenseRetrievalResult:
        return DenseRetrievalResult(
            text=point.payload["text"],
            source=point.payload["source"],
            heading_path=point.payload["heading_path"],
            chunk_index=point.payload["chunk_id"],
            images=point.payload["images"],
            score=point.score,
            rank=rank,
            point_id=point.id,
        )
