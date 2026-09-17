from db.qdrant import QdrantConnector
from indexer.chunker import MarkdownChunker
from indexer.embedder import DualEmbedder
from indexer.loader import MarkdownLoader

loader = MarkdownLoader("../docs")
documents = loader.load()

print(f"Loaded {len(documents)} documents")

chunker = MarkdownChunker(
    chunk_size=400,
    overlap=80,
)

embedder = DualEmbedder()
db = QdrantConnector(dense_dim=embedder.embedding_dimension)

for document in documents[:1]:
    print(f"\nSOURCE: {document.path}")

    chunks = chunker.chunk(
        document.content,
        document.path,
    )

    print(f"Chunks: {len(chunks)}")
    e_chunks = embedder.dual_embed(chunks)

    print(f"Embedded: {len(e_chunks)}")
    l = db.upsert_chunks(embedded_chunks=e_chunks)

    print(f"Inserted {l} chunks to Qdrant")
