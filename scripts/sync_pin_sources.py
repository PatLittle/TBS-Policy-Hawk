import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin

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


def build_unique_filenames(notices: list[dict]) -> None:
    used = {}
    for notice in notices:
        base = sanitize_filename(notice["title"])
        candidate = base
        if candidate in used:
            suffix = sanitize_filename(notice.get("notice_code") or notice.get("listing_date") or notice.get("group") or "notice")
            candidate = sanitize_filename(f"{base}_{suffix}")
        counter = 2
        while candidate in used:
            candidate = sanitize_filename(f"{base}_{counter}")
            counter += 1
        used[candidate] = True
        notice["filename"] = candidate + ".md"


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


def write_notice_files(source_records: list[dict], session: requests.Session) -> None:
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    detail_urls = {}
    for record in source_records:
        for notice in record["notices"]:
            detail_urls[notice["url"]] = {"html": None, "error": ""}

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

    PIN_ROOT.mkdir(parents=True, exist_ok=True)
    for record in source_records:
        defn = record["definition"]
        source_dir = PIN_ROOT / defn.folder
        source_dir.mkdir(parents=True, exist_ok=True)
        expected_files = set()
        build_unique_filenames(record["notices"])

        for notice in record["notices"]:
            markdown = build_notice_markdown(
                defn=defn,
                source_modified=record["source_modified"],
                notice=notice,
                detail_html=detail_urls[notice["url"]]["html"],
                fetch_error=detail_urls[notice["url"]]["error"],
                captured_at=captured_at,
            )
            file_path = source_dir / notice["filename"]
            file_path.write_text(markdown, encoding="utf-8")
            notice["path"] = str(file_path.as_posix())
            expected_files.add(file_path.name)

        for existing in source_dir.glob("*.md"):
            if existing.name not in expected_files:
                existing.unlink()


def build_manifest(source_records: list[dict]) -> dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
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
    write_notice_files(source_records, session)
    fill_missing_table_dates_from_detail(source_records)

    PIN_SOURCES_MD_PATH.write_text(render_pin_sources_md(source_records), encoding="utf-8")
    PIN_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIN_MANIFEST_PATH.write_text(json.dumps(build_manifest(source_records), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Updated {PIN_SOURCES_MD_PATH}")
    print(f"Updated {PIN_MANIFEST_PATH}")
    for record in source_records:
        print(f"{record['definition'].short_name}: {len(record['notices'])} notices")


if __name__ == "__main__":
    main()
