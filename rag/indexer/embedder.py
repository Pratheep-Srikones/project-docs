from dataclasses import dataclass, field

from fastembed import SparseTextEmbedding, TextEmbedding
from indexer.chunker import DocumentChunk

DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"


@dataclass
class EmbeddedChunk(DocumentChunk):
    dense_vector: list[float] = field(default_factory=list)
    sparse_vector: dict = field(default_factory=dict)


class DualEmbedder:
    def __init__(
        self,
        dense_model_name: str = DENSE_MODEL,
        sparse_model_name: str = SPARSE_MODEL,
    ):
        self.dense_model = TextEmbedding(dense_model_name)
        self.sparse_model = SparseTextEmbedding(sparse_model_name)

        self._embedding_dimension = self._get_embedding_dimension()

    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dimension

    def dual_embed(
        self,
        chunks: list[DocumentChunk],
    ) -> list[EmbeddedChunk]:

        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]

        dense_vectors = self._dense_embed_texts(texts)
        sparse_vectors = self._sparse_embed_texts(texts)

        if len(dense_vectors) != len(chunks):
            raise RuntimeError(
                "Number of dense embeddings does not match number of chunks"
            )

        if len(sparse_vectors) != len(chunks):
            raise RuntimeError(
                "Number of sparse embeddings does not match number of chunks"
            )

        embedded_chunks: list[EmbeddedChunk] = []

        for chunk, dense_vector, sparse_vector in zip(
            chunks,
            dense_vectors,
            sparse_vectors,
        ):
            embedded_chunks.append(
                self._build_embedded_chunk(
                    chunk,
                    dense_vector,
                    sparse_vector,
                )
            )

        return embedded_chunks

    def dense_embed_query(self, query: str):
        return self._dense_embed_texts([query])[0]

    def sparse_embed_query(self, query: str) -> dict:
        return self._sparse_embed_texts([query])[0]

    def _dense_embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        generator = self.dense_model.embed(texts)

        return [
            vector.tolist() if hasattr(vector, "tolist") else list(vector)
            for vector in generator
        ]

    def _sparse_embed_texts(
        self,
        texts: list[str],
    ) -> list[dict]:

        generator = self.sparse_model.embed(texts)

        sparse_vectors = []

        for vector in generator:
            indices = (
                vector.indices.tolist()
                if hasattr(vector.indices, "tolist")
                else list(vector.indices)
            )

            values = (
                vector.values.tolist()
                if hasattr(vector.values, "tolist")
                else list(vector.values)
            )

            sparse_vectors.append(
                {
                    "indices": indices,
                    "values": values,
                }
            )

        return sparse_vectors

    def _get_embedding_dimension(self) -> int:
        sample = self._dense_embed_texts(["testing"])

        if not sample:
            raise RuntimeError("Dense embedding model returned no vector")

        return len(sample[0])

    @staticmethod
    def _build_embedded_chunk(
        chunk: DocumentChunk,
        dense_vector: list[float],
        sparse_vector: dict,
    ) -> EmbeddedChunk:

        return EmbeddedChunk(
            text=chunk.text,
            source=chunk.source,
            heading_path=chunk.heading_path,
            chunk_index=chunk.chunk_index,
            images=chunk.images,
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
        )
