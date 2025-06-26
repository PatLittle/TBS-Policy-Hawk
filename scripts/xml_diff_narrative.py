import os
import re
import json
from collections import defaultdict

# 1. Find XML pairs with matching names except date
pattern = re.compile(r"^(.*?)(\d{4}-\d{2}-\d{2})\.xml$")
files = defaultdict(list)
for root, dirs, filenames in os.walk('data'):
    for f in filenames:
        if f.endswith('.xml'):
            m = pattern.match(f)
            if m:
                prefix = os.path.join(root, m.group(1))
                files[prefix].append(os.path.join(root, f))

pairs = []
for prefix, flist in files.items():
    if len(flist) >= 2:
        # sort files by date in filename (descending)
        flist.sort(reverse=True)
        for i in range(len(flist)-1):
            pairs.append([flist[i], flist[i+1]])

with open("pairs.json", "w") as out:
    json.dump(pairs, out)

if len(pairs) == 0:
    print("No XML pairs found for diff.")
    exit(0)
