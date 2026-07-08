import csv
import hashlib
import html as html_lib
import json
import os
import re
import time
from copy import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    from scripts.build_tbs_policy_hierarchy import build_full_records, extract_rows_with_hierarchy
except ModuleNotFoundError:
    from build_tbs_policy_hierarchy import build_full_records, extract_rows_with_hierarchy


BASE_URL = "https://www.tbs-sct.canada.ca/pol/"
DEFAULT_USER_AGENT = os.getenv("TBS_POLICY_HAWK_USER_AGENT", "TBS-Policy-Hawk/1.0 (+https://github.com/TBS-Policy-Hawk)")
HIERARCHY_URL = urljoin(BASE_URL, "hierarch-eng.aspx")
GLOSSARY_URLS = {
    "en": urljoin(BASE_URL, "glossary-lexique-eng.aspx"),
    "fr": urljoin(BASE_URL, "glossary-lexique-fra.aspx"),
}
HIERARCHY_HEADERS = ["ID", "URL", "Name", "Min Level", "Hierarchy Paths", "Other Names"]
GLOSSARY_HEADERS = [
    "source_id",
    "source_en",
    "source_fr",
    "term_en",
    "term_fr",
    "def_en",
    "def_fr",
    "date_modified",
]


def clean_text(value):
    text = html_lib.unescape(value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_key(value):
    return clean_text(value).casefold()


def extract_doc_id(url):
    match = re.search(r"[?&]id=(\d+)", url or "")
    return match.group(1) if match else ""


def page_date_modified(soup):
    time_tag = soup.select_one('time[property="dateModified"]')
    return clean_text(time_tag.get_text()) if time_tag else ""


def infer_category(title):
    title = title or ""
    lowered = title.casefold()
    if "directive" in lowered:
        return "Directive"
    if "policy framework" in lowered or "framework" in lowered:
        return "Framework"
    if "policy" in lowered:
        return "Policy"
    if "standard" in lowered:
        return "Standard"
    if "guideline" in lowered or "guidelines" in lowered:
        return "Guidelines"
    if "guide" in lowered:
        return "Guide"
    return "Uncategorized"


def resolve_policy_url(url, getter=requests.get, user_agent=None):
    headers = {"User-Agent": user_agent or DEFAULT_USER_AGENT}
    response = getter(url, timeout=(5, 15), headers=headers, allow_redirects=True, stream=True)
    try:
        response.raise_for_status()
        final_url = response.url or url
        return final_url.replace("http://", "https://")
    finally:
        close = getattr(response, "close", None)
        if close:
            close()


def get_with_retries(url, getter=requests.get, *, attempts=3, backoff_seconds=5, **kwargs):
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            response = getter(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            print(f"Warning: request failed for {url} on attempt {attempt}/{attempts}: {exc}. Retrying.")
            if backoff_seconds:
                time.sleep(backoff_seconds * attempt)
    raise last_exc


def fetch_hierarchy_records(
    getter=requests.get,
    user_agent=None,
    resolve_redirects=True,
    attempts=3,
    retry_backoff_seconds=5,
):
    headers = {"User-Agent": user_agent or DEFAULT_USER_AGENT}
    response = get_with_retries(
        HIERARCHY_URL,
        getter=getter,
        attempts=attempts,
        backoff_seconds=retry_backoff_seconds,
        timeout=60,
        headers=headers,
    )

    soup = BeautifulSoup(response.text, "html.parser")
    date_modified = page_date_modified(soup)
    records = build_full_records(extract_rows_with_hierarchy(response.text))

    def resolve_record(record):
        original_url = urljoin(BASE_URL, record["URL"])
        if not resolve_redirects:
            return record, original_url, original_url
        try:
            return record, original_url, resolve_policy_url(original_url, getter=getter, user_agent=user_agent)
        except requests.RequestException as exc:
            print(f"Warning: unable to resolve hierarchy link {original_url}: {exc}")
            return record, original_url, original_url

    resolved_records = []
    if resolve_redirects:
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(resolve_record, record) for record in records]
            for future in as_completed(futures):
                resolved_records.append(future.result())
    else:
        resolved_records = [resolve_record(record) for record in records]

    by_id = {}
    for record, original_url, resolved_url in resolved_records:
        resolved_id = extract_doc_id(resolved_url) or record["ID"]
        existing = by_id.get(resolved_id)
        hierarchy_paths = set(filter(None, (record.get("Hierarchy Paths") or "").split(" || ")))
        names = set(filter(None, [record.get("Name"), record.get("Other Names")]))

        if existing:
            existing_paths = set(filter(None, (existing["Hierarchy Paths"] or "").split(" || ")))
            existing_names = set(filter(None, (existing["Other Names"] or "").split(", ")))
            existing_paths.update(hierarchy_paths)
            existing_names.update(names - {existing["Name"]})
            existing["Hierarchy Paths"] = " || ".join(sorted(existing_paths))
            existing["Other Names"] = ", ".join(sorted(existing_names))
            existing["Min Level"] = str(min(int(existing["Min Level"]), int(record["Min Level"])))
            continue

        by_id[resolved_id] = {
            "ID": resolved_id,
            "URL": resolved_url,
            "Name": record["Name"],
            "Min Level": str(record["Min Level"]),
            "Hierarchy Paths": " || ".join(sorted(hierarchy_paths)),
            "Other Names": record.get("Other Names", ""),
            "date_modified": date_modified,
            "category": infer_category(record["Name"]),
            "original_id": record["ID"],
            "original_url": original_url,
        }

    return sorted(by_id.values(), key=lambda row: (int(row["Min Level"]), row["Name"]))


def read_hierarchy_csv(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_hierarchy_csv(path, records):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HIERARCHY_HEADERS)
        writer.writeheader()
        for row in records:
            writer.writerow({header: row.get(header, "") for header in HIERARCHY_HEADERS})


def hierarchy_tree_text(records):
    roots = {}
    name_counts = {}
    labels_by_name = {}

    def node_label(record):
        label = f"{record.get('Name', '')} [{record.get('ID', '')}]"
        url = record.get("URL", "")
        return f"{label} - {url}" if url else label

    for record in records:
        name = record.get("Name", "")
        name_counts[name] = name_counts.get(name, 0) + 1
        labels_by_name[name] = node_label(record)

    def path_label(name):
        return labels_by_name[name] if name_counts.get(name) == 1 else name

    def ensure_child(parent, name):
        return parent.setdefault(name, {})

    for record in records:
        paths = [p for p in (record.get("Hierarchy Paths") or "").split(" || ") if p]
        if not paths:
            paths = [""]
        for path in paths:
            current = roots
            if path:
                for part in path.split(" > "):
                    current = ensure_child(current, path_label(part))
            ensure_child(current, node_label(record))

    lines = []

    def render(children, prefix=""):
        items = sorted(children.items(), key=lambda item: clean_text(item[0]).casefold())
        for index, (label, grandchildren) in enumerate(items):
            is_last = index == len(items) - 1
            connector = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{connector}{label}")
            extension = "    " if is_last else "|   "
            render(grandchildren, prefix + extension)

    render(roots)
    return "\n".join(lines).rstrip() + "\n"


def write_hierarchy_tree(path, records):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(hierarchy_tree_text(records), encoding="utf-8")


def compare_hierarchy(previous, current):
    previous_by_id = {row["ID"]: row for row in previous if row.get("ID")}
    current_by_id = {row["ID"]: row for row in current if row.get("ID")}
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)
    return {
        "added": [current_by_id[i] for i in sorted(current_ids - previous_ids)],
        "removed": [previous_by_id[i] for i in sorted(previous_ids - current_ids)],
    }


def split_term(dt, lang):
    dt_copy = copy(dt)
    other_lang = "fr" if lang == "en" else "en"
    translated = ""
    for span in dt_copy.find_all(attrs={"lang": other_lang}):
        translated = clean_text(span.get_text(" ", strip=True)) or translated
        span.decompose()

    primary = clean_text(dt_copy.get_text(" ", strip=True))
    primary = re.sub(r"[\s\-\u2013\u2014]*\(\s*\)\s*$", "", primary).strip()
    primary = re.sub(r"[\s\-\u2013\u2014]+$", "", primary).strip()

    if lang == "en":
        return primary, translated
    return translated, primary


def definition_text(dd):
    dd_copy = copy(dd)
    for footer in dd_copy.select("footer"):
        footer.decompose()
    return clean_text(dd_copy.get_text(" ", strip=True))


def source_links(dd):
    footer = dd.select_one("footer")
    if not footer:
        return [{"source_id": "", "source": ""}]

    links = []
    for link in footer.select("a[href*='doc-']"):
        source_id = extract_doc_id(link.get("href", ""))
        if source_id:
            links.append({"source_id": source_id, "source": clean_text(link.get_text(" ", strip=True))})
    return links or [{"source_id": "", "source": clean_text(footer.get_text(" ", strip=True))}]


def parse_glossary_html(html, lang):
    soup = BeautifulSoup(html, "html.parser")
    date_modified = page_date_modified(soup)
    rows = []

    for dt in soup.select("main dt"):
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        term_en, term_fr = split_term(dt, lang)
        definition = definition_text(dd)
        for source in source_links(dd):
            row = {
                "source_id": source["source_id"],
                "source_en": source["source"] if lang == "en" else "",
                "source_fr": source["source"] if lang == "fr" else "",
                "term_en": term_en,
                "term_fr": term_fr,
                "def_en": definition if lang == "en" else "",
                "def_fr": definition if lang == "fr" else "",
                "date_modified": date_modified,
            }
            rows.append(row)
    return rows


def merge_glossary_rows(rows_en, rows_fr):
    merged = {}
    by_source_term_en = {}
    by_source_term_fr = {}

    def row_key(row):
        digest = hashlib.sha1(
            "||".join([
                row.get("source_id", ""),
                normalize_key(row.get("term_en", "")),
                normalize_key(row.get("term_fr", "")),
            ]).encode("utf-8")
        ).hexdigest()[:12]
        return digest

    for row in rows_en:
        key = row_key(row)
        merged[key] = row.copy()
        if row.get("term_en"):
            by_source_term_en[(row.get("source_id", ""), normalize_key(row["term_en"]))] = key
        if row.get("term_fr"):
            by_source_term_fr[(row.get("source_id", ""), normalize_key(row["term_fr"]))] = key

    for row in rows_fr:
        key = None
        if row.get("term_en"):
            key = by_source_term_en.get((row.get("source_id", ""), normalize_key(row["term_en"])))
        if not key and row.get("term_fr"):
            key = by_source_term_fr.get((row.get("source_id", ""), normalize_key(row["term_fr"])))
        if not key:
            key = row_key(row)

        existing = merged.setdefault(key, {header: "" for header in GLOSSARY_HEADERS})
        for field in GLOSSARY_HEADERS:
            if row.get(field) and not existing.get(field):
                existing[field] = row[field]
            elif field == "def_fr" and row.get(field):
                existing[field] = row[field]
            elif field == "source_fr" and row.get(field):
                existing[field] = row[field]

    rows = list(merged.values())
    rows.sort(key=lambda r: (normalize_key(r.get("source_en") or r.get("source_fr")), normalize_key(r.get("term_en") or r.get("term_fr"))))
    return rows


def fetch_glossary_rows(getter=requests.get, user_agent=None):
    headers = {"User-Agent": user_agent or DEFAULT_USER_AGENT}
    parsed = {}
    for lang, url in GLOSSARY_URLS.items():
        response = getter(url, timeout=60, headers=headers)
        response.raise_for_status()
        parsed[lang] = parse_glossary_html(response.text, lang)
    return merge_glossary_rows(parsed["en"], parsed["fr"])


def read_glossary_csv(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_glossary_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GLOSSARY_HEADERS)
        writer.writeheader()
        writer.writerows([{header: row.get(header, "") for header in GLOSSARY_HEADERS} for row in rows])


def write_glossary_markdown(path, rows):
    lines = [
        "# TBS Policy Glossary",
        "",
        "This file is generated from the English and French TBS policy glossary pages.",
        "",
    ]
    current_source = None
    for row in rows:
        source = row.get("source_en") or row.get("source_fr") or "Unknown source"
        if source != current_source:
            if current_source is not None:
                lines.append("")
            lines.append(f"## {source}")
            lines.append("")
            current_source = source

        term_en = row.get("term_en") or "n/a"
        term_fr = row.get("term_fr") or "n/a"
        lines.append(f"### {term_en} / {term_fr}")
        if row.get("def_en"):
            lines.append("")
            lines.append(f"**EN:** {row['def_en']}")
        if row.get("def_fr"):
            lines.append("")
            lines.append(f"**FR:** {row['def_fr']}")
        if row.get("date_modified"):
            lines.append("")
            lines.append(f"_Glossary page date modified: {row['date_modified']}_")
        lines.append("")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def glossary_row_key(row):
    return "||".join([
        row.get("source_id", ""),
        normalize_key(row.get("term_en", "")),
        normalize_key(row.get("term_fr", "")),
    ])


def compare_glossary_rows(previous, current):
    previous_by_key = {glossary_row_key(row): row for row in previous}
    current_by_key = {glossary_row_key(row): row for row in current}
    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)

    changed = []
    compare_fields = ["source_en", "source_fr", "def_en", "def_fr", "date_modified"]
    for key in sorted(previous_keys & current_keys):
        old = previous_by_key[key]
        new = current_by_key[key]
        fields = [
            field for field in compare_fields
            if clean_text(old.get(field, "")) != clean_text(new.get(field, ""))
        ]
        if fields:
            changed.append({"old": old, "new": new, "fields": fields})

    return {
        "added": [current_by_key[key] for key in sorted(current_keys - previous_keys)],
        "removed": [previous_by_key[key] for key in sorted(previous_keys - current_keys)],
        "changed": changed,
    }


def truncate(value, limit=500):
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def build_glossary_change_payload(changes):
    grouped = {}

    def bucket_for(row):
        source_id = row.get("source_id") or "glossary"
        return grouped.setdefault(
            source_id,
            {
                "source_id": source_id,
                "source_en": row.get("source_en", ""),
                "source_fr": row.get("source_fr", ""),
                "added": [],
                "removed": [],
                "changed": [],
            },
        )

    for row in changes["added"]:
        bucket_for(row)["added"].append({
            "term_en": row.get("term_en", ""),
            "term_fr": row.get("term_fr", ""),
            "def_en": truncate(row.get("def_en", "")),
            "def_fr": truncate(row.get("def_fr", "")),
        })
    for row in changes["removed"]:
        bucket_for(row)["removed"].append({
            "term_en": row.get("term_en", ""),
            "term_fr": row.get("term_fr", ""),
            "def_en": truncate(row.get("def_en", "")),
            "def_fr": truncate(row.get("def_fr", "")),
        })
    for item in changes["changed"]:
        row = item["new"]
        old = item["old"]
        bucket_for(row)["changed"].append({
            "term_en": row.get("term_en", ""),
            "term_fr": row.get("term_fr", ""),
            "fields": item["fields"],
            "old_def_en": truncate(old.get("def_en", "")),
            "new_def_en": truncate(row.get("def_en", "")),
            "old_def_fr": truncate(old.get("def_fr", "")),
            "new_def_fr": truncate(row.get("def_fr", "")),
        })

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "changes_by_source": grouped,
    }


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
