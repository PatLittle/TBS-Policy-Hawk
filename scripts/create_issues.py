#!/usr/bin/env python3
import sys
import csv
import subprocess
import os

def main():
    new_items_csv = 'data/new_items.csv'
    if not os.path.isfile(new_items_csv):
        print("No new_items.csv found, skipping issue creation.")
        sys.exit(0)

    items = []
    with open(new_items_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue
            title, link, description, category, guid, pubDate = (row + ['']*6)[:6]
            items.append({
                'title': title.strip(),
                'link': link.strip(),
                'description': description.strip(),
                'category': category.strip(),
                'guid': guid.strip(),
                'pubDate': pubDate.strip()
            })

    if not items:
        print("No items to create issues for.")
        sys.exit(0)

    # Create issues for each item
    for item in items:
        issue_title = f'New RSS Item: {item["title"]}'
        body = (
            f'**Published:** {item["pubDate"]}\n'
            f'**Link:** {item["link"]}\n'
            f'**Category:** {item["category"]}\n'
            f'**GUID:** {item["guid"]}\n\n'
            f'{item["description"]}\n'
        )
        print(f'Creating issue: {issue_title}')
        try:
            subprocess.run([
                'gh', 'issue', 'create',
                '--title', issue_title,
                '--body', body
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create issue for {item['link']}: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
