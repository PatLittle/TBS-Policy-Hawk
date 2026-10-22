#!/usr/bin/env python3
"""Monitor registered Cabinet Directive URLs; share the normal issue handoff. Analysis belongs to the agent skill."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    from scripts.sync_pin_sources import html_to_markdown, extract_modified_date, _append_csv_rows, NEW_ITEM_HEADERS
except ModuleNotFoundError:
    from sync_pin_sources import html_to_markdown, extract_modified_date, _append_csv_rows, NEW_ITEM_HEADERS

REGISTER = Path("CabinetDirectives.md")
ROOT = Path("data/CabinetDirectives")
MANIFEST = ROOT / "manifest.json"
LABEL = "🍁CabinetDir🏛️"
STATUSES = {"Announced", "In Force", "Superseded", "Retired"}
FIELDS = ("Status", "Date Published", "Date of effect", "Date last modified")
SOURCE_HEADERS = {
    "User-Agent": "TBS-Policy-Hawk/1.0 (+https://github.com/PatLittle/TBS-Policy-Hawk)",
    "Referer": "https://www.canada.ca/",
}
HEADING = re.compile(r"^## \[([^\n]+)\]\((https://[^\s)]+)\)\s*$", re.MULTILINE)


def today() -> str:
    return datetime.now(ZoneInfo("America/Toronto")).date().isoformat()


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.port
            or not (host == "canada.ca" or host.endswith(".canada.ca") or host.endswith(".gc.ca"))):
        raise ValueError(f"Cabinet Directive source must be an HTTPS Government of Canada URL: {url}")
    return url


def identity(url: str) -> str:
    return hashlib.sha256(validate_url(url).encode()).hexdigest()[:16]


def read_register(path: Path = REGISTER) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING.finditer(text))
    if len(headings) != len(re.findall(r"^## ", text, re.MULTILINE)):
        raise ValueError("Every Cabinet register section must have a linked HTTPS source heading")
    entries = []
    for i, heading in enumerate(headings):
        block = text[heading.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)]
        entry = {"title": heading[1], "url": validate_url(heading[2])}
        for field in FIELDS:
            match = re.search(rf"^- {re.escape(field)}: (.+)$", block, re.MULTILINE)
            if not match:
                raise ValueError(f"Missing {field} for {entry['title']}")
            value = match[1].strip()
            if field == "Status":
                if value not in STATUSES:
                    raise ValueError(f"Invalid Cabinet Directive status: {value}")
            elif value != "Unknown":
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError(f"Invalid {field}: {value}")
                datetime.strptime(value, "%Y-%m-%d")
            entry[field] = value
        archive = re.search(r"^- Archive: ([A-Za-z0-9_-]+)$", block, re.MULTILINE)
        if archive:
            entry["Archive"] = archive[1]
        entries.append(entry)
    if not entries or len({item['url'] for item in entries}) != len(entries):
        raise ValueError("Cabinet Directive register is empty or has duplicate URLs")
    return entries


def update_register(entry: dict, path: Path = REGISTER) -> None:
    """Update just the source's metadata, preserving prose and other entries."""
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING.finditer(text))
    fields = FIELDS + (("Archive",) if entry.get("Archive") else ())
    for i, heading in enumerate(headings):
        if heading[2] != entry["url"]:
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[heading.end():end]
        for field in fields:
            block, count = re.subn(rf"^- {re.escape(field)}: .+$", lambda m: f"- {field}: {entry[field]}", block, flags=re.MULTILINE)
            if not count:
                block = block.rstrip() + f"\n\n- {field}: {entry[field]}\n\n"
        path.write_text(text[:heading.end()] + block + text[end:], encoding="utf-8")
        return
    metadata = "\n".join(f"- {field}: {entry[field]}" for field in fields)
    path.write_text(text.rstrip() + f"\n\n## [{entry['title']}]({entry['url']})\n\n{metadata}\n", encoding="utf-8")


class SourceUnavailable(ValueError):
    """A successful HTTP response explicitly says the page was not found."""


def fetch_source(url: str) -> dict:
    validate_url(url)
    # Validate each redirect before following it, including URLs from manual issues.
    for _ in range(6):
        for attempt in range(3):
            try:
                print(f"Fetching Cabinet source (attempt {attempt + 1}/3): {url}", flush=True)
                headers = SOURCE_HEADERS if attempt == 0 else {"Referer": "https://www.canada.ca/"}
                response = requests.get(url, timeout=(10, 30), allow_redirects=False, headers=headers)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if attempt == 2 or (status and status not in {408, 429, 500, 502, 503, 504}):
                    raise
                print(f"Transient Cabinet fetch failure for {url}: {type(exc).__name__}; retrying", flush=True)
                time.sleep(2 ** attempt)
        if response.is_redirect:
            from urllib.parse import urljoin
            url = validate_url(urljoin(url, response.headers["Location"]))
            continue
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError(f"Cabinet source is not HTML: {url}")
        response.encoding = "utf-8"
        heading = BeautifulSoup(response.text, "lxml").select_one("main h1, h1")
        if heading and re.search(r"page not found|couldn.t find|404", heading.get_text(" "), re.I):
            raise SourceUnavailable(f"Soft 404: {url}")
        source = parse_source(response.text, url)
        source["resolved_url"] = url
        return source
    raise ValueError("Too many Cabinet Directive redirects")


def parse_source(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main")
    heading = main.find("h1") if main else None
    if not heading or "cabinet directive" not in heading.get_text(" ", strip=True).casefold():
        raise ValueError(f"Not a Cabinet Directive content page: {url}")
    if re.search(r"request rejected|access denied|an error occurred while processing", main.get_text(" "), re.I):
        raise ValueError(f"Source error page: {url}")
    modified = extract_modified_date(soup)[:10]
    for selector in [".pagedetails", ".page-details", "#wb-share", ".gc-pg-hlpfl", "#gc-pg-hlpfl", "#wb-dtmd", "nav", "script", "style", "noscript"]:
        for node in main.select(selector):
            node.decompose()
    title, markdown = html_to_markdown(str(main), url)
    if len(markdown) < 300:
        raise ValueError(f"Incomplete Cabinet Directive content: {url}")
    issued = soup.select_one('meta[name="dcterms.issued"]')
    published = str(issued.get("content", ""))[:10] if issued else ""
    return {"title": title, "markdown": markdown, "html": html,
            "published": published if re.fullmatch(r"\d{4}-\d{2}-\d{2}", published) else "Unknown",
            "modified": modified if re.fullmatch(r"\d{4}-\d{2}-\d{2}", modified) else "Unknown"}


def read_manifest() -> dict:
    if not MANIFEST.exists():
        if any(ROOT.rglob("change.json")):
            raise ValueError("Cabinet manifest is missing but captures exist; restore the last good manifest")
        return {"version": 1, "sources": {}, "events": {}}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or manifest.get("version") != 1
            or not isinstance(manifest.get("sources"), dict) or not isinstance(manifest.get("events"), dict)):
        raise ValueError("Invalid Cabinet Directive manifest")
    return manifest


def save_manifest(manifest: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST)


def confined_path(value: str) -> Path:
    path = Path(value).resolve()
    path.relative_to(ROOT.resolve())
    return path


def archive_name(entry: dict, manifest: dict) -> str:
    previous = manifest["sources"].get(identity(entry["url"]), {})
    name = entry.get("Archive") or previous.get("archive")
    if not name:
        title = re.sub(r"^Cabinet Directive (?:on )?(?:the )?", "", entry["title"], flags=re.I)
        title = re.sub(r"[^A-Za-z0-9]+", "", title)[:70]
        published = entry["Date Published"] if entry["Date Published"] != "Unknown" else today()
        name = f"CD_{title}{published.replace('-', '')}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", name):
        raise ValueError("Archive must be a readable folder name without path separators")
    return name


def capture(entry: dict, source: dict | None, manifest: dict, *, detected: str,
            previous_url: str = "", manual_issue: int | None = None, change: str = "") -> dict | None:
    """Archive evidence; first captures are quiet baselines, not policy-change events."""
    key = identity(entry["url"])
    previous = manifest["sources"].get(identity(previous_url) if previous_url else key)
    old_text = confined_path(previous["current"]).read_text(encoding="utf-8") if previous else ""
    if source and old_text and not previous_url and len(source["markdown"]) < len(old_text) * 0.5:
        raise ValueError(f"Suspicious content shrink: {entry['url']}; baseline retained")
    metadata = {field: entry[field] for field in FIELDS if field != "Date last modified"}
    fingerprint = hashlib.sha256((source["markdown"] + json.dumps(metadata, sort_keys=True)).encode()).hexdigest() if source else ""
    resolved = source.get("resolved_url", entry["url"]) if source else ""
    if (source and previous and previous.get("fingerprint") == fingerprint and not previous_url
            and previous.get("resolved_url", entry["url"]) == resolved and not change):
        return None
    redirected = previous and source and previous.get("fingerprint") == fingerprint and previous.get("resolved_url", entry["url"]) != resolved
    kind = change or ("replacement" if previous_url else "redirected" if redirected else "changed" if previous else "baseline")
    folder = archive_name(entry, manifest)
    entry["Archive"] = folder
    directory = ROOT / folder / "captures" / detected.replace("-", "")
    sequence = 1
    while directory.exists():
        sequence += 1
        directory = directory.with_name(detected.replace("-", "") + f"_{sequence:02d}")
    directory.mkdir(parents=True)
    guid = f"{folder}_{kind}_{directory.name}"
    current, prior = "", ""
    if source:
        current = (directory / "current.md").as_posix()
        Path(current).write_text(source["markdown"], encoding="utf-8")
        (directory / "current.html").write_text(source["html"], encoding="utf-8")
    if previous:
        prior = (directory / "previous.md").as_posix()
        Path(prior).write_text(old_text, encoding="utf-8")
        old_html = confined_path(previous["current"]).with_suffix(".html")
        if old_html.exists():
            (directory / "previous.html").write_bytes(old_html.read_bytes())
    event = {"guid": guid, "title": entry["title"], "url": entry["url"],
             "detected_date": detected, "change_type": kind, "previous_url": previous_url,
             "current": current, "previous": prior, "resolved_url": resolved,
             "previous_resolved_url": previous.get("resolved_url", previous["url"]) if previous else "",
             "metadata": metadata, "issue_number": manual_issue, "complete": kind == "baseline"}
    (directory / "change.json").write_text(json.dumps(event, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["events"][guid] = event
    if source:
        manifest["sources"][key] = {"url": entry["url"], "archive": folder, "current": current,
                                    "fingerprint": fingerprint, "resolved_url": resolved,
                                    "event": guid, "metadata": metadata}
    return event


def sync_sources() -> None:
    """Watch known URLs only; do not discover or auto-analyze new instruments."""
    manifest = read_manifest()
    issue_map_path = Path("data/issue_map.json")
    issue_map = json.loads(issue_map_path.read_text(encoding="utf-8")) if issue_map_path.exists() else {}
    if not isinstance(issue_map, dict):
        raise ValueError("Issue map must be an object; refusing to modify source tracking")
    for entry in read_register():
        key = identity(entry["url"])
        previous = manifest["sources"].get(key)
        try:
            source = fetch_source(entry["url"])
            if entry["Date Published"] == "Unknown":
                entry["Date Published"] = source["published"]
            status = previous.get("availability", "available") if previous else "available"
            kind = "restored" if status == "unavailable" else ""
            capture(entry, source, manifest, detected=today(), change=kind)
            current = manifest["sources"][key]
            current.pop("missing_checks", None)
            current.pop("availability", None)
            entry["Date last modified"] = source["modified"]
            update_register(entry)
        except (requests.RequestException, ValueError) as exc:
            code = getattr(getattr(exc, "response", None), "status_code", None)
            missing = code in {404, 410} or isinstance(exc, SourceUnavailable)
            if missing and previous:
                previous["missing_checks"] = min(2, previous.get("missing_checks", 0) + 1)
                if previous["missing_checks"] == 2 and previous.get("availability") != "unavailable":
                    capture(entry, None, manifest, detected=today(), change="unavailable")
                    previous["availability"] = "unavailable"
            elif previous and previous.get("availability") != "unavailable":
                previous.pop("missing_checks", None)
            # Timeouts, access blocks, parser failures and shrinkage do not prove withdrawal.
            print(f"::warning::Cabinet source retained for {entry['url']}: {exc}", flush=True)
    save_manifest(manifest)
    rows = []
    for event in manifest["events"].values():
        if event.get("complete") or event.get("issue_number") or event["guid"] in issue_map:
            continue
        if event["change_type"] not in {"changed", "unavailable", "restored", "redirected"}:
            continue
        evidence = event["current"] or event["previous"]
        metadata_path = Path(evidence).with_name("change.json")
        rows.append({"guid": event["guid"], "title": event["title"], "link": event["url"],
                     "category": "Cabinet Directive", "filename": metadata_path.as_posix(),
                     "updated_date": event["detected_date"], "change_type": "cabinet",
                     "change_summary": event["change_type"], "source_id": "Cabinet Directive"})
    _append_csv_rows(Path("data/new_items.csv"), NEW_ITEM_HEADERS, rows)


if __name__ == "__main__":
    sync_sources()
