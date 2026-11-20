---
name: policy-hawk-sitrep
description: Create narrated TBS Policy Hawk videos from a fiscal-quarter PolicyEvolution report using Brag and HyperFrames. Use for Policy Hawk video updates, SITREPs, and End of Quarter briefings.
---

# Policy Hawk briefing videos

Use Brag for planning and packaging and HyperFrames for composition, preview, validation, and rendering. Both Policy Hawk formats include narration and use the radio opening and closing below. Their runtimes follow the material in the report.

## Choose the format

- **SITREP** is the default for a Policy Hawk video request, including a general Policy Hawk Brag. Use it for periodic updates during a quarter. Give a concise quarter-to-date briefing through the requested cutoff or the latest supported date.
- **End of Quarter** is for the full fiscal quarter. Summarize the quarter’s changes in more detail, explain practical implications supported by the evidence, and connect related entries when the sources support the relationship.

## Build the rundown

Use the supplied `PolicyEvolution{YYYY-YYQ#}.md` report, or find the report for the requested quarter in [TBS-Policy-Hawk](https://github.com/PatLittle/TBS-Policy-Hawk). Resolve the asset paths below from the repository root. Keep the coverage window and evidence cutoff visible. Use report figures and charts from snapshots appropriate to that cutoff.

1. **Policy suite overview.** Cover currency, composition, and structural changes together before the dated entries. Use the currency profile to explain the age or recency of current instruments and the changes the profile records. Describe the mix of instrument types and any structural shifts the report identifies, including changes to the mandatory and voluntary mix or audience when documented. State when the report finds no structural shift. Label instrument and notice totals with their own scope and snapshot dates.
2. **Dated entries.** Inventory every dated report entry in scope and mention each in the video, including separate entries on the same date. The SITREP covers entries through its cutoff unless the user supplies a narrower interval. End of Quarter covers the full report for that quarter and gives each entry more context. Chronological order is the default. Related entries may share a scene when each remains identifiable by date and subject. Identify what changed, who needs to act, and when wherever those details are supported. Keep publication, capture, effective, and submission dates distinct. If a supporting notice explains an already counted amendment, mention both report entries and count the amendment once. Describe inventory baselines, access failures, and recoveries as monitoring events when the report includes them.
3. **Runtime.** Budget time from the number of entries and the detail the format calls for. Draft the complete rundown, time the narration and readable holds, and allow time for the whole closing sequence. More entries or a fuller explanation can extend the video. Use short narration and shared scenes to tighten a cut while retaining all dated entries.

Review linked issues, original instruments and dated captures for the claims you use. Make narration complement the on-screen figures and dates. Keep a source note for each entry and check the final edit against the rundown.

## Open on the HawkBITR

- Reuse `assets/hawkbitr-transmitting.svg`, with `assets/hawkbitr-1200.png` as a fallback. Keep the MBITR-style cartoon illustration and its fictional **HawkBITR** case branding.
- Set the centered display to **Pol Hawk TAC FREQ** in the composition copy. Update the existing display lettering to match this wording.
- Play a short push-to-talk click and let it clear the first word. The opening line is **“Hawk-1 sending Policy Suite SITREP.”** Use Kokoro `am_michael`. Apply a radio bandpass and restrained bit crushing to this line while protecting intelligibility.
- Animate drawn waves outward from the integrated speaker during the transmission. Time the motion to the voiced portions and let it settle as the call ends. Keep the antenna, speaker and display visible.

## Mix the briefing

- Use Kokoro `am_michael` for the main narration. Keep every line after the opening call clean and intelligible. Give amounts, dates and instrument identifiers room in the read.
- Use **“Carry On” by Michael Ramir C.**, the [Mixkit classic-rock stock track](https://mixkit.co/free-stock-music/classic-rock/) under the [Mixkit Stock Music Free License](https://mixkit.co/license/modal/musicFree/). Reuse the verified copy from a previous SITREP if available. Start the bed after the radio call begins, balance its guitar and drums beneath speech, and fade it at the close. Keep the Mixkit credit and source in the delivery notes.
- Use the Mixkit recording named above. Exclude the AC/DC recording, riff, melody and lyrics.

## Close in this order

1. Say **“End SITREP. Hawk One out.”** in the clear Kokoro `am_michael` narration voice. Finish the music fade by the start of the disclaimer.
2. On the final slide, play `policy-hawk-disclaimer-fast.wav` from `assets/policy-hawk-disclaimer-fast-2026-10-18/` as supplied. Display the full, exact text from `transcript.txt` for the entire 9.658-second recording. Keep it legible at the delivery size. The recording has its own announcer voice and treatment.
3. After the disclaimer finishes, play one hawk wink and one synchronized bell. Reuse the open and wink poses from `assets/wink-gif-loop.gif` as a single timed wink. Reuse the previous SITREP’s bell cue when available. Return to the open-eye pose and hold the final frame briefly. Keep the disclaimer on the final slide.

Point viewers to the relevant PolicyEvolution report for the write-up and original sources.

## Deliver

Render the requested video and include the editable composition, poster, share copy, synchronized captions, and source and media credits. Check that the export covers all three overview topics and every dated entry in scope. Verify the opener’s display, spoken line, and speaker-wave timing. Check the signoff, complete disclaimer, finished music fade, and single wink and bell in the exported ending. Review the phrasing of counts, dates and obligations against the source notes.
