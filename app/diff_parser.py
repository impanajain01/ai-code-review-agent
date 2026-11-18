"""
Parse a unified diff into reviewable chunks.

Each chunk is a piece of one file's diff, small enough to send to an LLM.
Added and context lines are prefixed with their line number in the NEW
version of the file, so review comments can later be attached to exact lines.
"""

from dataclasses import dataclass

from unidiff import PatchSet

MAX_CHUNK_CHARS = 6000

SKIP_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
}
SKIP_SUFFIXES = (
    ".lock", ".min.js", ".min.css", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".woff", ".woff2",
)


@dataclass
class DiffChunk:
    filename: str
    text: str


def should_review(path: str) -> bool:
    """Skip generated, binary, and lock files: reviewing them wastes tokens."""
    name = path.rsplit("/", 1)[-1]
    return name not in SKIP_FILENAMES and not path.endswith(SKIP_SUFFIXES)


def _render_hunk(hunk) -> list[str]:
    """Render one hunk as text lines with new-file line numbers."""
    lines = [f"@@ -{hunk.source_start} +{hunk.target_start} @@"]
    for line in hunk:
        content = line.value.rstrip("\n")
        if line.is_removed:
            lines.append(f"      - {content}")
        elif line.target_line_no is None:
            continue  # e.g. "\ No newline at end of file"
        elif line.is_added:
            lines.append(f"{line.target_line_no:>5} + {content}")
        else:
            lines.append(f"{line.target_line_no:>5}   {content}")
    return lines


def _split_lines(lines: list[str], limit: int):
    """Yield groups of lines whose combined size stays under `limit`."""
    group, size = [], 0
    for line in lines:
        if group and size + len(line) + 1 > limit:
            yield group
            group, size = [], 0
        group.append(line)
        size += len(line) + 1
    if group:
        yield group


def parse_diff(diff_text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[DiffChunk]:
    """Turn a unified diff into a list of reviewable chunks."""
    chunks: list[DiffChunk] = []

    for patched_file in PatchSet(diff_text):
        if (
            patched_file.is_removed_file
            or getattr(patched_file, "is_binary_file", False)
            or not should_review(patched_file.path)
        ):
            continue

        # Break each hunk into blocks that individually fit the limit
        blocks: list[str] = []
        for hunk in patched_file:
            for group in _split_lines(_render_hunk(hunk), max_chars):
                blocks.append("\n".join(group))

        # Pack blocks into chunks without exceeding the limit
        current: list[str] = []
        size = 0
        for block in blocks:
            if current and size + len(block) + 1 > max_chars:
                chunks.append(DiffChunk(patched_file.path, "\n".join(current)))
                current, size = [], 0
            current.append(block)
            size += len(block) + 1
        if current:
            chunks.append(DiffChunk(patched_file.path, "\n".join(current)))

    return chunks