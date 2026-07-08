# Policy Evolution 2026-27 Q2

**Period covered:** 2026-07-01 to 2026-09-30  
**Source:** Auto-analysis comments added to TBS-Policy-Hawk issues.

This file compiles policy-change analysis comments for updates detected during the quarter. Entries are organized chronologically by the effective/update date in the issue GUID.

---

## 2026-07-06 — Digital Talent, Directive on

**Issue:** [#261](https://github.com/PatLittle/TBS-Policy-Hawk/issues/261)  
**Document ID:** 32749  
**Category:** Directive  
**GUID:** `32749_2026-07-06`

### Policy change analysis

Compared the current captured version for `32749_2026-07-06` with the closest prior repository copy:

- New/current capture: `data/Directive/32749_2026-07-06/20260707T163905Z.md`
- Prior version used for comparison: `data/Directive/Digital Talent Directive on_2025-08-31.xml`

#### Summary

This update is a targeted procedural amendment to the mandatory procedures for digital talent sourcing. The main substantive change removes explicit reliance on the GC Digital Talent platform from two TBS-OCIO interaction points and instead states the requirement in platform-neutral terms.

#### Substantive changes identified

| Section | Prior version | New/current version | Interpretation |
|---|---|---|---|
| **A.2.5.1.1** | Required managers/delegated authorities to check TBS-OCIO-led centralized talent recruitment and talent management pools **using the GC Digital Talent platform** before launching department-specific recruitment or initiating a digital services contract. | Requires checking TBS-OCIO-led centralized talent recruitment and talent management pools, but no longer names the GC Digital Talent platform. | The obligation to verify available centralized talent remains, but the channel is now technology-neutral and no longer tied to a named platform. |
| **A.2.5.4.2** | Directed managers/delegated authorities to follow instructions on the GC Digital Talent Platform to complete and submit the Digital Services Contracting Questionnaire. | Requires completion and submission of the Digital Services Contracting Questionnaire directly to TBS-OCIO when qualifying procurements are submitted to contracting authorities, and links to the questionnaire document. | The questionnaire requirement remains, but the process is reframed around direct submission to TBS-OCIO rather than platform-based instructions. |
| **A.2.5.4.3** | Required confirmation with TBS-OCIO **using the GC Digital Talent Platform** that no available pre-qualified talent in a TBS-OCIO-coordinated pool could meet the need before relying on a talent shortage as the rationale for contracting out. | Requires confirmation with TBS-OCIO that no available pre-qualified talent in a TBS-OCIO-coordinated pool could meet the need in the timeframe provided, without specifying the platform. | The pre-contracting confirmation obligation remains, but the specified confirmation mechanism has been removed. |

#### Practical effect

1. **Platform-neutral compliance:** Departments still need to check centralized digital talent pools and engage TBS-OCIO, but the directive no longer makes the GC Digital Talent platform the explicit route for those steps.
2. **Procurement questionnaire retained:** The Digital Services Contracting Questionnaire remains mandatory for contracts, amendments and task authorizations that exceed $40,000 and align with the cited procurement procedures.
3. **Contracting-out rationale still constrained:** Managers and delegated authorities must still confirm with TBS-OCIO that suitable pre-qualified talent is unavailable before citing talent shortage as the primary reason to contract out.

#### Non-substantive changes

Most remaining differences appear to be formatting, link rendering, punctuation spacing, and conversion differences between the prior HTML/XML capture and the current markdown capture.

#### Watch item

Because the named GC Digital Talent platform references were removed rather than replaced with a specific alternate workflow, departments may need operational guidance from TBS-OCIO on the current channel for pool checks, questionnaire submission, and pre-qualified talent confirmation.

---

## 2026-07-07 — Removed from hierarchy: GC Digital Talent Platform

**Issue:** [#264](https://github.com/PatLittle/TBS-Policy-Hawk/issues/264)
**Document ID:** 32750
**Category:** Hierarchy
**GUID:** `hierarchy_removed_32750_2026-07-07`
**Change type:** hierarchy_removed

### Policy change analysis

Compared the current hierarchy-removal capture for `hierarchy_removed_32750_2026-07-07` with the closest prior repository hierarchy snapshot:

- New/current capture: `data/Hierarchy/hierarchy_removed_32750_2026-07-07/20260707T231942Z.md`
- Current hierarchy source: `data/tbs_policy_hierarchy_full.csv`
- Prior version used for comparison: `data/tbs_policy_hierarchy_full.csv` from commit `2b3d38b^`

#### Summary

This is a hierarchy-tree removal for the GC Digital Talent Platform entry, not a full removal of the public page content. The removed hierarchy row had placed document `32750` as a level-4 child under `Directive on Digital Talent`; the captured page still resolves as a sparse GC Digital Talent Platform page with a 2023-04-04 page date.

#### Substantive changes identified

| Area | Evidence before / previous state | Evidence now | Interpretation |
|---|---|---|---|
| **Hierarchy path** | `GC Digital Talent Platform` appeared at minimum level 4 under `Values and Ethics Code for the Public Sector > Foundation Framework for Treasury Board Policies > Service and Digital, Policy on > Digital Talent, Directive on`. | Document `32750` no longer appears in `data/tbs_policy_hierarchy_full.csv`; `data/new_items.csv` records `hierarchy_removed_32750_2026-07-07` as `hierarchy_removed`. | The platform has been removed from the TBS policy hierarchy tree as a child/supporting item under the Directive on Digital Talent. |
| **Public page state** | Prior hierarchy metadata linked to `https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32750`. | The current capture still shows a standalone `GC Digital Talent Platform` page with minimal content and no substantive policy requirements. | The evidence supports hierarchy removal, but not complete retirement of the public URL. |
| **Related policy context** | The previous Directive on Digital Talent text explicitly referenced the GC Digital Talent platform in talent-pool checks, questionnaire submission, and pre-qualified talent confirmation. | Issue #261's 2026-07-06 directive update removed those named platform references and made the relevant procedures platform-neutral or direct-to-TBS-OCIO. | The hierarchy removal is consistent with the directive no longer presenting the platform as the named procedural channel. |

#### Practical effect

1. **Hierarchy cleanup:** The GC Digital Talent Platform no longer appears as a level-4 policy hierarchy item under the Directive on Digital Talent.
2. **Operational dependency reduced:** Together with the July 6 directive amendment, the policy suite no longer points departments to this named platform as the explicit route for key digital talent sourcing steps.
3. **Standalone page still visible:** Because the captured page still resolves, departments should not infer from this evidence alone that the platform URL or service has been fully decommissioned.

#### Non-substantive changes

The capture includes ordinary Canada.ca page chrome and duplicate date-modified footer content. Those elements were not treated as policy hierarchy changes.

#### Watch item

Watch for TBS-OCIO guidance or further site updates that clarify the current operational channel replacing former GC Digital Talent Platform instructions.

---
