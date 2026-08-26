import csv
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, time, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


DEFAULT_USER_AGENT = os.getenv(
    "TBS_POLICY_HAWK_USER_AGENT",
    "TBS-Policy-Hawk/1.0 (+https://github.com/TBS-Policy-Hawk)",
)
BASE_URL = "https://www.canada.ca"
PIN_SOURCES_MD_PATH = Path("PIN_sources.md")
PIN_ROOT = Path("data/PINs")
PIN_MANIFEST_PATH = PIN_ROOT / "pin_sources_manifest.json"
PIN_EVENTS_PATH = Path("data/pin_events.csv")
NEW_ITEMS_PATH = Path("data/new_items.csv")
ISSUE_MAP_PATH = Path("data/issue_map.json")
CHANGES_ROOT_NAME = "changes"
LOCAL_TIMEZONE = ZoneInfo("America/Toronto")
ITEM_HEADERS = ["guid", "title", "link", "pubDate", "category", "filename", "updated_date"]
NEW_ITEM_HEADERS = ITEM_HEADERS + ["change_type", "change_summary", "related_guid", "source_id"]


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    title: str
    short_name: str
    url: str
    folder: str
    parser_name: str


SOURCE_DEFINITIONS = [
    SourceDefinition(
        key="service_digital_announcements",
        title="Policy on Service and Digital Announcements",
        short_name="PSDA",
        url="https://www.canada.ca/en/government/system/digital-government/policies-standards/policy-service-digital-announcements.html",
        folder="PSDA",
        parser_name="parse_service_digital_announcements",
    ),
    SourceDefinition(
        key="contracting_policy_notices",
        title="Contracting policy notices",
        short_name="CPN",
        url="https://www.canada.ca/en/treasury-board-secretariat/services/policy-notice.html",
        folder="CPN",
        parser_name="parse_contracting_policy_notices",
    ),
    SourceDefinition(
        key="access_information_privacy_notices",
        title="Access to Information and Privacy Notices",
        short_name="ATIPN",
        url="https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy/access-information-privacy-notices.html",
        folder="ATIPN",
        parser_name="parse_atip_notices",
    ),
    SourceDefinition(
        key="human_resources_information_notices",
        title="Human Resources Information Notices",
        short_name="HRIN",
        url="https://www.canada.ca/en/treasury-board-secretariat/services/information-notice.html",
        folder="HRIN",
        parser_name="parse_hr_information_notices",
    ),
    SourceDefinition(
        key="security_policy_implementation_notice",
        title="Security Policy Implementation Notice",
        short_name="SPIN",
        url="https://www.canada.ca/en/government/system/digital-government/policies-standards/spin.html",
        folder="SPIN",
        parser_name="parse_spin",
    ),
    SourceDefinition(
        key="real_property_policy_notices",
        title="Real Property Policy Notices",
        short_name="RPPN",
        url="https://www.canada.ca/en/treasury-board-secretariat/services/federal-real-property-management/real-property-policy-notices.html",
        folder="RPPN",
        parser_name="parse_real_property_policy_notices",
    ),
]


def clean_text(value: str) -> str:
    text = value or ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def markdown_escape(value: str) -> str:
    return (value or "").replace("|", "\\|")


def normalize_markdown_body(value: str) -> str:
    text = (value or "").replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_filename(value: str) -> str:
    text = (value or "").replace(":", "_").replace("/", "_")
    text = re.sub(r"[^A-Za-z0-9 _.-]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("._")
    return text or "notice"


def extract_modified_date(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[name="dcterms.modified"]')
    if meta and meta.get("content"):
        return clean_text(meta["content"])

    pagedetails = soup.select_one(".pagedetails")
    if pagedetails:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", pagedetails.get_text(" ", strip=True))
        if match:
            return match.group(1)

    time_tag = soup.select_one('time[property="dateModified"]')
    if time_tag:
        if time_tag.get("datetime"):
            return clean_text(time_tag["datetime"])
        return clean_text(time_tag.get_text(" ", strip=True))

    return ""


def fetch_text(url: str, session: requests.Session) -> str:
    response = session.get(url, timeout=(10, 60))
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def absolute_url(href: str, base_url: str) -> str:
    return urljoin(base_url, href)


def split_notice_code_and_title(text: str) -> tuple[str, str]:
    cleaned = clean_text(text).replace("–", "-")
    match = re.match(r"^([0-9]{4}-[0-9]{2})\s*:\s*(.+)$", cleaned)
    if match:
        return match.group(1), clean_text(match.group(2))
    return "", cleaned


def parse_notice_code_from_li(text: str) -> str:
    matches = re.findall(r"\(([^()]+)\)", clean_text(text))
    return clean_text(matches[-1]) if matches else ""


def normalize_md_header(text: str) -> str:
    return clean_text(text).strip("# ").strip()


def inline_text(node, base_url: str) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    if node.name == "br":
        return "\n"
    if node.name == "a":
        text = clean_text("".join(inline_text(child, base_url) for child in node.children))
        href = node.get("href", "").strip()
        href = absolute_url(href, base_url) if href else ""
        if href and text:
            return f"[{text}]({href})"
        return text or href
    return "".join(inline_text(child, base_url) for child in node.children)


def node_text(node, base_url: str) -> str:
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return clean_text(str(node))
    return clean_text("".join(inline_text(child, base_url) for child in node.children))


def emit_list(node: Tag, out: list[str], base_url: str, indent: int = 0) -> None:
    items = [child for child in node.children if isinstance(child, Tag) and child.name == "li"]
    for index, item in enumerate(items, 1):
        marker = f"{index}. " if node.name == "ol" else "- "
        parts = []
        nested = []
        for child in item.children:
            if isinstance(child, Tag) and child.name in {"ul", "ol"}:
                nested.append(child)
            else:
                parts.append(inline_text(child, base_url))
        line = clean_text("".join(parts))
        if line:
            out.append("  " * indent + marker + line)
        for nested_list in nested:
            emit_list(nested_list, out, base_url, indent + 1)
    out.append("")


def emit_table(node: Tag, out: list[str], base_url: str) -> None:
    rows = []
    for tr in node.find_all("tr"):
        cells = [node_text(cell, base_url) for cell in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    out.append("| " + " | ".join(rows[0]) + " |")
    out.append("| " + " | ".join(["---"] * width) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(row) + " |")
    out.append("")


def walk_markdown(node: Tag, out: list[str], base_url: str) -> None:
    if isinstance(node, NavigableString):
        return
    if not isinstance(node, Tag):
        return
    if node.name in {"script", "style", "noscript"}:
        return
    if node.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        text = node_text(node, base_url)
        if text:
            out.append("#" * int(node.name[1]) + " " + text)
            out.append("")
        return
    if node.name == "summary":
        text = node_text(node, base_url)
        if text:
            out.append("**" + text + "**")
            out.append("")
        return
    if node.name == "p":
        text = node_text(node, base_url)
        if text:
            out.append(text)
            out.append("")
        return
    if node.name in {"ul", "ol"}:
        emit_list(node, out, base_url)
        return
    if node.name == "table":
        emit_table(node, out, base_url)
        return
    if node.name == "dl":
        term = None
        for child in node.children:
            if isinstance(child, Tag) and child.name == "dt":
                term = node_text(child, base_url)
            elif isinstance(child, Tag) and child.name == "dd":
                definition = node_text(child, base_url)
                if term or definition:
                    out.append(f"**{term}**: {definition}".strip())
                    out.append("")
        return
    if node.name == "section":
        heading = node.find(["h1", "h2", "h3", "h4", "h5", "h6"], recursive=False)
        if heading and node_text(heading, base_url).casefold() == "on this page":
            return
    for child in node.children:
        walk_markdown(child, out, base_url)


def html_to_markdown(html: str, page_url: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup.body or soup
    for selector in [
        "script",
        "style",
        "noscript",
        "nav.breadcrumbs",
        "#wb-bc",
        ".pagedetails",
        ".gc-subway",
        ".page-details",
        ".btn-group",
    ]:
        for node in main.select(selector):
            node.decompose()

    title_node = main.find(id="wb-cont") or main.find("h1") or soup.find("title")
    title = normalize_md_header(node_text(title_node, page_url))

    out: list[str] = []
    walk_markdown(main, out, page_url)
    body = normalize_markdown_body("\n".join(out)) + "\n"
    return title, body


def parse_service_digital_announcements(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for row in soup.select("main table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link = cells[0].find("a", href=True)
        if not link:
            continue
        notices.append(
            {
                "title": clean_text(link.get_text(" ", strip=True)),
                "url": absolute_url(link["href"], source_url),
                "listing_date": clean_text(cells[1].get_text(" ", strip=True)),
                "notice_code": "",
                "group": "",
                "table_schema": "date_title_url",
            }
        )
    return notices


def parse_contracting_policy_notices(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for heading in soup.select("main h2.h4"):
        year = clean_text(heading.get_text(" ", strip=True))
        notice_list = heading.find_next_sibling("ul")
        if not notice_list:
            continue
        for item in notice_list.find_all("li", recursive=False):
            link = item.find("a", href=True)
            if not link:
                continue
            full_text = clean_text(item.get_text(" ", strip=True))
            notices.append(
                {
                    "title": clean_text(link.get_text(" ", strip=True)),
                    "url": absolute_url(link["href"], source_url),
                    "listing_date": "",
                    "notice_code": parse_notice_code_from_li(full_text) or year,
                    "group": "",
                    "table_schema": "date_notice_title_url",
                }
            )
    return notices


def parse_atip_notices(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for details in soup.select("main details"):
        summary = details.find("summary")
        group = clean_text(summary.get_text(" ", strip=True)) if summary else ""
        for item in details.select("ul li"):
            link = item.find("a", href=True)
            if not link:
                continue
            notice_code, title = split_notice_code_and_title(link.get_text(" ", strip=True))
            notices.append(
                {
                    "title": title,
                    "url": absolute_url(link["href"], source_url),
                    "listing_date": "",
                    "notice_code": notice_code,
                    "group": group,
                    "table_schema": "date_group_notice_title_url",
                }
            )
    return notices


def parse_hr_information_notices(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for details in soup.select("main details"):
        summary = details.find("summary")
        summary_text = clean_text(summary.get_text(" ", strip=True)) if summary else ""
        if summary_text == "Active notices":
            for row in details.select("table tbody tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                link = cells[0].find("a", href=True)
                if not link:
                    continue
                url = absolute_url(link["href"], source_url)
                if "/en/treasury-board-secretariat/services/information-notice/" not in url:
                    continue
                notices.append(
                    {
                        "title": clean_text(link.get_text(" ", strip=True)),
                        "url": url,
                        "listing_date": clean_text(cells[1].get_text(" ", strip=True)),
                        "notice_code": "",
                        "group": "Active notices",
                        "table_schema": "date_group_title_url",
                    }
                )
        elif summary_text == "Archived notices":
            for item in details.select("ul.mrgn-tp-md li"):
                link = item.find("a", href=True)
                if not link:
                    continue
                url = absolute_url(link["href"], source_url)
                if "/en/treasury-board-secretariat/services/information-notice/" not in url:
                    continue
                full_text = clean_text(item.get_text(" ", strip=True))
                match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", full_text)
                title = clean_text(re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)$", "", link.get_text(" ", strip=True)))
                notices.append(
                    {
                        "title": title,
                        "url": url,
                        "listing_date": match.group(1) if match else "",
                        "notice_code": "",
                        "group": "Archived notices",
                        "table_schema": "date_group_title_url",
                    }
                )
    return notices


def parse_spin(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for item in soup.select("main ul.list-unstyled.mrgn-lft-lg li"):
        link = item.find("a", href=True)
        if not link:
            continue
        time_tag = item.find("time")
        text = clean_text(item.get_text(" ", strip=True))
        code_match = re.match(r"^([0-9]{4}-[0-9]{2})", text)
        notices.append(
            {
                "title": clean_text(link.get_text(" ", strip=True)),
                "url": absolute_url(link["href"], source_url),
                "listing_date": clean_text(time_tag.get("datetime", "") if time_tag else ""),
                "notice_code": code_match.group(1) if code_match else "",
                "group": "",
                "table_schema": "date_notice_title_url",
            }
        )
    return notices


def parse_real_property_policy_notices(soup: BeautifulSoup, source_url: str) -> list[dict]:
    notices = []
    for item in soup.select("main ul li"):
        link = item.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if "/real-property-policy-notices/" not in href:
            continue
        full_text = clean_text(item.get_text(" ", strip=True))
        notices.append(
            {
                "title": clean_text(link.get_text(" ", strip=True)),
                "url": absolute_url(href, source_url),
                "listing_date": "",
                "notice_code": parse_notice_code_from_li(full_text),
                "group": "",
                "table_schema": "date_notice_title_url",
            }
        )
    return notices


SOURCE_PARSERS: dict[str, Callable[[BeautifulSoup, str], list[dict]]] = {
    "parse_service_digital_announcements": parse_service_digital_announcements,
    "parse_contracting_policy_notices": parse_contracting_policy_notices,
    "parse_atip_notices": parse_atip_notices,
    "parse_hr_information_notices": parse_hr_information_notices,
    "parse_spin": parse_spin,
    "parse_real_property_policy_notices": parse_real_property_policy_notices,
}


def parse_source(defn: SourceDefinition, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    modified = extract_modified_date(soup)
    parser = SOURCE_PARSERS[defn.parser_name]
    notices = parser(soup, defn.url)
    return {"source_modified": modified, "notices": notices}


def build_unique_filenames(notices: list[dict], previous_by_url: dict[str, dict] | None = None) -> None:
    """Assign filenames while retaining the URL's established repository identity."""
    previous_by_url = previous_by_url or {}
    used = set()
    for notice in notices:
        previous = previous_by_url.get(notice["url"], {})
        previous_filename = Path(previous.get("filename", "")).name
        if previous_filename and previous_filename not in used:
            notice["filename"] = previous_filename
            used.add(previous_filename)
            continue
        base = sanitize_filename(notice["title"])
        candidate = base
        if candidate + ".md" in used:
            suffix = sanitize_filename(notice.get("notice_code") or notice.get("listing_date") or notice.get("group") or "notice")
            candidate = sanitize_filename(f"{base}_{suffix}")
        counter = 2
        while candidate + ".md" in used:
            candidate = sanitize_filename(f"{base}_{counter}")
            counter += 1
        filename = candidate + ".md"
        used.add(filename)
        notice["filename"] = filename


def format_section_table(defn: SourceDefinition, notices: list[dict]) -> list[str]:
    if not notices:
        return ["No notices found.", ""]

    schema = notices[0]["table_schema"]
    if schema == "date_title_url":
        lines = ["| Date | Title | URL |", "|---|---|---|"]
        for notice in notices:
            lines.append(
                "|{date}|{title}|{url}|".format(
                    date=markdown_escape(notice["table_date"]),
                    title=markdown_escape(notice["title"]),
                    url=markdown_escape(notice["url"]),
                )
            )
        return lines + [""]

    if schema == "date_notice_title_url":
        lines = ["| Date | Notice | Title | URL |", "|---|---|---|---|"]
        for notice in notices:
            lines.append(
                "|{date}|{code}|{title}|{url}|".format(
                    date=markdown_escape(notice["table_date"]),
                    code=markdown_escape(notice.get("notice_code", "")),
                    title=markdown_escape(notice["title"]),
                    url=markdown_escape(notice["url"]),
                )
            )
        return lines + [""]

    if schema == "date_group_notice_title_url":
        lines = ["| Date | Group | Notice | Title | URL |", "|---|---|---|---|---|"]
        for notice in notices:
            lines.append(
                "|{date}|{group}|{code}|{title}|{url}|".format(
                    date=markdown_escape(notice["table_date"]),
                    group=markdown_escape(notice.get("group", "")),
                    code=markdown_escape(notice.get("notice_code", "")),
                    title=markdown_escape(notice["title"]),
                    url=markdown_escape(notice["url"]),
                )
            )
        return lines + [""]

    if schema == "date_group_title_url":
        lines = ["| Date | Group | Title | URL |", "|---|---|---|---|"]
        for notice in notices:
            lines.append(
                "|{date}|{group}|{title}|{url}|".format(
                    date=markdown_escape(notice["table_date"]),
                    group=markdown_escape(notice.get("group", "")),
                    title=markdown_escape(notice["title"]),
                    url=markdown_escape(notice["url"]),
                )
            )
        return lines + [""]

    raise ValueError(f"Unknown table schema: {schema}")


def render_pin_sources_md(source_records: list[dict]) -> str:
    lines = [
        "# Policy Notice Sources",
        "",
        "Generated from the live source pages listed below.",
        "",
    ]
    for record in source_records:
        defn = record["definition"]
        lines.append(f"## [{defn.title} ({defn.short_name})]({defn.url})")
        lines.append("")
        lines.append(f"> Date modified: {record['source_modified']}")
        lines.append("")
        lines.append(f"> Notices: {len(record['notices'])}")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Notice table</summary>")
        lines.append("")
        lines.extend(format_section_table(defn, record["notices"]))
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_notice_markdown(defn: SourceDefinition, source_modified: str, notice: dict, detail_html: str | None, fetch_error: str, captured_at: str) -> str:
    if detail_html:
        detail_soup = BeautifulSoup(detail_html, "lxml")
        notice_modified = extract_modified_date(detail_soup)
        title, body = html_to_markdown(detail_html, notice["url"])
    else:
        notice_modified = ""
        title = notice["title"]
        body = "## Fetch error\nUnable to retrieve the linked notice page during sync.\n"

    lines = [
        f"# {notice['title']}",
        "",
        f"- Notice source: {defn.title} ({defn.short_name})",
        f"- Source page URL: {defn.url}",
        f"- Source page modified: {source_modified}",
        f"- Notice URL: {notice['url']}",
        f"- Notice modified: {notice_modified}",
    ]
    if notice.get("notice_code"):
        lines.append(f"- Notice identifier: {notice['notice_code']}")
    if notice.get("group"):
        lines.append(f"- Notice group: {notice['group']}")
    lines.extend(
        [
            f"- Listed date: {notice.get('listing_date', '')}",
            f"- Captured at (UTC): {captured_at}",
        ]
    )
    if fetch_error:
        lines.append(f"- Fetch error: {fetch_error}")
    if title and title != notice["title"]:
        lines.append(f"- Page title: {title}")
    lines.extend(["", "---", "", body.rstrip(), ""])
    notice["detail_modified"] = notice_modified
    notice["fetch_error"] = fetch_error
    return "\n".join(lines)


def canonical_notice_text(value: str) -> str:
    """Remove capture metadata that changes even when notice content does not."""
    lines = []
    for line in (value or "").splitlines():
        if line.startswith("- Source page modified:"):
            continue
        if line.startswith("- Captured at (UTC):"):
            continue
        lines.append(line.rstrip())
    return normalize_markdown_body("\n".join(lines))


def canonical_sources_text(value: str) -> str:
    lines = [line for line in (value or "").splitlines() if not line.startswith("> Date modified:")]
    return normalize_markdown_body("\n".join(lines))


def semantic_manifest(value: dict) -> dict:
    """Return the durable state, excluding run and upstream page timestamps."""
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in {"generated_at_utc", "source_modified"}:
            continue
        if isinstance(item, dict):
            result[key] = semantic_manifest(item)
        elif isinstance(item, list):
            result[key] = [semantic_manifest(entry) if isinstance(entry, dict) else entry for entry in item]
        else:
            result[key] = item
    return result


def _existing_capture_paths() -> list[Path]:
    if not PIN_ROOT.exists():
        return []
    return [path for path in PIN_ROOT.glob("*/*.md") if path.parent.name != CHANGES_ROOT_NAME]


def load_tracking_manifest() -> tuple[dict, bool]:
    """Load trusted tracking state; never silently re-baseline an existing corpus."""
    captures = _existing_capture_paths()
    if not PIN_MANIFEST_PATH.exists():
        if captures:
            raise RuntimeError("PIN manifest is missing while tracked PIN captures exist; refusing to re-baseline")
        return {"sources": [], "pending_removals": {}}, True
    try:
        manifest = json.loads(PIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if captures:
            raise RuntimeError("PIN manifest is unreadable while tracked PIN captures exist; refusing to re-baseline") from exc
        return {"sources": [], "pending_removals": {}}, True
    valid_sources = (
        isinstance(manifest, dict)
        and isinstance(manifest.get("sources"), list)
        and all(
            isinstance(source, dict)
            and isinstance(source.get("notices", []), list)
            and all(isinstance(notice, dict) for notice in source.get("notices", []))
            for source in manifest.get("sources", [])
        )
    )
    if not valid_sources:
        if captures:
            raise RuntimeError("PIN manifest is invalid while tracked PIN captures exist; refusing to re-baseline")
        return {"sources": [], "pending_removals": {}}, True
    return manifest, not manifest["sources"] and not captures


def build_manifest(source_records: list[dict], pending_removals: dict[str, dict[str, int]], generated_at: str) -> dict:
    return {
        "schema_version": 2,
        "generated_at_utc": generated_at,
        "pending_removals": pending_removals,
        "sources": [
            {
                "key": record["definition"].key,
                "title": record["definition"].title,
                "short_name": record["definition"].short_name,
                "url": record["definition"].url,
                "folder": record["definition"].folder,
                "source_modified": record["source_modified"],
                "notice_count": len(record["notices"]),
                "notices": [
                    {
                        "title": notice["title"],
                        "url": notice["url"],
                        "listing_date": notice.get("listing_date", ""),
                        "table_date": notice.get("table_date", ""),
                        "notice_code": notice.get("notice_code", ""),
                        "group": notice.get("group", ""),
                        "detail_modified": notice.get("detail_modified", ""),
                        "fetch_error": notice.get("fetch_error", ""),
                        "filename": notice["filename"],
                        "path": notice.get("path", ""),
                    }
                    for notice in record["notices"]
                ],
            }
            for record in source_records
        ],
    }


def _source_map(manifest: dict) -> dict[str, dict]:
    return {source.get("key", ""): source for source in manifest.get("sources", []) if source.get("key")}


def _path_text(path_value: str) -> str | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _event_guid(defn: SourceDefinition, url: str, change: str, previous: str, current: str, detected_date: str) -> str:
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    transition = canonical_notice_text(previous) + "\0" + canonical_notice_text(current)
    transition_hash = hashlib.sha256(transition.encode("utf-8")).hexdigest()[:12]
    return f"pin_{defn.folder.lower()}_{url_hash}_{change}_{transition_hash}_{detected_date}"


def _tombstone(defn: SourceDefinition, notice: dict, detected_date: str) -> str:
    return (
        f"# {notice.get('title', 'Removed PIN')}\n\n"
        f"- Notice source: {defn.title} ({defn.short_name})\n"
        f"- Notice URL: {notice.get('url', '')}\n"
        f"- Removal detected: {detected_date}\n\n"
        "---\n\nThis notice is no longer listed by its tracked source after two consecutive successful checks.\n"
    )


def _write_change_evidence(
    defn: SourceDefinition,
    notice: dict,
    change: str,
    previous: str,
    current: str,
    detected_date: str,
    stable_path: Path,
) -> dict:
    guid = _event_guid(defn, notice["url"], change, previous, current, detected_date)
    change_dir = PIN_ROOT / CHANGES_ROOT_NAME / guid
    previous_path = change_dir / "previous.md"
    current_path = change_dir / "current.md"
    metadata_path = change_dir / "change.json"
    if metadata_path.exists():
        try:
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Existing PIN change evidence is corrupt: {metadata_path}") from exc
        if existing.get("guid") != guid or not previous_path.exists() or not current_path.exists():
            raise RuntimeError(f"Existing PIN change evidence is incomplete: {change_dir}")
        existing.setdefault("metadata_path", _display_path(metadata_path))
        return existing
    if change_dir.exists() and any(change_dir.iterdir()):
        raise RuntimeError(f"Refusing to overwrite incomplete PIN change evidence: {change_dir}")
    metadata = {
        "guid": guid,
        "change_type": "pin",
        "pin_change": change,
        "detected_date": detected_date,
        "family": defn.short_name,
        "source_key": defn.key,
        "source_title": defn.title,
        "notice_identifier": notice.get("notice_code", ""),
        "title": notice.get("title", ""),
        "url": notice.get("url", ""),
        "stable_path": _display_path(stable_path),
        "previous_path": _display_path(previous_path),
        "current_path": _display_path(current_path),
        "metadata_path": _display_path(metadata_path),
    }
    change_dir.mkdir(parents=True, exist_ok=True)
    previous_path.write_text(previous or "# No previous capture\n", encoding="utf-8")
    current_path.write_text(current, encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def _event_row(event: dict, now_local: datetime) -> dict:
    midnight = datetime.combine(now_local.date(), time.min, tzinfo=LOCAL_TIMEZONE)
    change = event["pin_change"]
    family = event["family"]
    identifier = event.get("notice_identifier") or event["title"]
    return {
        "guid": event["guid"],
        "title": event["title"],
        "link": event["url"],
        "pubDate": format_datetime(midnight),
        "category": "PIN",
        "filename": event["metadata_path"],
        "updated_date": now_local.replace(microsecond=0).isoformat(),
        "change_type": "pin",
        "change_summary": f"PIN {change}: {family} {identifier}",
        "related_guid": "",
        "source_id": family,
    }


def _append_csv_rows(path: Path, headers: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_guids = set()
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != headers:
                raise RuntimeError(f"Unexpected CSV columns in {path}: {reader.fieldnames}")
            existing_guids = {row.get("guid", "") for row in reader}
    new_rows = []
    for row in rows:
        if row["guid"] in existing_guids:
            continue
        new_rows.append(row)
        existing_guids.add(row["guid"])
    if not new_rows:
        return
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        if needs_header:
            writer.writeheader()
        writer.writerows(new_rows)


def _validate_csv_header(path: Path, headers: list[str]) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames
    if fieldnames != headers:
        raise RuntimeError(f"Unexpected CSV columns in {path}: {fieldnames}")


def _load_issue_map() -> dict:
    if not ISSUE_MAP_PATH.exists():
        return {}
    try:
        issue_map = json.loads(ISSUE_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"PIN issue map is unreadable: {ISSUE_MAP_PATH}") from exc
    if not isinstance(issue_map, dict):
        raise RuntimeError(f"PIN issue map must contain a JSON object: {ISSUE_MAP_PATH}")
    return issue_map


def _requeue_unmapped_pin_events(issue_map: dict) -> list[dict]:
    """Restore durable, unissued PIN events after fetch_feed clears new_items.csv."""
    if not PIN_EVENTS_PATH.exists() or PIN_EVENTS_PATH.stat().st_size == 0:
        return []
    with PIN_EVENTS_PATH.open(newline="", encoding="utf-8") as handle:
        ledger_rows = list(csv.DictReader(handle))
    rows = []
    for ledger_row in ledger_rows:
        guid = ledger_row.get("guid", "")
        if not guid or guid in issue_map:
            continue
        metadata = {}
        metadata_path = Path(ledger_row.get("filename", ""))
        if metadata_path.exists():
            try:
                loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"PIN event metadata is corrupt: {metadata_path}") from exc
            if not isinstance(loaded, dict):
                raise RuntimeError(f"PIN event metadata must contain a JSON object: {metadata_path}")
            metadata = loaded
        family = metadata.get("family", "")
        change = metadata.get("pin_change", "activity")
        identifier = metadata.get("notice_identifier") or ledger_row.get("title", "")
        rows.append(
            {
                **{header: ledger_row.get(header, "") for header in ITEM_HEADERS},
                "change_type": "pin",
                "change_summary": f"PIN {change}: {family} {identifier}".replace(":  ", ": ").strip(),
                "related_guid": "",
                "source_id": family,
            }
        )
    _append_csv_rows(NEW_ITEMS_PATH, NEW_ITEM_HEADERS, rows)
    return rows


def _write_sources_if_changed(rendered: str) -> bool:
    if PIN_SOURCES_MD_PATH.exists():
        old = PIN_SOURCES_MD_PATH.read_text(encoding="utf-8")
        if canonical_sources_text(old) == canonical_sources_text(rendered):
            return False
    PIN_SOURCES_MD_PATH.write_text(rendered, encoding="utf-8")
    return True


def _write_manifest_if_changed(manifest: dict, previous: dict) -> bool:
    if semantic_manifest(previous) == semantic_manifest(manifest):
        return False
    PIN_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIN_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def _fetch_details(source_records: list[dict], session: requests.Session) -> dict[str, dict]:
    detail_urls = {notice["url"]: {"html": None, "error": ""} for record in source_records for notice in record["notices"]}

    def fetch_detail(url: str) -> tuple[str, dict]:
        try:
            return url, {"html": fetch_text(url, session), "error": ""}
        except requests.RequestException as exc:
            return url, {"html": None, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_detail, url) for url in detail_urls]
        for future in as_completed(futures):
            url, result = future.result()
            detail_urls[url] = result
    return detail_urls


def _table_schema_for(defn: SourceDefinition, current_notices: list[dict]) -> str:
    if current_notices and current_notices[0].get("table_schema"):
        return current_notices[0]["table_schema"]
    return {
        "PSDA": "date_title_url",
        "ATIPN": "date_group_notice_title_url",
        "HRIN": "date_group_title_url",
    }.get(defn.folder, "date_notice_title_url")


def sync_source_records(
    source_records: list[dict],
    session: requests.Session,
    now: datetime | None = None,
) -> list[dict]:
    """Persist a successful listing snapshot and emit only semantic PIN events."""
    previous_manifest, baseline = load_tracking_manifest()
    # Validate downstream ledgers before creating any evidence or changing captures.
    _validate_csv_header(NEW_ITEMS_PATH, NEW_ITEM_HEADERS)
    _validate_csv_header(PIN_EVENTS_PATH, ITEM_HEADERS)
    issue_map = _load_issue_map()
    previous_sources = _source_map(previous_manifest)
    pending_before = previous_manifest.get("pending_removals", {})
    if not isinstance(pending_before, dict):
        raise RuntimeError("PIN manifest pending_removals must be an object")

    # A large inventory drop usually means an upstream/parser failure, not removals.
    for record in source_records:
        defn = record["definition"]
        prior_count = len(previous_sources.get(defn.key, {}).get("notices", []))
        current_count = len(record["notices"])
        if prior_count >= 5 and current_count * 4 <= prior_count * 3:
            raise RuntimeError(
                f"Suspicious PIN inventory drop for {defn.short_name}: {prior_count} to {current_count}; refusing to modify tracking state"
            )

    detail_results = _fetch_details(source_records, session)
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    now_local = now_utc.astimezone(LOCAL_TIMEZONE)
    captured_at = now_utc.isoformat().replace("+00:00", "Z")
    detected_date = now_local.date().isoformat()
    pending_after: dict[str, dict[str, int]] = {}
    persisted_records = []
    events = []
    stable_writes: list[tuple[Path, str]] = []
    stable_removals: list[Path] = []

    for record in source_records:
        defn = record["definition"]
        previous_source = previous_sources.get(defn.key, {})
        previous_notices = previous_source.get("notices", [])
        previous_by_url = {notice.get("url", ""): notice for notice in previous_notices if notice.get("url")}
        current_notices = [dict(notice) for notice in record["notices"]]
        table_schema = _table_schema_for(defn, current_notices)
        build_unique_filenames(current_notices, previous_by_url)
        current_urls = {notice["url"] for notice in current_notices}
        source_dir = PIN_ROOT / defn.folder
        processed: dict[str, dict] = {}

        for notice in current_notices:
            previous_notice = previous_by_url.get(notice["url"])
            previous_text = _path_text(previous_notice.get("path", "")) if previous_notice else None
            detail = detail_results[notice["url"]]
            if detail["html"] is None:
                if previous_notice and previous_text is not None:
                    # A transient detail failure must not replace the last good capture.
                    preserved = dict(previous_notice)
                    preserved["table_schema"] = table_schema
                    processed[notice["url"]] = preserved
                else:
                    print(f"Deferred uncaptured PIN after fetch failure: {notice['url']} ({detail['error']})")
                continue

            markdown = build_notice_markdown(
                defn,
                record["source_modified"],
                notice,
                detail["html"],
                "",
                captured_at,
            )
            stable_path = source_dir / notice["filename"]
            notice["path"] = _display_path(stable_path)
            if previous_text is None:
                stable_writes.append((stable_path, markdown))
                if not baseline:
                    events.append(_write_change_evidence(defn, notice, "added", "", markdown, detected_date, stable_path))
            elif canonical_notice_text(previous_text) != canonical_notice_text(markdown):
                stable_writes.append((stable_path, markdown))
                events.append(_write_change_evidence(defn, notice, "changed", previous_text, markdown, detected_date, stable_path))
            else:
                # Retain both bytes and durable metadata when only volatile timestamps changed.
                notice["detail_modified"] = previous_notice.get("detail_modified", notice.get("detail_modified", ""))
                notice["fetch_error"] = ""
            processed[notice["url"]] = notice

        source_pending: dict[str, int] = {}
        prior_pending = pending_before.get(defn.key, {})
        if not isinstance(prior_pending, dict):
            raise RuntimeError(f"PIN manifest pending removals for {defn.key} must be an object")
        for url, previous_notice in previous_by_url.items():
            if url in current_urls:
                continue
            miss_count = int(prior_pending.get(url, 0)) + 1
            previous_text = _path_text(previous_notice.get("path", ""))
            if miss_count < 2:
                source_pending[url] = miss_count
                if previous_text is not None:
                    preserved = dict(previous_notice)
                    preserved["table_schema"] = table_schema
                    processed[url] = preserved
                continue
            stable_path = Path(previous_notice.get("path", ""))
            if previous_text is None:
                raise RuntimeError(f"Cannot confirm PIN removal without its previous capture: {url}")
            current = _tombstone(defn, previous_notice, detected_date)
            events.append(_write_change_evidence(defn, previous_notice, "removed", previous_text, current, detected_date, stable_path))
            stable_removals.append(stable_path)
        if source_pending:
            pending_after[defn.key] = source_pending

        ordered_urls = [notice.get("url", "") for notice in previous_notices if notice.get("url") in processed]
        ordered_urls.extend(notice["url"] for notice in current_notices if notice["url"] in processed and notice["url"] not in ordered_urls)
        persisted_records.append(
            {
                "definition": defn,
                "source_modified": record["source_modified"],
                "notices": [processed[url] for url in ordered_urls],
            }
        )

    PIN_ROOT.mkdir(parents=True, exist_ok=True)
    for path, markdown in stable_writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    for path in stable_removals:
        path.unlink(missing_ok=True)

    prepare_table_dates(persisted_records)
    fill_missing_table_dates_from_detail(persisted_records)
    _write_sources_if_changed(render_pin_sources_md(persisted_records))
    manifest = build_manifest(persisted_records, pending_after, captured_at)
    _write_manifest_if_changed(manifest, previous_manifest)
    rows = [_event_row(event, now_local) for event in events]
    _append_csv_rows(NEW_ITEMS_PATH, NEW_ITEM_HEADERS, rows)
    _append_csv_rows(PIN_EVENTS_PATH, ITEM_HEADERS, rows)
    _requeue_unmapped_pin_events(issue_map)
    return events


def prepare_table_dates(source_records: list[dict]) -> None:
    for record in source_records:
        for notice in record["notices"]:
            notice["table_date"] = notice.get("listing_date", "")


def fill_missing_table_dates_from_detail(source_records: list[dict]) -> None:
    for record in source_records:
        for notice in record["notices"]:
            if not notice.get("table_date"):
                notice["table_date"] = notice.get("detail_modified", "")


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    source_records = []
    for defn in SOURCE_DEFINITIONS:
        html = fetch_text(defn.url, session)
        parsed = parse_source(defn, html)
        source_records.append(
            {
                "definition": defn,
                "source_modified": parsed["source_modified"],
                "notices": parsed["notices"],
            }
        )

    prepare_table_dates(source_records)
    events = sync_source_records(source_records, session)

    print(f"PIN events detected: {len(events)}")
    for record in source_records:
        print(f"{record['definition'].short_name}: {len(record['notices'])} notices")


if __name__ == "__main__":
    main()
