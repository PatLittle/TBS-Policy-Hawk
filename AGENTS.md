# TBS Policy Hawk

Policy Hawk monitors Treasury Board policy instruments, implementation notices, and registered Cabinet Directives. It archives evidence, opens GitHub issues for review, and publishes independent fiscal-quarter analysis. Read [README.md](README.md) for the pipeline and its datasets.

## Choose the workflow

- For issue analysis and quarterly report updates, follow [the Policy Evolution analysis skill](skills/tbs-policy-hawk/SKILL.md). On an open issue with comparable Markdown captures, post the unified diff and before-and-after line and character counts before drafting the analysis. Use the substantive analysis for the dated report entry.
- For Cabinet Directive announcements, replacements, and amendments, use [the Cabinet Directive skill](skills/cabinet-directives/SKILL.md). Start with the [register](CabinetDirectives.md) and the dated captures.
- For Policy Hawk videos, use `policy-hawk-sitrep` from `skills/policy-hawk-sitrep/` when available. Start with the relevant quarterly report and the reusable media in `assets/`. SITREP is the quarter-to-date format. End of Quarter covers the full quarter in more detail.
- For monitoring or enrichment changes, trace the normal entry points through [.github/workflows/policy_watch.yml](.github/workflows/policy_watch.yml) and [.github/workflows/issue_enrich.yml](.github/workflows/issue_enrich.yml). The two workflows share a write queue. Preserve retry behavior and verify that a rerun can resume without duplicating issues, comments, or report entries.

## Evidence and reports

- Compare the same instrument or notice against its closest valid earlier capture. Cite the saved revisions and distinguish publication, effective, detection, and capture dates. Treat blocked, incomplete, or rate-limited responses as source-access evidence. Verify substantive source content before drawing policy conclusions.
- Preserve archived captures and historical snapshots. `data/items.csv` is the historical policy capture ledger. `data/new_items.csv` is a transient issue handoff. Keep changes to generated datasets and captures tied to the task.
- Use the Government of Canada’s April–March fiscal year for `PolicyEvolution{YYYY-YYQ#}.md`. Update the existing marker-delimited issue entry when rerunning an analysis. Keep the quarter-start currency baseline fixed and use the repository’s instrument scope for suite counts, with notices reported separately.
- Generate report artifacts from their owning scripts. Use [generate_policy_heatmap.py](scripts/generate_policy_heatmap.py) for heatmaps, [generate_policy_category_history.py](scripts/generate_policy_category_history.py) for instrument composition, and [build_policy_currency_quarter.py](scripts/build_policy_currency_quarter.py) for currency profiles. Review the generated diff before including it.

## Local validation

Run from the repository root. Install Python dependencies with `python -m pip install -r requirements.txt`. Install Chromium with `playwright install chromium` for work that exercises browser captures.

```bash
python -m unittest discover -s tests
git diff --check
```

For a focused check, run `python -m unittest discover -s tests -p 'test_policy_evolution.py'` with the appropriate test filename. Use fixtures or a temporary checkout for tests that write generated files. Issue creation, enrichment, and workflow dispatch can write to GitHub. Run those against the live repository when the task calls for that action.
