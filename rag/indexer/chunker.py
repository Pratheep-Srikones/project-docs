import re
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class DocumentChunk:
    text: str
    source: str
    heading_path: list[str]
    chunk_index: int
    images: list[str] = field(default_factory=list)


@dataclass
class MarkdownBlock:
    text: str
    heading_path: list[str]
    images: list[str] = field(default_factory=list)


class MarkdownChunker:
    """
    Converts Markdown documents into structure-aware chunks.

    Strategy:
    - Respect Markdown heading hierarchy.
    - Keep code blocks intact.
    - Keep images as metadata and add an image marker to the text.
    - Chunk within semantic sections.
    - Use overlap between chunks belonging to the same section.
    """

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 80,
    ):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    # create chunks on given string
    def chunk(
        self,
        content: str,
        source: str,
    ) -> list[DocumentChunk]:

        sections = self._parse_sections(content)

        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for section in sections:
            section_chunks = self._chunk_section(
                section,
                source,
                chunk_index,
            )

            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        return chunks

    # break the content into sections
    def _parse_sections(self, content: str) -> list[list[MarkdownBlock]]:
        lines = content.splitlines()

        sections: list[list[MarkdownBlock]] = []
        heading_stack: list[str] = []

        current_lines: list[str] = []
        current_images: list[str] = []
        current_section: list[MarkdownBlock] = []

        in_code_block = False

        # flush the content of already existing block
        def flush_block():
            nonlocal current_lines, current_images, current_section

            if not current_lines:
                return

            text = "\n".join(current_lines).strip()

            if text:
                current_section.append(
                    MarkdownBlock(
                        text=text,
                        heading_path=heading_stack.copy(),
                        images=current_images.copy(),
                    )
                )

            current_lines = []
            current_images = []

        def flush_section():
            nonlocal current_section

            # flush existing content
            flush_block()

            # save sections that contain actual content
            if current_section:
                sections.append(current_section)

            current_section = []

        for line in lines:
            # code block
            if line.strip().startswith("```"):
                current_lines.append(line)
                # toggle
                in_code_block = not in_code_block
                continue

            if in_code_block:
                current_lines.append(line)
                continue

            # heading
            heading_match = self.HEADING_RE.match(line)

            if heading_match:
                # finish content belonging to the previous heading.
                flush_section()

                level = len(heading_match.group(1))
                heading = heading_match.group(2).strip()

                # update heading hierarchy.
                heading_stack = heading_stack[: level - 1]
                heading_stack.append(heading)

                continue

            # image handling
            image_matches = self.IMAGE_RE.findall(line)

            if image_matches:
                for alt_text, image_path in image_matches:
                    current_images.append(image_path)

                image_text = self._image_marker(image_matches)
                current_lines.append(image_text)
                continue

            # normal content
            if line.strip():
                current_lines.append(line)

            # empty lines
            elif current_lines:
                flush_block()

        # flush final section
        flush_section()

        return sections

    # section chunking
    def _chunk_section(
        self,
        blocks: list[MarkdownBlock],
        source: str,
        starting_index: int,
    ) -> list[DocumentChunk]:

        if not blocks:
            return []

        chunks: list[DocumentChunk] = []

        current_blocks: list[MarkdownBlock] = []
        current_size = 0

        chunk_index = starting_index

        for block in blocks:
            block_size = self._token_estimate(block.text)

            # normal case: block fits
            if current_blocks and current_size + block_size > self.chunk_size:
                chunks.append(
                    self._build_chunk(
                        current_blocks,
                        source,
                        chunk_index,
                    )
                )

                chunk_index += 1

                # Keep overlap ONLY within this semantic section.
                current_blocks = self._get_overlap_blocks(current_blocks)

                current_size = sum(self._token_estimate(b.text) for b in current_blocks)

            current_blocks.append(block)
            current_size += block_size

            # if a single block is larger than chunk_size
            # keep it intact rather than destroying its structure
            if current_size > self.chunk_size and len(current_blocks) == 1:
                chunks.append(
                    self._build_chunk(
                        current_blocks,
                        source,
                        chunk_index,
                    )
                )

                chunk_index += 1

                current_blocks = []
                current_size = 0

        # remaining blocks
        if current_blocks:
            chunks.append(
                self._build_chunk(
                    current_blocks,
                    source,
                    chunk_index,
                )
            )

        return chunks

    # chunk construction
    def _build_chunk(
        self,
        blocks: list[MarkdownBlock],
        source: str,
        chunk_index: int,
    ) -> DocumentChunk:

        heading_path = blocks[-1].heading_path

        context = self._build_context(heading_path)

        body = "\n\n".join(block.text for block in blocks)

        text_parts = []

        if context:
            text_parts.append(context)

        text_parts.append(body)

        text = "\n\n".join(text_parts)

        images = []

        for block in blocks:
            for image in block.images:
                if image not in images:
                    images.append(image)

        return DocumentChunk(
            text=text,
            source=source,
            heading_path=heading_path,
            chunk_index=chunk_index,
            images=images,
        )

    # context
    @staticmethod
    def _build_context(
        heading_path: list[str],
    ) -> str:

        if not heading_path:
            return ""

        return "Section: " + " > ".join(heading_path)

    # overlap
    def _get_overlap_blocks(
        self,
        blocks: list[MarkdownBlock],
    ) -> list[MarkdownBlock]:

        overlap_blocks: list[MarkdownBlock] = []
        size = 0

        for block in reversed(blocks):
            block_size = self._token_estimate(block.text)

            # if overlap size is exceeded
            if size + block_size > self.overlap:
                break

            overlap_blocks.insert(
                0,
                block,
            )

            size += block_size

        return overlap_blocks

    # images
    @staticmethod
    def _image_marker(
        images: list[tuple[str, str]],
    ) -> str:

        markers = []

        for alt_text, image_path in images:
            if alt_text:
                markers.append(f"[Image: {alt_text}]")
            else:
                markers.append(f"[Image: {image_path}]")

        return "\n".join(markers)

    @staticmethod
    def _token_estimate(
        text: str,
    ) -> int:
        """
        Cheap token approximation.

        This will later be replaced with the BGE tokenizer
        once we introduce the embedding model.
        """

        return len(text.split())
