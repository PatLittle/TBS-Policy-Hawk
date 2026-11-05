## Policy change analysis

Compared the PIN evidence for `pin_hrin_147643942e8a_changed_837b14e70ca8_2026-11-04`:

- New/current evidence: `data/PINs/changes/pin_hrin_147643942e8a_changed_837b14e70ca8_2026-11-04/current.md`
- Prior evidence used for comparison: `data/PINs/changes/pin_hrin_147643942e8a_changed_837b14e70ca8_2026-11-04/previous.md`

### Summary
The apparent "change" in the tracked Treasury Board Human Resources Information Notice (HRIN) is entirely an artifact of an HTTP rate-limiting error encountered while retrieving the archived source page (`Rate limit reached` from the Internet Archive). The substantive content of the 2015 bulletin regarding family-related leave codes (Codes 470, 471, and 472) has not experienced a genuine policy modification; rather, the current retrieval failed to capture the page text.

### Substantive changes identified

| Area | Evidence before / previous state | Evidence now | Interpretation |
| :--- | :--- | :--- | :--- |
| **Notice Content** | Complete 2015 HRIN bulletin text regarding Leave Reporting System codes (470, 471, 472) and administrative thresholds. | HTTP rate-limit error message (`Rate limit reached`). | *Inference:* No actual policy or operational modification has occurred. The difference is solely due to a web retrieval failure (anti-scraping rate limit) on the archiving source. |

### Practical effect
* **Operational Direction:** None. Because the change is strictly an archival retrieval error, there are no new practical obligations, altered thresholds, transitional instructions, or compliance effects introduced by this diff.
* **Affected Instruments:** None.

### Non-substantive changes
* Loss of the archived HTML body text due to an external server-side rate-limiting response (`Aitratelimit@archive.org`), resulting in the removal of the notice's date, addressees, signature block, and text from the tracked version.
* Removal of the `Notice modified` date field value (`2015-06-26`).

### Watch item
* Verify subsequent automated scrapes to ensure that future diffs restore the original text once the archival rate-limit window resets, confirming that no underlying Treasury Board policy site modification actually took place.
