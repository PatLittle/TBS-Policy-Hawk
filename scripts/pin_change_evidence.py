#!/usr/bin/env python3

"""Load immutable PIN change evidence without allowing arbitrary file reads."""

from __future__ import annotations

import json
import re
from pathlib import Path


PIN_CHANGES_ROOT = Path("data/PINs/changes")
VOLATILE_METADATA = re.compile(
    r"^- (?:Source page modified|Captured at \(UTC\)|Fetch error):.*$",
    flags=re.MULTILINE,
)


def canonical_pin_text(text: str) -> str:
    """Remove collection metadata which does not describe notice content."""
    text = VOLATILE_METADATA.sub("", text or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + ("\n" if text.strip() else "")


def _confined_path(repo_root: Path, value: str, *, must_exist: bool = True) -> Path:
    if not value:
        raise ValueError("PIN evidence path is empty.")
    candidate = (repo_root / value).resolve()
    changes_root = (repo_root / PIN_CHANGES_ROOT).resolve()
    try:
        candidate.relative_to(changes_root)
    except ValueError as exc:
        raise ValueError(f"PIN evidence path is outside {PIN_CHANGES_ROOT}: {value}") from exc
    if must_exist and not candidate.is_file():
        raise FileNotFoundError(f"PIN evidence file does not exist: {value}")
    return candidate


def load_pin_change(metadata_path: str, repo_root: Path | str = Path(".")) -> dict:
    """Load a change manifest and its current/previous markdown evidence."""
    root = Path(repo_root).resolve()
    metadata_file = _confined_path(root, metadata_path)
    if metadata_file.name != "change.json":
        raise ValueError("PIN metadata must point to a change.json file.")

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("PIN change metadata must be a JSON object.")

    def load_optional(key: str) -> tuple[str, str]:
        value = metadata.get(key) or metadata.get(f"{key}_path") or ""
        if not value:
            return "", ""
        evidence_path = _confined_path(root, str(value))
        return evidence_path.relative_to(root).as_posix(), evidence_path.read_text(encoding="utf-8")

    previous_path, previous_text = load_optional("previous")
    current_path, current_text = load_optional("current")
    # Sync records use change_type="pin" for routing and pin_change for the
    # actual transition. Accept older experimental names as fallbacks.
    change_type = str(
        metadata.get("pin_change") or metadata.get("change") or metadata.get("change_type") or "changed"
    ).lower()
    if change_type not in {"added", "changed", "removed"}:
        raise ValueError(f"Unsupported PIN change type: {change_type}")
    if change_type == "added" and not current_text:
        raise ValueError("An added PIN requires current evidence.")
    if change_type == "changed" and (not previous_text or not current_text):
        raise ValueError("A changed PIN requires previous and current evidence.")
    if change_type == "removed" and not previous_text:
        raise ValueError("A removed PIN requires previous evidence.")

    return {
        "metadata": metadata,
        "metadata_path": metadata_file.relative_to(root).as_posix(),
        "change_dir": metadata_file.parent,
        "change_type": change_type,
        "previous_path": previous_path,
        "previous_text": previous_text,
        "current_path": current_path,
        "current_text": current_text,
        "canonical_previous": canonical_pin_text(previous_text),
        "canonical_current": canonical_pin_text(current_text),
    }
