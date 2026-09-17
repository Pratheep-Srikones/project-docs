from dataclasses import dataclass
from pathlib import Path


@dataclass
class MarkdownDocument:
    path: str
    content: str


class MarkdownLoader:
    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)

    def load(self) -> list[MarkdownDocument]:
        documents = []
        print(f"Searching for markdown files in {self.docs_dir}")
        for path in sorted(self.docs_dir.rglob("*.md")):
            content = path.read_text(encoding="utf-8")

            documents.append(
                MarkdownDocument(
                    path=str(path),
                    content=content,
                )
            )

        return documents