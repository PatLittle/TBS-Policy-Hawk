---
name: cabinet-directives
description: Assess a user-supplied Canadian Cabinet Directive URL, decide whether it is new, replaces an earlier directive, or changes an existing source, and write an agent-authored strategic deep dive or ordinary change analysis for TBS-Policy-Hawk. Use for requests such as “cab directive change” followed by a link.
---

# Cabinet Directives: strategic analysis with source monitoring

Cabinet Directives are a small, low-velocity collection of Cabinet-endorsed direction. The main task is to understand concepts, approaches, responsibilities and the policy signal. The agent doing this work performs the substantive analysis. Do not invoke Gemini, route the thinking to a weaker model, or mistake first project capture for new government direction.

## Decide what happened

Start with the user-supplied URL, `CabinetDirectives.md`, and `data/CabinetDirectives/manifest.json`. New instruments have no predictable publication location: monitoring observes the registered URLs only. The user can simply say **“cab directive change <URL>”**; do not require them to know the predecessor or to fill in a classification form.

Read the full published directive and its announcement/commencement wording. Determine:

- **New instrument:** a newly issued policy instrument without an identified predecessor. Explain what it introduces and where it fits.
- **Replacement:** an instrument expressly superseding another, including an announced future replacement. Find and read the predecessor as a whole, preferably the closest valid repository capture. Compare the policy approach and implications, not a textual diff.
- **Existing-source change:** an amendment, administrative/link change, redirect, removal or restoration of a registered source. Use the ordinary Policy Hawk/PIN-style analysis lifecycle. Do not create another strategic report just because the monitored page changed. If the content establishes a genuine replacement, reclassify based on that evidence.
- **Inventory baseline:** an older directive newly added to the project. Archive and register it quietly; no quarterly event or retrospective deep dive unless explicitly requested.

Keep publication/announcement, effective, modified, capture and observed-change dates distinct. A future replacement remains **Announced**; its predecessor stays **In Force** until replacement takes effect. A broken page is not proof of retirement.

## Evidence and readable archives

Use one readable instrument folder under `data/CabinetDirectives/`, for example `CD_RegCompRedTape20261021`, with dates that have an explicit meaning. Its register entry has an `Archive` field. Preserve the published HTML and normalized Markdown under `captures/YYYYMMDD/` (use `_02` etc. for further same-day captures). Preserve source URLs and date provenance in metadata.

Reuse `scripts/cabinet_directives.py` for validated retrieval, register updates and evidence capture. Its `fetch_source(url)` returns parsed HTML/Markdown and the resolved URL. `capture(entry, source, manifest, detected=..., change="new"|"replacement", previous_url=..., manual_issue=...)` records user-led additions. Choose the classification and source dates first; the monitor's default first capture is deliberately a quiet baseline. For a replacement, keep both current and predecessor evidence and identify the predecessor explicitly. `update_register` and `save_manifest` persist the result. Do not treat a shorter replacement as a truncated amendment.

Capture **and inspect** screenshots of the current directive and, for a replacement or amendment, the available predecessor. Keep readable `current.png`/`previous.png` beside the archived source. The normal screenshot utility in `scripts/create_issues_with_screenshots.py` can capture live pages; for archived evidence, use Playwright to render that exact HTML and capture the `main` element. Do not silently substitute a newer live page for archived before-state evidence. Preserve a failed-source limitation instead of inventing missing content.

Retain valid sources across timeouts, access blocks, malformed responses and implausible truncation. Monitoring requires two consecutive explicit 404/410 or soft-404 checks before opening an unavailability review; it keeps the last good source. Do not automatically change legal status from availability results.

## New or replacement: write the deep dive

Read the **active fiscal-quarter PolicyEvolution report and the preceding quarter's report**, including the actual issue sections relevant to the directive. Verify supporting source captures and official announcements when they materially affect the interpretation. Link to specific sections/issues. Distinguish direct links, thematic alignment, tension and absence of a demonstrated connection; never infer that the Cabinet Directive caused an earlier bureaucratic amendment.

Write `DeepDive.md` in the instrument folder. Answer **what does it say, what are the impacts, and what does it signal?** Scale depth to the instrument; the following analytical lenses matter more than a rigid template:

- **National scope:** the problem being addressed, intended public/economic outcomes, jurisdictions and populations affected, application boundaries and preserved legal obligations.
- **Strategic approach:** the governing philosophy, instruments and trade-offs. For a replacement, explain what changes in the national policy approach, what continues, and what cannot yet be concluded. Discuss the Cabinet/Prime Minister-level priority signal using stated government priorities and clearly labelled inference, without inventing private motives or treating measured outcomes as already achieved.
- **Responsibilities and authority:** identify positions and organizations; distinguish newly assigned functions, strengthened or reframed existing functions, and duties merely absent from a shorter document. A removed paragraph is not proof that a statutory duty, separate policy or organization has lost its mandate. Follow supporting-policy and announcement evidence before declaring an obligation rescinded.
- **Operational consequences:** processes, cross-government coordination, evidence, reporting, capacity and oversight needed to implement the approach. Identify who must act and what needs authoritative clarification.
- **Tactical application:** specific decisions and practical examples showing what practitioners would do differently. Separate source requirements from recommended preparation; do not invent compliance deadlines, procedures or measurement definitions.
- **Recent policy context:** relate both specific Q2/Q3-type developments and the broader direction of travel. Explain the limits of analogies across regulatory policy, procurement, investment, people management, security and other domains.
- **Uncertainty and watch items:** missing implementation definitions, supporting policy continuity, transition arrangements, monitoring of actual results, and possible unintended effects.

A compact responsibility/action table and a thematic before/after table can help, but do not produce a raw textual diff or make clause-by-clause minutiae the report's organizing principle. Include citations close to substantive findings and a source/evidence list. Identify the report as agent-authored analysis, with an as-of date and the project's personal/unofficial guidance disclaimer. Use the October 2026 `CD_RegCompRedTape20261021/DeepDive.md` as an example of depth, not wording to copy.

## Routine monitoring: ordinary change analysis

`scripts/cabinet_directives.py` runs inside the existing Policy Watch job. It uses the common `data/new_items.csv`, `data/issue_map.json`, issue creation, screenshot and enrichment handoff. The issue workflow points the issue to this skill; it does not analyze Cabinet material or update a quarterly report with Gemini.

For an actual existing-source change, inspect the before/after evidence and explain substantive impact or the lack of it, much as for a PIN. A semantic diff can assist an ordinary amendment review, but is not a deep-dive deliverable. For unavailability, distinguish observed disappearance/redirect from proven retirement and check whether the instrument moved. Keep the analysis proportional; no new `DeepDive.md` for a routine change.

## Quarterly scope and publication

For new/replacement instruments, put a **short synopsis linked to the deep dive in the publication/announcement quarter**, using the Government of Canada fiscal calendar. State the future effective date separately. Do not insert an old instrument into the active quarter merely because it was captured today. If publication cannot be established, record the limitation and avoid manufacturing a dated policy event. Existing-source changes use their supported amendment date, or the observation date with that limitation stated.

For the October 2026 collection introduction, Q3 contains **only** the directive published on **2026-10-21** (issue #527). Issues #528–#532 are older collection baselines, not Q3 policy changes; do not backfill them into Q2 either.

Reuse the existing quarterly report structure and idempotent issue markers, keeping its visuals and unrelated issue sections intact. A synopsis should explain the strategic shift, key practical implications, timing and the report link, without copying the full deep dive into the quarter. Keep Cabinet Directives outside official TBS instrument totals, PIN counts and currency/composition charts.

When publication is authorized by the user's request, post or update the issue's analysis with the synopsis and deep-dive link (or ordinary analysis for a monitored change), commit/push the evidence and report, then apply `🪄📝AutoAnalyzed`. Avoid duplicate comments or report sections. Update the manifest's issue/completion state when completing the review. Do not create a new issue just to reclassify an existing baseline.

Verify the actual artifacts: source dates and replacement relationship, readable paths and working links, screenshot content, report scope and quarter placement, issue/report consistency, and the shared monitoring/issue path. Protect unrelated dirty files and stage only the requested changes. Tests and template validation support this check; they do not substitute for reading the directive and evaluating the analysis.
