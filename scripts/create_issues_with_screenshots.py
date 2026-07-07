import os
import csv
import json
import re

# --- Configuration ---
DATA_DIR = "data"
NEW_ITEMS_CSV_PATH = os.path.join(DATA_DIR, "new_items.csv")
ISSUE_MAP_JSON_PATH = os.path.join(DATA_DIR, "issue_map.json")
GLOSSARY_CHANGES_JSON_PATH = os.path.join(DATA_DIR, "glossary_changes.json")
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

    if change_type == "hierarchy_added":
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


def create_issue_with_fallback(repo, title, body, labels):
    labels = [label for label in labels if label]
    try:
        return repo.create_issue(title=title, body=body, labels=labels)
    except Exception as exc:
        if labels != ["policy-update"]:
            print(f"Warning: issue creation with labels {labels} failed: {exc}. Retrying with policy-update only.")
            return repo.create_issue(title=title, body=body, labels=["policy-update"])
        raise

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

    if not os.path.exists(NEW_ITEMS_CSV_PATH):
        print("No new items found (new_items.csv does not exist). Exiting.")
        return

    from github import Github

    g = Github(github_token)
    repo = g.get_repo(REPO_NAME)
    issue_map = load_issue_map()
    glossary_changes = load_glossary_changes()
    
    ensure_dir(SCREENSHOTS_DIR)

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

            try:
                labels = [row.get('category'), "policy-update"]
                if change_type == "glossary":
                    labels.append("glossary-update")
                issue = create_issue_with_fallback(repo, f"{title_prefix}: {row['title']}", issue_body, labels)
                print(f"Successfully created issue #{issue.number} for '{row['title']}'")
                issue_map[guid] = issue.number
            except Exception as e:
                print(f"Error creating GitHub issue for '{row['title']}': {e}")

    save_issue_map(issue_map)
    print("Issue creation process complete.")

if __name__ == "__main__":
    main()
