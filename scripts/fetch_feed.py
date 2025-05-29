import os
import csv
import feedparser
import requests

# Configuration
FEED_URL = 'https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=25'
CSV_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'items.csv')
GITHUB_API = 'https://api.github.com'
REPO = os.getenv('GITHUB_REPOSITORY')  # e.g., 'owner/name'
TOKEN = os.getenv('GITHUB_TOKEN')

# Load existing items (by link)
existing = set()
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(row['link'])

# Fetch feed
feed = feedparser.parse(FEED_URL)
new_items = []
for entry in feed.entries:
    if entry.link not in existing:
        new_items.append(entry)

# Append to CSV and create issues
if new_items:
    # Append rows to CSV
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for e in new_items:
            title = e.get('title', '')
            link = e.get('link', '')
            description = e.get('description', '') or e.get('summary', '')
            category = e.get('category', '')
            guid = e.get('id', '')
            pubDate = e.get('published', '')
            writer.writerow([title, link, description, category, guid, pubDate])

    # Create GitHub Issues
    headers = {'Authorization': f'token {TOKEN}'}
    for e in new_items:
        issue = {
            'title': f"New RSS Item: {e.get('title', '')}",
            'body': (
                f"**Published:** {e.get('published', '')}\n"
                f"**Link:** {e.get('link', '')}\n"
                f"**Category:** {e.get('category', '')}\n"
                f"**GUID:** {e.get('id', '')}\n\n"
                f"{e.get('description', '') or e.get('summary', '')}"
            )
        }
        url = f"{GITHUB_API}/repos/{REPO}/issues"
        resp = requests.post(url, json=issue, headers=headers)
        resp.raise_for_status()
