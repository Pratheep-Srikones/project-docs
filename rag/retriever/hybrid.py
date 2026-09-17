from dataclasses import asdict, dataclass

from db.qdrant import QdrantConnector
from indexer.embedder import DualEmbedder
from retriever.dense import DenseRetriever, RetrievalResult
from retriever.sparse import SparseRetriever

RRF_K = 60


@dataclass(kw_only=True)
class HybridRetrievalResult(RetrievalResult):
    rrf_score: float = 0.0
    dense_rank: int | None = None
    sparse_rank: int | None = None

    @classmethod
    def from_retrieval_result(
        cls,
        result: RetrievalResult,
        rrf_score: float = 0.0,
        dense_rank: int | None = None,
        sparse_rank: int | None = None,
    ) -> "HybridRetrievalResult":
        return cls(
            **asdict(result),
            rrf_score=rrf_score,
            dense_rank=dense_rank,
            sparse_rank=sparse_rank,
        )


class HybridRetriever:
    def __init__(
        self,
        embedder: DualEmbedder,
        db: QdrantConnector,
        rrf_k: int = RRF_K,
    ):
        self.dense = DenseRetriever(embedder, db)
        self.sparse = SparseRetriever(embedder, db)
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 10,
    ) -> list[HybridRetrievalResult]:

        dense_results = self.dense.retrieve(
            query=query, collection_name=collection_name, limit=limit
        )
        print(f"retrieved {len(dense_results)} dense results")
        sparse_results = self.sparse.retrieve(
            query=query, collection_name=collection_name, limit=limit
        )
        print(f"retrieved {len(sparse_results)} sparse results")

        candidate_map: dict[str, HybridRetrievalResult] = {}

        # Dense results
        for result in dense_results:
            point_id = str(result.point_id)

            if point_id not in candidate_map:
                candidate_map[point_id] = HybridRetrievalResult.from_retrieval_result(
                    result,
                    dense_rank=result.rank,
                )
            else:
                candidate_map[point_id].dense_rank = result.rank

            candidate_map[point_id].rrf_score += 1.0 / (self.rrf_k + result.rank)

        # Sparse results
        for result in sparse_results:
            point_id = str(result.point_id)

            if point_id not in candidate_map:
                candidate_map[point_id] = HybridRetrievalResult.from_retrieval_result(
                    result,
                    sparse_rank=result.rank,
                )
            else:
                candidate_map[point_id].sparse_rank = result.rank

            candidate_map[point_id].rrf_score += 1.0 / (self.rrf_k + result.rank)

        candidates = list(candidate_map.values())

        candidates.sort(
            key=lambda result: result.rrf_score,
            reverse=True,
        )

        return candidates[:limit]
