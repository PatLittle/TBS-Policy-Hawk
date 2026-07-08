# TBS Policy Hawk: Policy Evolution Analysis Skill

Use this skill with Codex to analyze newly detected TBS policy updates, comment the analysis on GitHub issues, label completed issues, and maintain a quarterly `PolicyEvolution{YYYY-YYQ#}.md` report in the repository root.

## Goal

For open `policy-update` issues:

1. Find the current policy document identified by the issue.
2. Locate the closest previous captured version in the repository.
3. Compare the current and previous versions for substantive policy changes.
4. Add an analysis comment to the issue.
5. Add the label `🪄📝AutoAnalyzed` to the issue.
6. Add the same analysis to the fiscal-quarter `PolicyEvolution{YYYY-YYQ#}.md` file in chronological order.

Also analyze related source changes raised by the repository automation:

- policy implementation notices (PINs) that are newly issued, changed, or newly captured
- glossary terms that are added, changed, or deleted
- policy hierarchy tree additions, removals, moves, redirects, or parent-child path changes

---

## Repository assumptions

The repository stores captured policy instruments under `data/`, usually by category and either:

```text
// older naming pattern
data/{Category}/{Title_With_Underscores}_{documentID}_{YYYY-MM-DD}.xml

data/{CategoryPlural}/{Title With Spaces}_{YYYY-MM-DD}.xml

// current/update naming pattern
data/{Category}/{documentID}_{YYYY-MM-DD}/{timestamp}.md
data/{Category}/{documentID}_{YYYY-MM-DD}/{timestamp}.html
```

Examples:

```text
data/Policy/32593_2026-06-01/20260603T202106Z.md
data/Policy/Planning_and_Management_of_Investments__Policy_on_the_32593_2025-05-27.xml

data/Directive/32692_2026-04-30/20260502T124922Z.md
data/Directive/32692_2026-02-20/20260222T171021Z.md
```

Issue bodies usually include:

```markdown
**Title:** Management of Procurement, Directive on the
**Link:** http://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32692
**Category:** Directive
**GUID:** 32692_2026-04-30
```

Issue bodies may also include source-specific metadata:

```markdown
**Hierarchy document ID:** 32750
**Source document ID:** 32692
### Glossary changes
**Added terms:**
**Removed terms:**
**Changed terms:**
```

PIN captures are stored under:

```text
PIN_sources.md
data/PINs/{PIN family}/...
data/PINs/pin_sources_manifest.json
```

Common PIN families include ATIPN, HRIN, SPIN, and RPPN. Treat these as implementation direction and operational evidence, not just supporting links.

---

## Fiscal year and quarter naming

Use the Government of Canada fiscal year: **April 1 to March 31**.

| Date range | Fiscal quarter | Filename example |
|---|---:|---|
| Apr 1 – Jun 30 | Q1 | `PolicyEvolution2026-27Q1.md` |
| Jul 1 – Sep 30 | Q2 | `PolicyEvolution2026-27Q2.md` |
| Oct 1 – Dec 31 | Q3 | `PolicyEvolution2026-27Q3.md` |
| Jan 1 – Mar 31 | Q4 | `PolicyEvolution2025-26Q4.md` |

Formula:

- If month is April–December, fiscal year starts in the calendar year of the date and ends in the next calendar year.
- If month is January–March, fiscal year started in the previous calendar year and ends in the calendar year of the date.

Examples:

```text
2026-04-27 -> FY 2026-27 Q1 -> PolicyEvolution2026-27Q1.md
2026-06-01 -> FY 2026-27 Q1 -> PolicyEvolution2026-27Q1.md
2026-01-15 -> FY 2025-26 Q4 -> PolicyEvolution2025-26Q4.md
```

---

## Workflow

### 1. Find candidate issues

Search open issues in the repository with label `policy-update` and without label `🪄📝AutoAnalyzed`.

Suggested GitHub search query:

```text
repo:PatLittle/TBS-Policy-Hawk is:issue is:open label:policy-update -label:"🪄📝AutoAnalyzed"
```

For each issue, parse:

- issue number
- title
- document title
- document URL
- document ID from `id=...`
- category
- GUID
- update date from GUID suffix
- change type from the issue title or body, such as policy update, hierarchy addition, hierarchy removal, glossary update, or PIN-related update
- hierarchy document ID or source document ID, when present

Example parsing from `GUID: 32692_2026-04-30`:

```text
document_id = 32692
update_date = 2026-04-30
```

If the issue is not a standard policy document update, still complete the same analysis lifecycle: gather evidence, explain the change, comment on the issue, apply `🪄📝AutoAnalyzed`, and update the fiscal-quarter report.

---

### 2. Locate the current captured version

Search repository files for the GUID and document ID.

Preferred current captures:

1. `data/{Category}/{GUID}/*.md`
2. `data/{CategoryPlural}/{GUID}/*.md`
3. `data/{Category}/{GUID}/*.html`
4. `data/{CategoryPlural}/{GUID}/*.html`

Prefer `.md` over `.html` because it is easier to diff semantically. If only `.html` exists, extract visible text from the HTML before comparing.

For PIN analysis, search:

1. `PIN_sources.md`
2. `data/PINs/pin_sources_manifest.json`
3. `data/PINs/{PIN family}/*.md`

For glossary analysis, inspect:

1. the issue body `### Glossary changes` section
2. `data/glossary_changes.json`, if present in the same run
3. `data/policy_glossary.csv`
4. `data/policy_glossary.md`

For hierarchy-tree analysis, inspect:

1. the issue body hierarchy metadata
2. `data/tbs_policy_hierarchy_full.csv`
3. relevant current or prior policy captures for the affected document ID
4. `screenshots/hierarchy_removed_{document_id}_{date}.png` or `screenshots/{GUID}.png`, when present

---

### 3. Locate a previous version

Search repository files using:

- document ID
- document title keywords
- category

Candidate previous files may include:

```text
data/{Category}/{Title}_{documentID}_{YYYY-MM-DD}.xml
data/{CategoryPlural}/{Title}_{YYYY-MM-DD}.xml
data/{Category}/{documentID}_{YYYY-MM-DD}/{timestamp}.md
```

Choose the closest previous version by date that is **strictly earlier** than the update date.

Priority order:

1. Same document ID and closest earlier date.
2. Same normalized title and closest earlier date.
3. Same URL/document ID in file content.
4. Older canonical XML if no closer markdown exists.

Avoid comparing against much older versions if a closer prior capture exists, because unrelated amendments may be mixed into the diff.

For PINs, compare the newly captured notice against any prior capture with the same title, notice number, source URL, or PIN family. If there is no prior local copy, analyze the notice as newly issued and record its operational direction.

For glossary changes, compare by source document ID and bilingual term key. Capture added terms, removed terms, changed English or French definitions, changed source labels, and date-modified changes. Do not treat a date-modified-only change as substantive unless it accompanies term or definition changes.

For hierarchy changes, compare by document ID first, then by normalized title and URL. Determine whether the affected instrument was added, removed, renamed, redirected to another ID, moved under a different hierarchy path, or changed in minimum level.

---

### 4. Normalize text before diffing

Normalize both current and previous versions before analysis:

- Strip HTML navigation, scripts, styles, page chrome and screenshots.
- Convert HTML/XML content to plain markdown-like text where possible.
- Preserve headings, clause numbers, list structure and table content.
- Normalize whitespace.
- Decode HTML entities.
- Treat encoding artifacts as non-substantive, for example:
  - `Â`
  - `â`
  - non-breaking spaces
- Ignore purely formatting changes unless they alter meaning.

Useful comparison units:

- clause numbers, such as `2.2`, `4.1.16`, `A.2.3.1.4`
- appendix sections
- tables and schedules
- note-to-reader amendment bullets
- date-modified metadata

---

### 5. Analyze the change

Focus on substantive changes:

- authority or delegation changes
- new, removed or revised obligations
- reporting changes
- approval threshold changes
- deadline changes
- renamed references or linked instruments
- compliance / monitoring / consequences changes
- appendix schedule/table changes
- changes to application scope
- new implementation notices, PIN effective dates, or operational direction
- glossary additions, removals, or definition changes that affect interpretation
- hierarchy additions, removals, moves, redirects, or parent/child relationship changes

De-emphasize:

- markup changes
- typography
- whitespace
- broken/changed line wrapping
- mojibake/encoding cleanup
- link formatting that does not change the referenced instrument

Classify each change with one or more of:

```text
authority-change
reporting-change
approval-change
scope-change
reference-update
terminology-change
threshold-change
deadline-change
administrative-cleanup
possible-regression
pin-update
glossary-change
hierarchy-change
```

---

### 6. Analyze source-specific changes

#### PINs

When a PIN is newly issued or changed, capture:

- PIN family and notice identifier, if available
- title and source URL
- issue date or page date modified
- linked or affected policy instruments
- new direction, clarification, transitional instruction, deadline, threshold, implementation expectation, or operational obligation
- whether the notice supersedes, amends, or points back to prior guidance

In the interpretation, explain whether the PIN creates a new operational requirement, clarifies existing policy, changes timing or compliance expectations, or is only administrative/publication cleanup.

#### Glossary terms

When glossary terms are added, changed, or deleted, capture:

- source document ID and source instrument title
- added terms in English and French
- removed terms in English and French
- changed terms and the fields changed, including English definition, French definition, source title, or date modified
- whether the change affects scope, eligibility, authority, delegated responsibility, compliance, reporting, or implementation terminology

Do not stop at counting changed terms. Explain what the changed terminology means for interpreting the source instrument.

#### Hierarchy tree

When the policy hierarchy changes, capture:

- affected document ID
- affected title and URL
- added or removed state
- prior and current hierarchy paths, if both are available
- parent, child, or sibling relationship changes
- minimum hierarchy level changes
- possible redirect, rename, retirement, consolidation, or replacement signals

For removals, say whether the instrument appears retired, moved, redirected, or only absent from the hierarchy source. Use "appears removed" if the evidence does not prove retirement.

---

### 7. Draft the issue comment

Use this structure:

```markdown
## Policy change analysis

Compared the current captured version for `{GUID}` with the closest prior repository copy:

- New/current capture: `{current_path}`
- Prior version used for comparison: `{previous_path}`

### Summary

{1–3 sentence summary of the overall nature of the amendment.}

### Substantive changes identified

| Section | Prior version | New/current version | Interpretation |
|---|---|---|---|
| **{section}** | {old effect} | {new effect} | {meaning / operational implication} |

### Practical effect

1. **{effect name}:** {explanation}
2. **{effect name}:** {explanation}
3. **{effect name}:** {explanation}

### Non-substantive changes

{Mention formatting/encoding/link/page-chrome differences, if relevant.}

### Watch item

{Optional: include if something appears moved, removed, or possibly regressed.}
```

For PIN, glossary, and hierarchy issues, adapt the table headings to the source:

```markdown
| Area | Evidence before / previous state | Evidence now | Interpretation |
|---|---|---|---|
| **PIN direction** | {prior notice state or no prior local copy} | {new or changed direction} | {operational impact} |
| **Glossary term** | {old term or definition} | {new term or definition} | {interpretive impact} |
| **Hierarchy path** | {prior path or absent} | {current path or removed} | {suite-structure impact} |
```

Keep the comment concise but useful. Prefer a clear before/after table over long prose. Include explicit "No substantive policy impact found" only after checking the relevant source evidence.

---

### 8. Post the comment and add the label

After posting the analysis comment, add the label:

```text
🪄📝AutoAnalyzed
```

Only add the label after the analysis comment has been successfully created.

If the issue already has an analysis comment and the label, skip unless explicitly asked to update it.

If the issue has an analysis comment but no label, add the label.

If the issue has the label but no analysis comment, inspect before deciding whether to re-run; the label may have been applied manually.

---

### 9. Maintain the quarterly PolicyEvolution file

Determine the fiscal quarter from the issue GUID/update date.

Filename:

```text
PolicyEvolution{YYYY-YYQ#}.md
```

Examples:

```text
PolicyEvolution2026-27Q1.md
PolicyEvolution2025-26Q4.md
```

If the file does not exist, create it with this header:

```markdown
# Policy Evolution {YYYY-YY} Q{#}

**Period covered:** {YYYY-MM-DD} to {YYYY-MM-DD}  
**Source:** Auto-analysis comments added to TBS-Policy-Hawk issues.

This file compiles policy-change analysis comments for updates detected during the quarter. Entries are organized chronologically by the effective/update date in the issue GUID.

---
```

If the file exists, append or update the issue section.

Do **not** duplicate an issue section. If a section for the issue already exists, replace that section with the latest analysis comment.

Section format:

```markdown
## {YYYY-MM-DD} — {Document title}

**Issue:** [#{issue_number}](https://github.com/PatLittle/TBS-Policy-Hawk/issues/{issue_number})  
**Document ID:** {document_id}  
**Category:** {category}  
**GUID:** `{GUID}`
**Change type:** {policy_update | hierarchy_added | hierarchy_removed | glossary | pin}

{analysis comment body, excluding the top `## Policy change analysis` heading if desired, or demoting headings so nesting is valid.}

---
```

Recommended heading normalization when inserting an issue comment:

- `## Policy change analysis` -> `### Policy change analysis`
- `### Summary` -> `### Summary` or `#### Summary`, depending on chosen nesting
- Keep tables intact.

After insertion, sort sections chronologically by update date. For multiple issues on the same date, sort by category then title or by issue number.

---

## Implementation checklist

For each open issue:

```text
[ ] Fetch issue metadata
[ ] Parse title, category, document ID, GUID, update date
[ ] Identify whether the issue is a policy update, PIN update, glossary update, hierarchy addition, or hierarchy removal
[ ] Find current capture path
[ ] Find closest previous capture path
[ ] Inspect PIN_sources.md and data/PINs when PIN evidence is relevant
[ ] Inspect data/policy_glossary.* and glossary_changes.json when glossary evidence is relevant
[ ] Inspect data/tbs_policy_hierarchy_full.csv and hierarchy screenshots when hierarchy evidence is relevant
[ ] Normalize current and previous content
[ ] Compare by clauses/sections
[ ] Compare PIN direction, glossary terms, and hierarchy paths when applicable
[ ] Draft analysis comment
[ ] Post analysis comment
[ ] Add 🪄📝AutoAnalyzed label
[ ] Determine fiscal year/quarter
[ ] Create or update PolicyEvolution{YYYY-YYQ#}.md
[ ] Insert or replace issue section
[ ] Sort sections chronologically
[ ] Commit changes
```

---

## Quality rules

- Be explicit when a finding is inferred rather than directly stated.
- Mention the previous and current paths used for comparison.
- Prefer the closest prior version.
- Do not overstate changes caused only by formatting, conversion, or encoding.
- Call out possible regressions, such as a standard reference changing from a newer version to an older version.
- For removed requirements, say “appears removed” unless the diff clearly proves it was deleted and not moved elsewhere.
- Use “watch item” when a removed requirement may have moved to another instrument or operational process.
- Keep issue comments readable for policy owners, not just developers.

---

## Example issue comment

```markdown
## Policy change analysis

Compared the current captured version for `32692_2026-04-30` with the immediately prior 2026-era repository copy:

- New/current capture: `data/Directive/32692_2026-04-30/20260502T124922Z.md`
- Prior version used for comparison: `data/Directive/32692_2026-02-20/20260222T171021Z.md`

### Summary

This update appears to be a targeted amendment to reduce reporting burden and align procurement reporting with the fiscal year rather than the calendar year.

### Substantive changes identified

| Section | Prior version | New/current version | Interpretation |
|---|---|---|---|
| **Appendix C.2.5.2** | Required annual aggregate reporting for each calendar year, due May 30. | Requires annual aggregate reporting for each fiscal year, due September 30. | Changes the reporting period and deadline. |

### Practical effect

1. **Fiscal-year alignment:** small-value contract and amendment reporting now follows the fiscal year.
2. **Later annual deadline:** the annual deadline shifts from May 30 to September 30.

### Watch item

Check whether removed reporting requirements were moved into another instrument, guide, or operational process rather than fully eliminated.
```

---

## Suggested automation inputs

When running with Codex, provide:

```text
Repository: PatLittle/TBS-Policy-Hawk
Issue search: open policy-update issues without 🪄📝AutoAnalyzed
Quarter file naming: PolicyEvolution{YYYY-YYQ#}.md using GC fiscal year
Output actions: comment issues, label issues, create/update quarterly markdown report
```
