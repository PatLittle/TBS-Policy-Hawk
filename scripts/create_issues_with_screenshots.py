import os
import csv
import json
import re
import time

import requests

try:
    from scripts.pin_change_evidence import load_pin_change
except ModuleNotFoundError:
    from pin_change_evidence import load_pin_change

# --- Configuration ---
DATA_DIR = "data"
NEW_ITEMS_CSV_PATH = os.path.join(DATA_DIR, "new_items.csv")
ISSUE_MAP_JSON_PATH = os.path.join(DATA_DIR, "issue_map.json")
GLOSSARY_CHANGES_JSON_PATH = os.path.join(DATA_DIR, "glossary_changes.json")
PENDING_ENRICHMENT_JSON_PATH = os.path.join(DATA_DIR, "pending_enrichment.json")
AUTOANALYZED_LABEL = "🪄📝AutoAnalyzed"
SCREENSHOTS_DIR = "screenshots"
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

# --- Helper Functions ---

def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_issue_map():
    """Loads the GUID to issue number mapping."""
    if os.path.exists(ISSUE_MAP_JSON_PATH):
        with open(ISSUE_MAP_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty dict if file is corrupted or empty
    return {}

def save_issue_map(issue_map):
    """Saves the GUID to issue number mapping."""
    with open(ISSUE_MAP_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(issue_map, f, indent=2)


def load_glossary_changes():
    if not os.path.exists(GLOSSARY_CHANGES_JSON_PATH):
        return {}
    with open(GLOSSARY_CHANGES_JSON_PATH, 'r', encoding='utf-8') as f:
        try:
            payload = json.load(f)
        except json.JSONDecodeError:
            return {}
    return payload.get("changes_by_source", {})


def load_pending_enrichment():
    if not os.path.exists(PENDING_ENRICHMENT_JSON_PATH):
        return []
    try:
        with open(PENDING_ENRICHMENT_JSON_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"Cannot safely read {PENDING_ENRICHMENT_JSON_PATH}; refusing to overwrite pending work."
        ) from exc
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise RuntimeError(f"Invalid pending enrichment data in {PENDING_ENRICHMENT_JSON_PATH}.")
    return payload


def save_pending_enrichment(items):
    unique = {}
    for item in items:
        number = int(item["issue_number"])
        normalized = {
            "issue_number": number,
            "guid": str(item.get("guid", "")),
        }
        if item.get("completion_label"):
            normalized["completion_label"] = str(item["completion_label"])
        previous = unique.get(number)
        if previous and previous.get("completion_label") and not normalized.get("completion_label"):
            continue
        unique[number] = normalized
    with open(PENDING_ENRICHMENT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump([unique[number] for number in sorted(unique)], f, indent=2)
        f.write("\n")


def dispatch_enrichment(repo_name, issue_number, github_token, ref="main", request=requests.post):
    """Explicitly dispatch enrichment; GITHUB_TOKEN-created issues do not trigger issue workflows."""
    url = f"https://api.github.com/repos/{repo_name}/actions/workflows/issue_enrich.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    for attempt in range(1, 4):
        try:
            response = request(
                url,
                headers=headers,
                json={"ref": ref, "inputs": {"issue_number": str(issue_number)}},
                timeout=30,
            )
            if response.status_code == 204:
                return True
            print(f"Enrichment dispatch attempt {attempt} failed: HTTP {response.status_code} {response.text[:300]}")
        except requests.RequestException as exc:
            print(f"Enrichment dispatch attempt {attempt} failed: {exc}")
        if attempt < 3:
            time.sleep(attempt)
    return False


def issue_has_label(repo, issue_number, label):
    issue = repo.get_issue(number=int(issue_number))
    return any(getattr(item, "name", str(item)) == label for item in issue.labels)


def retry_pending_enrichment(items, repo, repo_name, github_token, ref):
    remaining = []
    for item in items:
        completion_label = item.get("completion_label")
        if completion_label:
            try:
                if issue_has_label(repo, item["issue_number"], completion_label):
                    print(f"Confirmed enrichment complete for issue #{item['issue_number']}")
                    continue
            except Exception as exc:
                print(f"Could not confirm enrichment status for issue #{item['issue_number']}: {exc}")

            dispatch_enrichment(repo_name, item["issue_number"], github_token, ref=ref)
            # A successful dispatch only queues work; retain the item until the
            # completion label proves analysis and the report commit succeeded.
            remaining.append(item)
        elif dispatch_enrichment(repo_name, item["issue_number"], github_token, ref=ref):
            print(f"Successfully re-dispatched enrichment for issue #{item['issue_number']}")
        else:
            remaining.append(item)
    return remaining


def pending_record_for_issue(change_type, issue_number, guid, dispatch_succeeded):
    if change_type == "pin":
        return {
            "issue_number": int(issue_number),
            "guid": guid,
            "completion_label": AUTOANALYZED_LABEL,
        }
    if not dispatch_succeeded:
        return {"issue_number": int(issue_number), "guid": guid}
    return None


def safe_filename(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "screenshot"


def document_id_for_row(row):
    for key in ("source_id", "related_guid", "guid"):
        match = re.search(r"(\d+)", row.get(key, ""))
        if match:
            return match.group(1)
    return ""


def summarize_terms(items, label):
    if not items:
        return ""
    lines = [f"**{label}:**"]
    for item in items[:10]:
        term_en = item.get("term_en") or "n/a"
        term_fr = item.get("term_fr") or "n/a"
        fields = item.get("fields")
        suffix = f" ({', '.join(fields)})" if fields else ""
        lines.append(f"- `{term_en}` / `{term_fr}`{suffix}")
    if len(items) > 10:
        lines.append(f"- ...and {len(items) - 10} more.")
    return "\n".join(lines)


def glossary_change_section(source_id, glossary_changes):
    payload = glossary_changes.get(source_id)
    if not payload:
        return ""

    added = payload.get("added", [])
    removed = payload.get("removed", [])
    changed = payload.get("changed", [])
    total = len(added) + len(removed) + len(changed)
    source_title = payload.get("source_en") or payload.get("source_fr") or source_id
    parts = [
        "### Glossary changes",
        "",
        f"{total} glossary term change(s) were detected for `{source_id}` ({source_title}).",
        "",
    ]
    for section in [
        summarize_terms(added, "Added terms"),
        summarize_terms(removed, "Removed terms"),
        summarize_terms(changed, "Changed terms"),
    ]:
        if section:
            parts.extend([section, ""])
    return "\n".join(parts).rstrip()


def issue_body_for_row(row, screenshot_success, screenshot_url, glossary_changes):
    change_type = row.get("change_type") or "policy_update"
    doc_id = document_id_for_row(row)
    glossary_section = glossary_change_section(doc_id, glossary_changes)
    screenshot_section = (
        f"### Screenshot\n![Screenshot of policy page]({screenshot_url})"
        if screenshot_success else
        "*Failed to capture screenshot.*"
    )

    if change_type == "pin":
        metadata_path = row.get("filename", "")
        evidence = load_pin_change(metadata_path)
        metadata = evidence["metadata"]
        pin_change = evidence["change_type"]
        family = metadata.get("family") or metadata.get("pin_family") or row.get("source_id", "")
        identifier = (
            metadata.get("notice_identifier")
            or metadata.get("identifier")
            or metadata.get("notice_code")
            or "Not stated"
        )
        detected = metadata.get("detected_date") or metadata.get("date") or row.get("updated_date", "")[:10]
        previous_path = evidence["previous_path"] or "None (newly tracked notice)"
        current_path = evidence["current_path"] or "None (notice removed)"
        body = (
            "A substantive change to a tracked policy implementation notice was detected.\n\n"
            f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
            f"**Category:** PIN\n**GUID:** {row['guid']}\n"
            "**Change type:** pin\n"
            f"**PIN change:** {pin_change}\n"
            f"**PIN family:** {family or 'Unknown'}\n"
            f"**Notice identifier:** {identifier}\n"
            f"**Detected date:** {detected}\n"
            f"**PIN metadata:** {evidence['metadata_path']}\n"
            f"**Previous evidence:** {previous_path}\n"
            f"**Current evidence:** {current_path}\n\n"
            f"{screenshot_section}"
        )
    elif change_type == "hierarchy_added":
        body = (
            "A policy instrument has been added to the TBS policy hierarchy tree.\n\n"
            f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
            f"**Category:** {row['category']}\n**GUID:** {row['guid']}\n"
            f"**Hierarchy document ID:** {doc_id}\n\n"
            f"{row.get('change_summary', '')}\n\n"
            f"{screenshot_section}"
        )
    elif change_type == "hierarchy_removed":
        body = (
            "A policy instrument has been removed from the TBS policy hierarchy tree.\n\n"
            f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
            f"**Category:** {row['category']}\n**GUID:** {row['guid']}\n"
            f"**Hierarchy document ID:** {doc_id}\n\n"
            f"{row.get('change_summary', '')}\n\n"
            f"{screenshot_section}"
        )
    elif change_type == "glossary":
        body = (
            "Glossary terms changed for a tracked policy instrument, and no policy update issue was created for that source in this run.\n\n"
            f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
            f"**Category:** {row['category']}\n**GUID:** {row['guid']}\n"
            f"**Source document ID:** {doc_id}\n\n"
            f"{glossary_section}\n\n"
            f"{screenshot_section}"
        )
    else:
        body = (
            f"A new or updated policy document has been detected.\n\n"
            f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
            f"**Category:** {row['category']}\n**GUID:** {row['guid']}\n\n"
            f"{screenshot_section}"
        )

    if glossary_section and change_type not in {"glossary"}:
        body = f"{body}\n\n{glossary_section}"
    return body


def create_issue_with_fallback(repo, title, body, labels, fallback_labels=None):
    labels = [label for label in labels if label]
    fallback_labels = [label for label in (fallback_labels or ["policy-update"]) if label]
    try:
        return repo.create_issue(title=title, body=body, labels=labels)
    except Exception as exc:
        if labels != fallback_labels:
            print(f"Warning: issue creation with labels {labels} failed: {exc}. Retrying with {fallback_labels}.")
            return repo.create_issue(title=title, body=body, labels=fallback_labels)
        raise


def ensure_pin_update_label(repo):
    try:
        repo.get_label("pin-update")
    except Exception:
        repo.create_label(
            name="pin-update",
            color="7a3e9d",
            description="Tracked policy implementation notice change",
        )

def take_screenshot(url, filepath):
    """Takes a screenshot of a given URL with a Windows 11 user agent. On failure, retries with HTTPS."""
    from playwright.sync_api import sync_playwright

    WINDOWS11_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print(f"Taking screenshot of {url}...")
    def attempt_screenshot(target_url):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(user_agent=WINDOWS11_UA)
                page.goto(target_url, wait_until='networkidle', timeout=60000)
                page.screenshot(path=filepath, full_page=True)
                browser.close()
            print(f"Screenshot saved to {filepath}")
            return True
        except Exception as e:
            print(f"Error taking screenshot for {target_url}: {e}")
            return False

    # First attempt
    if attempt_screenshot(url):
        return True
    # If failed, try switching http:// to https://
    if url.startswith("http://"):
        https_url = "https://" + url[len("http://") :]
        print(f"Retrying screenshot with HTTPS: {https_url}")
        return attempt_screenshot(https_url)
    return False

# --- Main Script ---

def main():
    """Main function to create GitHub issues for new policy items."""
    if not REPO_NAME:
        print("Error: GITHUB_REPOSITORY environment variable not set.")
        return

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return

    pending = load_pending_enrichment()
    if not os.path.exists(NEW_ITEMS_CSV_PATH) and not pending:
        print("No new items or pending enrichment dispatches. Exiting.")
        return

    from github import Github

    g = Github(github_token)
    repo = g.get_repo(REPO_NAME)
    issue_map = load_issue_map()
    glossary_changes = load_glossary_changes()
    ref = os.environ.get("GITHUB_REF_NAME") or os.environ.get("GITHUB_DEFAULT_BRANCH") or "main"
    pending = retry_pending_enrichment(pending, repo, REPO_NAME, github_token, ref)
    save_pending_enrichment(pending)
    
    ensure_dir(SCREENSHOTS_DIR)

    if not os.path.exists(NEW_ITEMS_CSV_PATH):
        print("Pending enrichment retry process complete.")
        return

    with open(NEW_ITEMS_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            guid = row['guid']
            if guid in issue_map:
                print(f"Issue for '{row['title']}' ({guid}) already exists: #{issue_map[guid]}")
                continue

            print(f"Creating issue for new item: {row['title']}")
            screenshot_filename = f"{safe_filename(guid)}.png"
            screenshot_filepath = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
            screenshot_success = take_screenshot(row['link'], screenshot_filepath)
            
            screenshot_url = f"https://github.com/{REPO_NAME}/blob/main/{screenshot_filepath}?raw=true"
            issue_body = issue_body_for_row(row, screenshot_success, screenshot_url, glossary_changes)
            change_type = row.get("change_type") or "policy_update"
            title_prefix = "Policy Update"
            if change_type == "hierarchy_added":
                title_prefix = "Policy Hierarchy Addition"
            elif change_type == "hierarchy_removed":
                title_prefix = "Policy Hierarchy Removal"
            elif change_type == "glossary":
                title_prefix = "Glossary Update"
            elif change_type == "pin":
                pin_change = load_pin_change(row.get("filename", ""))["change_type"]
                title_prefix = f"PIN {pin_change.title()}"

            try:
                labels = [row.get('category'), "policy-update"]
                if change_type == "glossary":
                    labels.append("glossary-update")
                elif change_type == "pin":
                    ensure_pin_update_label(repo)
                    labels.append("pin-update")
                fallback_labels = ["policy-update", "pin-update"] if change_type == "pin" else None
                issue = create_issue_with_fallback(
                    repo,
                    f"{title_prefix}: {row['title']}",
                    issue_body,
                    labels,
                    fallback_labels=fallback_labels,
                )
                print(f"Successfully created issue #{issue.number} for '{row['title']}'")
                issue_map[guid] = issue.number
                dispatched = dispatch_enrichment(REPO_NAME, issue.number, github_token, ref=ref)
                pending_record = pending_record_for_issue(
                    change_type, issue.number, guid, dispatched
                )
                if pending_record:
                    pending.append(pending_record)
                save_pending_enrichment(pending)
            except Exception as e:
                print(f"Error creating GitHub issue for '{row['title']}': {e}")

    save_issue_map(issue_map)
    print("Issue creation process complete.")

if __name__ == "__main__":
    main()
