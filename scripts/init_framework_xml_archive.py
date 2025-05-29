# scripts/init_framework_xml_archive.py

import os
import re
import requests
import feedparser

# Feed URL for Framework
FEED_URL = 'https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=79'
TARGET_DIR = os.path.join('data', 'Framework')

# Make sure the target directory exists
os.makedirs(TARGET_DIR, exist_ok=True)

# Fetch and parse the feed
feed = feedparser.parse(FEED_URL)

def sanitize_filename(filename):
    # Remove/replace characters invalid in filenames
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)

for entry in feed.entries:
    # Construct XML download URL
    xml_url = f"{entry.link}&section=xml"
    
    # Compose filename
    title = entry.title
    guid = entry.id if 'id' in entry else entry.guid
    filename = f"{sanitize_filename(title)}_{sanitize_filename(guid)}.xml"
    filepath = os.path.join(TARGET_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        continue

    # Download the XML content
    resp = requests.get(xml_url)
    if resp.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {xml_url} (status: {resp.status_code})")
