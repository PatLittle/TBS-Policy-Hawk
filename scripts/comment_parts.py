import re
from typing import List, Optional


COMMENT_LIMIT = 60000
COMMENT_CONTENT_LIMIT = 58000
COMMENT_PART_MARKER = "<!-- policy-hawk:comment-part {part}/{total} -->"


def split_comment_text(text: str, limit: int = COMMENT_CONTENT_LIMIT) -> List[str]:
    """Split text without dropping content, preferring paragraph and line boundaries."""
    if limit < 1:
        raise ValueError("Comment split limit must be positive.")
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    current = ""
    paragraphs = re.split(r"(?<=\n\n)", text)

    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) > limit:
            chunks.append(current)
            current = ""

        while len(paragraph) > limit:
            split_at = paragraph.rfind("\n", 0, limit + 1)
            split_at = split_at + 1 if split_at >= 0 else limit
            if split_at == 0:
                split_at = limit
            chunks.append(paragraph[:split_at])
            paragraph = paragraph[split_at:]

        if paragraph:
            current += paragraph

    if current or not chunks:
        chunks.append(current)

    return chunks


def build_comment_parts(
    text: str,
    marker: str,
    heading: Optional[str] = None,
    fenced_language: Optional[str] = None,
    collapsible: bool = False,
) -> List[str]:
    """Build independently renderable, numbered GitHub issue comments."""
    chunks = split_comment_text(text)
    total = len(chunks)
    bodies = []

    for index, chunk in enumerate(chunks, start=1):
        part_label = f" (Part {index} of {total})" if total > 1 else ""
        sections = [
            marker,
            COMMENT_PART_MARKER.format(part=index, total=total),
        ]
        if heading:
            sections.append(f"### {heading}{part_label}")
        elif total > 1:
            sections.append(f"**Part {index} of {total}**")

        if fenced_language is not None:
            rendered_chunk = f"```{fenced_language}\n{chunk}\n```"
        else:
            rendered_chunk = chunk

        if collapsible:
            summary = f"View {heading.lower() if heading else 'content'}{part_label}"
            rendered_chunk = f"<details><summary>{summary}</summary>\n\n{rendered_chunk}\n\n</details>"

        sections.append(rendered_chunk)
        body = "\n\n".join(sections)
        if len(body) > COMMENT_LIMIT:
            raise ValueError(f"Generated comment part exceeds {COMMENT_LIMIT} characters.")
        bodies.append(body)

    return bodies


def post_comment_parts(
    issue,
    text: str,
    marker: str,
    heading: Optional[str] = None,
    fenced_language: Optional[str] = None,
    collapsible: bool = False,
) -> None:
    """Post every missing part and safely resume after a partially completed run."""
    bodies = build_comment_parts(
        text,
        marker,
        heading=heading,
        fenced_language=fenced_language,
        collapsible=collapsible,
    )
    existing_bodies = [
        comment.body or ""
        for comment in issue.get_comments()
        if marker in (comment.body or "")
    ]

    legacy_bodies = [
        body
        for body in existing_bodies
        if "<!-- policy-hawk:comment-part " not in body
    ]
    if legacy_bodies and not any("...(truncated)" in body for body in legacy_bodies):
        return

    for body in bodies:
        part_marker_match = re.search(
            r"<!-- policy-hawk:comment-part \d+/\d+ -->",
            body,
        )
        if part_marker_match is None:
            raise ValueError("Generated comment is missing its part marker.")
        part_marker = part_marker_match.group(0)
        if any(part_marker in existing for existing in existing_bodies):
            continue
        issue.create_comment(body)
