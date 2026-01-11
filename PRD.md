# TBS Policy Hawk vNext PRD

## Background
TBS Policy Hawk monitors the Government of Canada TBS Policy Suite RSS feed and creates GitHub issues when a policy is added or updated. The next iteration should refactor the project to be more efficient and to enrich each issue with evidence, diffs, and expert-level summaries of changes.

## Problem Statement
The current workflow detects items and creates issues, but it does not consistently:
- capture the source HTML and a screenshot at time of change,
- compare the new policy text to the previous version,
- provide both granular and high-level analysis of changes, and
- run the full enrichment chain automatically on issue creation.

## Goals
- Detect new and updated policies from the TBS RSS feed.
- Create a GitHub issue for each new/updated policy item.
- On issue creation, automatically enrich the issue with:
  - a screenshot of the HTML page,
  - markdown of the simplified HTML (section=HTML),
  - markdown of the previous version stored in this repo,
  - a plain-text diff and a readable diff summary,
  - an expert-level policy analysis summary of changes.
- Preserve a versioned archive of policy documents for reliable diffs.

## Non-Goals
- Manual review or approvals before posting issue comments.
- Full-text search or public API for the archive.
- UI beyond GitHub issues and repository files.

## Personas
- Policy Analyst: needs accurate, high-signal summaries and clear diffs.
- Maintainer: wants reliable automation and minimal manual steps.

## Success Metrics
- 95%+ of policy updates result in fully enriched issues within 15 minutes.
- Zero duplicate issues for the same policy/version.
- Diff summaries are consistently readable and actionable.

## Assumptions and Constraints
- The RSS feed remains the primary change detection source.
- The policy HTML page supports a simplified view via `section=HTML`.
- The repository can store versioned policy content (SCD2 or similar).
- GitHub Actions runtime is sufficient for screenshot capture and markdown conversion.
- Markdown conversion uses `markitdown` (installed via pip in the workflow).
- Summaries are generated via the Gemini API.

## Current State (Summary)
- RSS ingestion script updates `data/items.csv`.
- Issues are created for new items.
- Policy documents are archived by category in `data/`.
- There is a proof-of-concept diff script and SCD2 update workflow.

## Proposed Solution Overview
Refactor the project into a clear pipeline with these phases:
1. Ingest RSS feed and detect new/updated policy items.
2. Create GitHub issue for each item (new or updated).
3. Trigger a GitHub Action on issue creation to:
   - capture the HTML screenshot,
   - fetch simplified HTML (`section=HTML`),
   - convert HTML to markdown and comment it,
   - load the previous version from repo, convert to markdown, and comment it,
   - compute a diff and comment it,
   - generate an expert-level summary and comment it.

## Functional Requirements
1. RSS and Change Detection
   - Parse RSS feed and persist items with a stable GUID.
   - Detect updates vs new items with version tracking.
   - Avoid duplicates when a job re-runs.

2. Issue Creation
   - Create a GitHub issue for each new/updated policy item.
   - Include key metadata (title, URL, policy type, date, GUID).
   - Tag issues (labels) based on policy type and change type.

3. Issue Enrichment (Triggered on Issue Creation)
   - Capture a screenshot of the policy HTML page.
   - Fetch the simplified HTML using `section=HTML` parameter.
   - Convert the simplified HTML to markdown and comment in the issue (use `markitdown`).
   - Locate the previous version in the repository (SCD2 store).
   - Convert previous version to markdown and comment in the issue.
   - Generate a diff between previous and current markdown.
   - Comment the diff and a readable diff summary.
   - Generate a high-level change summary for expert analysts and comment it (Gemini API).

4. Version Store
   - Persist each policy version with timestamp and GUID.
   - Maintain a mapping for fast lookup of the previous version.
   - Store raw HTML and/or canonical markdown for diffing.

5. Failure Handling and Idempotency
   - Each step should be safe to retry without duplicating comments.
   - If previous version not found, post a clear note and skip diff.
   - Log errors and update the issue with a failure summary.

## Non-Functional Requirements
- Reliability: workflows should not fail on transient network errors.
- Performance: end-to-end enrichment should finish within 15 minutes.
- Cost: stay within GitHub Actions free-tier constraints.
- Security: do not leak tokens; store secrets in GitHub Actions secrets (Gemini API key).

## Data Model (Draft)
- `data/items.csv`: raw feed items with GUID, title, URL, published date.
- `data/tbs_policy_feed_scd2.csv`: version history by GUID and date.
- `data/issue_map.json`: issue number to GUID/version mapping.
- `data/<Category>/<GUID>/<timestamp>.html`: raw HTML snapshots.
- `data/<Category>/<GUID>/<timestamp>.md`: markdown snapshots.

## Workflow Triggers
- Scheduled workflow: checks RSS feed and creates issues for new/updated items.
- Issue-created workflow: runs enrichment chain for each new issue.

## Outputs
Each issue should contain:
- Original issue body with metadata.
- Comment 1: screenshot attachment.
- Comment 2: current version markdown.
- Comment 3: previous version markdown.
- Comment 4: diff (inline or attached).
- Comment 5: expert-level summary of changes.

## Gemini Summary Prompt (Draft)
Use a fixed system prompt and a structured user prompt.

System prompt:
```
You are an expert Canadian federal policy analyst. Write concise, evidence-based change summaries for policy updates. Avoid speculation, cite clauses by heading if available, and separate high-level takeaways from clause-level details.
```

User prompt template:
```
Task: Summarize changes between two versions of a TBS policy document.

Audience: Expert policy analysts.
Tone: Formal, precise, and actionable.

Inputs:
1) Current version (markdown):
<<<CURRENT_MD>>>

2) Previous version (markdown):
<<<PREVIOUS_MD>>>

3) Diff (markdown or unified diff):
<<<DIFF_MD>>>

Output format (markdown):
## High-Level Takeaways
- ...

## Clause-Level Changes
- [Section/Heading] ...
- [Section/Heading] ...

## Notable Additions
- ...

## Notable Removals
- ...

## Potential Impacts
- ...
```

Notes:
- If headings are missing, use best-effort section cues from the text.
- If a section is unchanged, omit it.
- If input is too long, summarize and call out truncation.

## GitHub Actions Sketch (Issue Enrichment)
Workflow: `.github/workflows/issue_enrich.yml`

Trigger:
- `issues` event: `opened`

Jobs:
- `enrich_issue`:
  - Checkout repo.
  - Set up Python.
  - Install deps: `pip install -r requirements.txt` plus `markitdown`.
  - Parse issue body to extract policy URL, GUID, and category.
  - Fetch simplified HTML (`section=HTML`).
  - Capture screenshot of HTML page.
  - Convert simplified HTML to markdown (markitdown).
  - Load previous version from repo (SCD2 store) and convert to markdown if needed.
  - Compute diff between current and previous markdown.
  - Call Gemini API with the prompt template and inputs.
  - Post comments to the issue in order (screenshot, current md, previous md, diff, summary).
  - Mark completion in `issue_map.json` or a dedicated status marker to prevent duplicates.

Environment/Secrets:
- `GEMINI_API_KEY` (GitHub Actions secret).
- `GITHUB_TOKEN` (provided by Actions).

Artifacts:
- Store screenshot in `screenshots/` and upload as an issue attachment.
- Store current/previous markdown in `data/<Category>/<GUID>/`.

## Open Questions
- Should diffs be computed on raw markdown or a normalized text format?
- What is the canonical location for the previous version store?
- What Gemini model and prompt template provide the best policy-analyst summaries?

## Refactor Plan (High Level)
Phase 1: Baseline refactor and data model
- Normalize scripts into clear modules: feed, issues, archive, diff, summary.
- Define canonical paths and SCD2 versioning keys.
- Add structured logs and idempotency guards.

Phase 2: Issue enrichment pipeline
- Build the issue-created GitHub Action.
- Add screenshot capture and HTML fetch for `section=HTML`.
- Convert HTML to markdown and post as issue comments.

Phase 3: Diff + summary
- Load previous version, compute diff, and post.
- Generate expert policy summary based on new/old text + diff.

Phase 4: Reliability and tests
- Add unit tests for parsing and diffing.
- Add integration tests for issue comment creation.
- Add retry logic and error reporting.

Phase 5: Rollout
- Run in parallel with current workflow for validation.
- Validate summaries and diff quality with sample policies.
