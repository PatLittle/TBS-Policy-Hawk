import os
import csv
import json
from github import Github
from playwright.sync_api import sync_playwright

# --- Configuration ---
DATA_DIR = "data"
NEW_ITEMS_CSV_PATH = os.path.join(DATA_DIR, "new_items.csv")
ISSUE_MAP_JSON_PATH = os.path.join(DATA_DIR, "issue_map.json")
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

def take_screenshot(url, filepath):
    """Takes a screenshot of a given URL."""
    print(f"Taking screenshot of {url}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.screenshot(path=filepath, full_page=True)
            browser.close()
        print(f"Screenshot saved to {filepath}")
        return True
    except Exception as e:
        print(f"Error taking screenshot for {url}: {e}")
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

    g = Github(github_token)
    repo = g.get_repo(REPO_NAME)
    issue_map = load_issue_map()
    
    ensure_dir(SCREENSHOTS_DIR)

    with open(NEW_ITEMS_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            guid = row['guid']
            if guid in issue_map:
                print(f"Issue for '{row['title']}' ({guid}) already exists: #{issue_map[guid]}")
                continue

            print(f"Creating issue for new item: {row['title']}")
            screenshot_filename = f"{guid.replace('/', '_')}.png"
            screenshot_filepath = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
            screenshot_success = take_screenshot(row['link'], screenshot_filepath)
            
            screenshot_url = f"https://github.com/{REPO_NAME}/blob/main/{screenshot_filepath}?raw=true"
            issue_body = (f"A new or updated policy document has been detected.\n\n"
                          f"**Title:** {row['title']}\n**Link:** {row['link']}\n"
                          f"**Category:** {row['category']}\n**GUID:** {guid}\n\n"
                          f"### Screenshot\n"
                          f"![Screenshot of policy page]({screenshot_url})" if screenshot_success else "*Failed to capture screenshot.*")

            try:
                issue = repo.create_issue(title=f"Policy Update: {row['title']}", body=issue_body, labels=[row['category'], "policy-update"])
                print(f"Successfully created issue #{issue.number} for '{row['title']}'")
                issue_map[guid] = issue.number
            except Exception as e:
                print(f"Error creating GitHub issue for '{row['title']}': {e}")

    save_issue_map(issue_map)
    print("Issue creation process complete.")

if __name__ == "__main__":
    main()