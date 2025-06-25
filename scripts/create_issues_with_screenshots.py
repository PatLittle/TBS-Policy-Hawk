#!/usr/bin/env python3
import sys
import csv
import subprocess
import os
import hashlib
import requests
import json

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_API = 'https://api.github.com'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

def safe_filename(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16] + '.png'

def take_screenshot(url, out_path):
    subprocess.run([
        'playwright', 'screenshot', 'url', url, out_path
    ], check=True)

def main():
    new_items_csv = 'data/new_items.csv'
    if not os.path.isfile(new_items_csv):
        print("No new_items.csv found, skipping issue creation.")
        sys.exit(0)

    os.makedirs('screenshots', exist_ok=True)
    items = []
    with open(new_items_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue
            title, link, description, category, guid, pubDate = (row + ['']*6)[:6]
            screenshot_file = os.path.join('screenshots', safe_filename(link))
            take_screenshot(link.strip(), screenshot_file)
            items.append({
                'title': title.strip(),
                'link': link.strip(),
                'description': description.strip(),
                'category': category.strip(),
                'guid': guid.strip(),
                'pubDate': pubDate.strip(),
                'screenshot_file': screenshot_file
            })

    if not items:
        print("No items to create issues for.")
        sys.exit(0)

    # Upload all screenshots to a single Gist
    files = {}
    for item in items:
        with open(item['screenshot_file'], 'rb') as f:
            content = f.read()
        files[os.path.basename(item['screenshot_file'])] = {'content': content.decode('latin1')}
    gist_payload = {
        'description': 'Screenshots for new RSS items',
        'public': True,
        'files': files
    }
    resp = requests.post(f'{GITHUB_API}/gists', headers=HEADERS, data=json.dumps(gist_payload))
    resp.raise_for_status()
    gist = resp.json()
    gist_files = gist['files']

    # Create issues for each item with screenshot
    for item in items:
        filename = os.path.basename(item['screenshot_file'])
        raw_url = gist_files[filename]['raw_url']
        issue_title = f'New RSS Item: {item["title"]}'
        body = (
            f'**Published:** {item["pubDate"]}\n'
            f'**Link:** {item["link"]}\n'
            f'**Category:** {item["category"]}\n'
            f'**GUID:** {item["guid"]}\n\n'
            f'{item["description"]}\n\n'
            f'![Screenshot]({raw_url})'
        )
        print(f'Creating issue: {issue_title}')
        subprocess.run([
            'gh', 'issue', 'create',
            '--title', issue_title,
            '--body', body
        ], check=True)

if __name__ == '__main__':
    main()
