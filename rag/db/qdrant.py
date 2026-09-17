import hashlib

from indexer.embedder import EmbeddedChunk
from qdrant_client import QdrantClient, models

QDRANT_URL = "http://localhost:6333"


class QdrantConnector:
    def __init__(self, dense_dim: int, url: str = QDRANT_URL):
        self.dense_dim = dense_dim
        self.client = QdrantClient(url=url)

    def collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)

    def ensure_collection(self, collection: str = "documents") -> None:
        if not self.client.collection_exists(collection):
            print("Collection not found, Creating...")
            self.client.create_collection(
                collection_name=collection,
                vectors_config={
                    "dense": models.VectorParams(
                        size=self.dense_dim, distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=False)
                    )
                },
            )

    def upsert_chunks(
        self,
        collection_name="documents",
        embedded_chunks: list[EmbeddedChunk] | None = None,
    ) -> int:
        if not embedded_chunks:
            print("No chunks inserted return 0")
            return 0

        self.ensure_collection(collection_name)
        print("Collection ensured, Inserting....")

        points = []

        for chunk in embedded_chunks:
            chunk_id_str = chunk.source + "_" + str(chunk.chunk_index)

            point_id = int(
                hashlib.md5(chunk_id_str.encode("utf-8")).hexdigest()[:16], 16
            )

            dense_vec = chunk.dense_vector
            sparse_dict = chunk.sparse_vector

            sparse_vec = models.SparseVector(
                indices=sparse_dict["indices"], values=sparse_dict["values"]
            )

            payload = {
                "source": chunk.source,
                "chunk_id": chunk_id_str,
                "text": chunk.text,
                "heading_path": chunk.heading_path,
                "images": chunk.images,
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={"dense": dense_vec, "sparse": sparse_vec},
                    payload=payload,
                )
            )

        self.client.upsert(collection_name=collection_name, points=points)

        return len(points)
