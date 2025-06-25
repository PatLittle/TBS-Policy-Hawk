import os
import re
import json
import difflib
from collections import defaultdict
from lxml import etree
from transformers import pipeline

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

# 2. Summarize XML file differences using HuggingFace Transformers
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def xml_diff_summary(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        xml1 = etree.tostring(etree.parse(f1), pretty_print=True).decode()
        xml2 = etree.tostring(etree.parse(f2), pretty_print=True).decode()
    diff = list(difflib.unified_diff(
        xml1.splitlines(), xml2.splitlines(),
        fromfile=os.path.basename(file1),
        tofile=os.path.basename(file2),
        lineterm=''
    ))
    diff_text = "\n".join(diff)
    preamble = (
        f"Here is a diff between two XML files. Briefly summarize the key differences in plain language for a non-technical reader:\n"
    )
    input_text = preamble + diff_text
    # HuggingFace models have a limit on input length, so we truncate if necessary
    input_text = input_text[:1024]
    summary = summarizer(input_text, max_length=120, min_length=30, do_sample=False)[0]['summary_text']
    return summary

output = []
for file1, file2 in pairs:
    summary = xml_diff_summary(file1, file2)
    output.append({
        "file1": file1,
        "file2": file2,
        "summary": summary
    })

with open("xml_diff_narratives.json", "w") as out:
    json.dump(output, out, indent=2)
