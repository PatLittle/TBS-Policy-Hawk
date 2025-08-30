import csv
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path("data")
SCREENSHOTS_DIR = Path("screenshots")
CSV_FILE = DATA_DIR / "items.csv"
ISSUE_MAP_FILE = DATA_DIR / "issue_map.json"

def take_screenshot(url, output_path):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        return True
    except Exception as e:
        print(f"Failed to screenshot {url}: {e}")
        return False

def main():
    if not CSV_FILE.exists():
        print(f"{CSV_FILE} does not exist.")
        return
    if not SCREENSHOTS_DIR.exists():
        os.makedirs(SCREENSHOTS_DIR)

    items = []
    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            items.append(row)

    if not items:
        print("No items to create issues for.")
        return

    issue_map = {}
    for item in items:
        url = item.get("url")
        if not url:
            continue
        filename = f"{abs(hash(url)) & 0xffffffff:x}.png"
        screenshot_path = SCREENSHOTS_DIR / filename
        print(f"Taking screenshot for {url} -> {screenshot_path}")
        success = take_screenshot(url, str(screenshot_path))
        if not success:
            print(f"Skipping item due to screenshot failure: '{url}'")
            continue
        # Here you would create the GitHub issue using the API or CLI, omitted for brevity.
        issue_map[url] = {"screenshot": str(screenshot_path)}  # Add additional metadata as needed

    with open(ISSUE_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(issue_map, f, indent=2)
    print(f"Issue map written to {ISSUE_MAP_FILE}")

if __name__ == "__main__":
    main()
