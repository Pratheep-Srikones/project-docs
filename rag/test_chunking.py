from indexer.chunker import MarkdownChunker
from indexer.loader import MarkdownLoader

loader = MarkdownLoader("../docs")
documents = loader.load()

print(f"Loaded {len(documents)} documents")

chunker = MarkdownChunker(
    chunk_size=400,
    overlap=80,
)

for document in documents[:1]:
    print(f"\nSOURCE: {document.path}")

    chunks = chunker.chunk(
        document.content,
        document.path,
    )

    print(f"Chunks: {len(chunks)}")

    for chunk in chunks:
        print("\n" + "=" * 80)
        print(f"CHUNK {chunk.chunk_index}")
        print(f"HEADINGS: {' > '.join(chunk.heading_path)}")
        print("-" * 80)
        print(chunk.text)
