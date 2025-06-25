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
    # Enhanced prompt for clarity and grouping
    preamble = (
        f"Below is a unified diff between two XML files. As an expert policy analyst, "
        f"write a concise, clear narrative for policy or technical stakeholders explaining the MAIN changes in content, structure, or meaning. "
        f"Highlight what was added, removed, or changed, grouping similar changes, and note any potential impact or significance. "
        f"Avoid technical jargon and present the analysis in plain language, focusing on practical implications.\n"
        f"Unified diff:\n"
    )
    input_text = preamble + diff_text
    # HuggingFace models have a limit on input length, so we truncate if necessary
    input_text = input_text[:1024]
    summary = summarizer(
        input_text,
        max_length=180,
        min_length=60,
        do_sample=False
    )[0]['summary_text'].strip()
    return diff_text, summary

output = []
for file1, file2 in pairs:
    diff_text, summary = xml_diff_summary(file1, file2)
    output.append({
        "file1": file1,
        "file2": file2,
        "diff": diff_text,
        "summary": summary
    })

with open("xml_diff_narratives.json", "w") as out:
    json.dump(output, out, indent=2)
