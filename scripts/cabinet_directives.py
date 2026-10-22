#!/usr/bin/env python3
"""Curated Cabinet Directive register, validated snapshots and durable issue outbox."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    from scripts.sync_pin_sources import html_to_markdown, extract_modified_date
except ModuleNotFoundError:
    from sync_pin_sources import html_to_markdown, extract_modified_date

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
        entries.append(entry)
    if not entries or len({item['url'] for item in entries}) != len(entries):
        raise ValueError("Cabinet Directive register is empty or has duplicate URLs")
    return entries


def update_register(entry: dict, path: Path = REGISTER) -> None:
    """Update just the source's metadata, preserving prose and other entries."""
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING.finditer(text))
    for i, heading in enumerate(headings):
        if heading[2] != entry["url"]:
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[heading.end():end]
        for field in FIELDS:
            block = re.sub(rf"^- {re.escape(field)}: .+$", lambda m: f"- {field}: {entry[field]}", block, flags=re.MULTILINE)
        path.write_text(text[:heading.end()] + block + text[end:], encoding="utf-8")
        return
    fields = "\n".join(f"- {field}: {entry[field]}" for field in FIELDS)
    path.write_text(text.rstrip() + f"\n\n## [{entry['title']}]({entry['url']})\n\n{fields}\n", encoding="utf-8")


def fetch_source(url: str) -> str:
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
        return response.text
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
        if any(ROOT.glob("changes/*/change.json")):
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


def capture(entry: dict, source: dict, manifest: dict, *, detected: str, previous_url: str = "", manual_issue: int | None = None) -> dict | None:
    key = identity(entry["url"])
    previous = manifest["sources"].get(identity(previous_url) if previous_url else key)
    previous_text = confined_path(previous["current"]).read_text(encoding="utf-8") if previous else ""
    if previous_text and not previous_url and len(source["markdown"]) < len(previous_text) * 0.5:
        raise ValueError(f"Suspicious content shrink for {entry['url']}; last good capture retained")
    metadata = {field: entry[field] for field in FIELDS if field != "Date last modified"}
    fingerprint = hashlib.sha256((source["markdown"] + json.dumps(metadata, sort_keys=True)).encode()).hexdigest()
    if previous and previous.get("fingerprint") == fingerprint and not previous_url and manual_issue is None:
        return None
    transition = hashlib.sha256(f"{previous.get('event', '') if previous else ''}:{fingerprint}:{manual_issue or ''}".encode()).hexdigest()[:16]
    guid = f"cabdir_{key}_{detected}_{transition}"
    directory = ROOT / "changes" / guid
    directory.mkdir(parents=True, exist_ok=True)
    current = directory / "current.md"
    current.write_text(source["markdown"], encoding="utf-8")
    (directory / "current.html").write_text(source["html"], encoding="utf-8")
    prior = ""
    if previous:
        prior = (directory / "previous.md").as_posix()
        Path(prior).write_text(previous_text, encoding="utf-8")
        old_html = confined_path(previous["current"]).with_suffix(".html")
        if old_html.exists():
            (directory / "previous.html").write_bytes(old_html.read_bytes())
    event = {"guid": guid, "title": entry["title"], "url": entry["url"], "detected_date": detected,
             "change_type": "replacement" if previous_url else "changed" if previous else "newly_captured",
             "previous_url": previous_url, "current": current.as_posix(), "previous": prior,
             "metadata": metadata, "previous_metadata": previous.get("metadata", {}) if previous else {},
             "issue_number": manual_issue, "complete": False}
    (directory / "change.json").write_text(json.dumps(event, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["events"][guid] = event
    manifest["sources"][key] = {"url": entry["url"], "current": current.as_posix(), "fingerprint": fingerprint,
                                "event": guid, "metadata": metadata}
    return event


def sync_sources() -> None:
    entries = read_register()
    manifest = read_manifest()
    # Validate the entire batch before writing any source or register changes.
    sources = [(entry, parse_source(fetch_source(entry["url"]), entry["url"])) for entry in entries]
    for entry, source in sources:
        previous = manifest["sources"].get(identity(entry["url"]))
        if previous and len(source["markdown"]) < len(confined_path(previous["current"]).read_text(encoding="utf-8")) * 0.5:
            raise ValueError(f"Suspicious content shrink: {entry['url']}")
    for entry, source in sources:
        entry["Date last modified"] = source["modified"]
        if entry["Date Published"] == "Unknown":
            entry["Date Published"] = source["published"]
        capture(entry, source, manifest, detected=today())
        update_register(entry)
    save_manifest(manifest)


def publish_issues() -> None:
    from github import Auth, Github
    try:
        from scripts.create_issues_with_screenshots import dispatch_enrichment
    except ModuleNotFoundError:
        from create_issues_with_screenshots import dispatch_enrichment
    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    repo = Github(auth=Auth.Token(token)).get_repo(repo_name)
    manifest = read_manifest()
    existing_labels = {label.name for label in repo.get_labels()}
    for name, color in [(LABEL, "b60205"), ("policy-update", "0366d6"), ("🪄📝AutoAnalyzed", "7057ff")]:
        if name not in existing_labels:
            repo.create_label(name=name, color=color)
    issues = None
    failures = []
    for event in manifest["events"].values():
        if event["complete"]:
            continue
        marker = f"<!-- policy-hawk:cabdir:{event['guid']} -->"
        if event["issue_number"]:
            issue = repo.get_issue(number=int(event["issue_number"]))
        else:
            # Recover an issue created before a runner stopped or a state push failed.
            if issues is None:
                issues = list(repo.get_issues(state="all", labels=[LABEL]))
            issue = next((item for item in issues if marker in (item.body or "")), None)
            if issue is None:
                body = (f"{marker}\n**Title:** {event['title']}\n**Link:** {event['url']}\n"
                        f"**Category:** Cabinet Directive\n**GUID:** {event['guid']}\n"
                        f"**Detected date:** {event['detected_date']}\n"
                        f"**Cabinet metadata:** {ROOT}/changes/{event['guid']}/change.json\n\n"
                        f"Change: {event['change_type']}. Required screenshots, source comparison, and quarterly synopsis are captured during enrichment. "
                        "A first repository capture is not evidence that the directive was newly issued.")
                issue = repo.create_issue(title=f"CABDir {event['change_type']}: {event['title']}", body=body, labels=[LABEL, "policy-update"])
                issues.append(issue)
            event["issue_number"] = issue.number
            save_manifest(manifest)
        if any(label.name == "🪄📝AutoAnalyzed" for label in issue.labels):
            event["complete"] = True
        elif not dispatch_enrichment(repo_name, issue.number, token, ref=repo.default_branch):
            failures.append(issue.number)
        save_manifest(manifest)
    if failures:
        raise RuntimeError(f"Cabinet enrichment dispatch failed; retained for retry: {failures}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sync", "publish"])
    arguments = parser.parse_args()
    sync_sources() if arguments.command == "sync" else publish_issues()
