import os
import csv
import feedparser

# Configuration
FEED_URL = 'https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=25'
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ITEMS_CSV = os.path.join(BASE_DIR, 'data', 'items.csv')
NEW_CSV = os.path.join(BASE_DIR, 'data', 'new_items.csv')

# Load existing links
existing = set()
if os.path.exists(ITEMS_CSV):
    with open(ITEMS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(row['link'])

# Fetch feed
feed = feedparser.parse(FEED_URL)
new_entries = []
for e in feed.entries:
    if e.link not in existing:
        new_entries.append(e)

# Write new_items.csv
with open(NEW_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['title','link','description','category','guid','pubDate'])
    for e in new_entries:
        writer.writerow([
            e.get('title',''),
            e.get('link',''),
            e.get('description','') or e.get('summary',''),
            e.get('category',''),
            e.get('id',''),
            e.get('published','')
        ])

# Append to items.csv
with open(ITEMS_CSV, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for e in new_entries:
        writer.writerow([
            e.get('title',''),
            e.get('link',''),
            e.get('description','') or e.get('summary',''),
            e.get('category',''),
            e.get('id',''),
            e.get('published','')
        ])
