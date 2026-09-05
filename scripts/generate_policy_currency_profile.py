#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, html, json, mimetypes
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

DEFAULT_PALETTE = {
    "background": "#F8F9FB",
    "card": "#FFFFFF",
    "ink": "#15264A",
    "muted_ink": "#6B7280",
    "grid": "#D9E0E8",
    "baseline_line": "#98A2B3",
    "current_line": "#1267D8",
    "row_baseline": "#F4F5F7",
    "row_current": "#EAF4FF",
    "added": "#148A3B",
    "modified": "#D69E00",
    "deleted": "#D7263D",
    "baseline_bins": ["#233C39", "#323E47", "#9A854F", "#A57249", "#8C4A3E"],
    "current_bins":  ["#076A61", "#1D526E", "#FCB400", "#FF7402", "#E22900"],
    "event_colors": ["#E22900", "#E39B00", "#1267D8", "#168A50", "#7A56C2", "#A06B00"],
}
DEFAULT_BINS = [
    {"label": "<12 months", "min_years": 0.0, "max_years": 1.0},
    {"label": "1–3 yr", "min_years": 1.0, "max_years": 3.0},
    {"label": "3–5 yr", "min_years": 3.0, "max_years": 5.0},
    {"label": "5–10 yr", "min_years": 5.0, "max_years": 10.0},
    {"label": "10+ yr", "min_years": 10.0, "max_years": None},
]
def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
def years_between(later: date, earlier: date) -> float:
    return (later - earlier).days / 365.25
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
def fmt_age(value: float) -> str:
    return f"{value:.1f} yr"
def fmt_pct(n: int, total: int) -> str:
    return "0%" if total <= 0 else f"{round(n / total * 100):d}%"
def load_logo_data_uri(path: Optional[Path]) -> Optional[str]:
    if not path:
        return None
    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
def merge_palette(user: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    p = dict(DEFAULT_PALETTE)
    if user:
        p.update(user)
    return p
def assign_bin(age: float, bins: Sequence[Mapping[str, Any]]) -> int:
    for i, b in enumerate(bins):
        lo = float(b.get("min_years", 0.0)); hi = b.get("max_years")
        if age >= lo and (hi is None or age < float(hi)):
            return i
    raise ValueError(f"Age {age} did not match any bin")
def aggregate_snapshot(instruments, snapshot_date: date, bins, topic_order):
    grouped = {t: [] for t in topic_order}
    for row in instruments:
        grouped.setdefault(str(row["topic"]), []).append(row)
    result = {}
    for topic in topic_order:
        items = grouped.get(topic, [])
        ages = []; bin_counts = [0] * len(bins)
        for item in items:
            vdate = parse_date(str(item["version_date"]))
            if vdate > snapshot_date:
                raise ValueError(f"{item['id']} has version_date {vdate} after snapshot {snapshot_date}")
            age = years_between(snapshot_date, vdate)
            ages.append(age)
            bin_counts[assign_bin(age, bins)] += 1
        result[topic] = {"count": len(items), "avg_age": (sum(ages) / len(ages)) if ages else 0.0, "bins": bin_counts}
    return result
def infer_changes(baseline, current, topic_order):
    changes = {t: {"added": 0, "modified": 0, "deleted": 0} for t in topic_order}
    b = {str(x["id"]): x for x in baseline}; c = {str(x["id"]): x for x in current}
    for iid in sorted(set(b) | set(c)):
        br = b.get(iid); cr = c.get(iid)
        if br is None:
            changes.setdefault(str(cr["topic"]), {"added": 0, "modified": 0, "deleted": 0})
            changes[str(cr["topic"])]["added"] += 1; continue
        if cr is None:
            changes.setdefault(str(br["topic"]), {"added": 0, "modified": 0, "deleted": 0})
            changes[str(br["topic"])]["deleted"] += 1; continue
        btopic = str(br["topic"]); ctopic = str(cr["topic"])
        if btopic != ctopic:
            changes.setdefault(btopic, {"added": 0, "modified": 0, "deleted": 0})
            changes.setdefault(ctopic, {"added": 0, "modified": 0, "deleted": 0})
            changes[btopic]["deleted"] += 1; changes[ctopic]["added"] += 1
        elif str(br["version_date"]) != str(cr["version_date"]):
            changes[btopic]["modified"] += 1
    return changes
def normalize_input(cfg):
    bins = cfg.get("bins") or DEFAULT_BINS
    baseline_date = parse_date(str(cfg["baseline_date"])); current_date = parse_date(str(cfg["current_date"]))
    topic_order = list(cfg.get("topic_order") or [x["name"] for x in cfg.get("topics", [])])
    if "topics" in cfg:
        topics = []
        for t in cfg["topics"]:
            topics.append({
                "name": str(t["name"]),
                "changes": {"added": int(t.get("changes", {}).get("added", 0)),
                            "modified": int(t.get("changes", {}).get("modified", 0)),
                            "deleted": int(t.get("changes", {}).get("deleted", 0))},
                "baseline": {"count": int(t["baseline"]["count"]), "avg_age": float(t["baseline"]["avg_age"]), "bins": [int(x) for x in t["baseline"]["bins"]]},
                "current": {"count": int(t["current"]["count"]), "avg_age": float(t["current"]["avg_age"]), "bins": [int(x) for x in t["current"]["bins"]]},
            })
    else:
        baseline_instruments = cfg["baseline_instruments"]; current_instruments = cfg["current_instruments"]
        if not topic_order:
            topic_order = sorted({str(x["topic"]) for x in baseline_instruments} | {str(x["topic"]) for x in current_instruments})
        bstats = aggregate_snapshot(baseline_instruments, baseline_date, bins, topic_order)
        cstats = aggregate_snapshot(current_instruments, current_date, bins, topic_order)
        changes = infer_changes(baseline_instruments, current_instruments, topic_order)
        topics = [{"name": topic, "changes": changes[topic], "baseline": bstats[topic], "current": cstats[topic]} for topic in topic_order]
    if topic_order:
        by_name = {t["name"]: t for t in topics}
        topics = [by_name[n] for n in topic_order if n in by_name]
    for t in topics:
        for snap in ("baseline", "current"):
            if len(t[snap]["bins"]) != len(bins):
                raise ValueError(f"{t['name']} {snap} bins mismatch")
            if sum(t[snap]["bins"]) != t[snap]["count"]:
                raise ValueError(f"{t['name']} {snap}: bin counts sum mismatch")
    out = dict(cfg); out.update({"bins": bins, "topics": topics, "baseline_date_obj": baseline_date, "current_date_obj": current_date})
    return out
def svg_text(x, y, text, cls="", anchor="start", fill=None):
    attrs = []
    if cls: attrs.append(f'class="{cls}"')
    if anchor != "start": attrs.append(f'text-anchor="{anchor}"')
    if fill: attrs.append(f'fill="{fill}"')
    extra = (" " + " ".join(attrs)) if attrs else ""
    return f'<text x="{x:.1f}" y="{y:.1f}"{extra}>{html.escape(text)}</text>'
def render_svg(cfg, logo_uri=None):
    cfg = normalize_input(cfg); palette = merge_palette(cfg.get("palette")); topics = cfg["topics"]; bins = cfg["bins"]; events = cfg.get("events", [])
    W = int(cfg.get("width", 1500)); margin = 24; header_h = 165; topic_w = 505; age_w = 535; dist_w = W - (margin * 2) - topic_w - age_w
    row_pair_h = 64; table_y = header_h + 58; table_h = row_pair_h * len(topics); footer_h = 62; H = table_y + table_h + footer_h
    x_topic = margin; x_age = x_topic + topic_w; x_dist = x_age + age_w
    topic_name_w = 240; row_x = x_topic + topic_name_w; current_num_x = x_topic + topic_w - 24; changes_start_x = row_x + 90
    age_plot_x0 = x_age + 18; age_plot_x1 = x_age + age_w - 26; age_plot_w = age_plot_x1 - age_plot_x0; max_age = float(cfg.get("max_age_years", 15))
    def age_x(v): return age_plot_x0 + clamp(v, 0.0, max_age) / max_age * age_plot_w
    dist_x0 = x_dist + 18; dist_x1 = x_dist + dist_w - 20; dist_plot_w = dist_x1 - dist_x0
    baseline_bins = palette["baseline_bins"]; current_bins = palette["current_bins"]; event_colors = palette["event_colors"]
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">')
    out.append('<title id="title">Policy suite currency profile — fiscal-quarter change view</title>')
    out.append('<desc id="desc">A deterministic SVG dashboard showing baseline and current policy-suite age distribution and changes by topic.</desc>')
    out.append(f'''
<style>
text {{ font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{palette["ink"]}; }}
.title {{ font-size:33px; font-weight:760; }}
.subtitle {{ font-size:13px; fill:{palette["muted_ink"]}; }}
.badge {{ font-size:14px; font-weight:700; fill:white; }}
.section {{ font-size:14px; font-weight:720; }}
.subsection {{ font-size:11px; fill:{palette["muted_ink"]}; }}
.topic {{ font-size:13px; font-weight:620; }}
.base {{ font-size:11px; fill:{palette["muted_ink"]}; }}
.current {{ font-size:11px; font-weight:720; fill:{palette["current_line"]}; }}
.metric {{ font-size:12px; font-weight:700; }}
.age-base {{ font-size:11px; font-weight:650; fill:{palette["muted_ink"]}; }}
.age-current {{ font-size:11px; font-weight:760; fill:{palette["ink"]}; }}
.axis {{ font-size:10px; fill:{palette["muted_ink"]}; }}
.legend {{ font-size:10px; fill:{palette["ink"]}; }}
.legend-title {{ font-size:11px; font-weight:720; }}
.bintext {{ font-size:9px; font-weight:720; }}
.foot {{ font-size:10px; fill:{palette["muted_ink"]}; }}
.change-add {{ font-size:11px; font-weight:800; fill:{palette["added"]}; }}
.change-mod {{ font-size:11px; font-weight:800; fill:{palette["modified"]}; }}
.change-del {{ font-size:11px; font-weight:800; fill:{palette["deleted"]}; }}
</style>
''')
    out.append(f'<rect width="100%" height="100%" fill="{palette["background"]}"/>')
    out.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" rx="18" fill="{palette["card"]}" stroke="#DDE3EA"/>')
    out.append(svg_text(30, 54, cfg.get("title", "Policy suite currency profile"), "title"))
    out.append(f'<rect x="30" y="70" width="190" height="31" rx="15.5" fill="#357DA8"/>')
    out.append(svg_text(125, 91, cfg.get("view_label", "Fiscal Q2 change view"), "badge", "middle"))
    out.append(svg_text(238, 91, f'Baseline: {cfg["baseline_date"]}  ·  Current snapshot: {cfg["current_date"]}', "subtitle"))
    if logo_uri: out.append(f'<image href="{logo_uri}" x="{W-135}" y="24" width="102" height="102" preserveAspectRatio="xMidYMid meet"/>')
    # Keep contextual events readable as their count grows: two compact columns.
    event_box_x = x_age + 20; event_box_y = 18; event_box_w = 520; event_box_h = 112
    out.append(f'<rect x="{event_box_x}" y="{event_box_y}" width="{event_box_w}" height="{event_box_h}" rx="12" fill="#FBFCFE" stroke="#DCE3EA"/>')
    out.append(svg_text(event_box_x + 14, event_box_y + 19, "Context events (vertical lines on age chart)", "legend-title"))
    event_columns = 2
    rows_per_column = max(1, (len(events) + event_columns - 1) // event_columns)
    column_width = 250
    for i, ev in enumerate(events):
        column = i // rows_per_column
        row = i % rows_per_column
        xx = event_box_x + 17 + column * column_width
        yy = event_box_y + 42 + row * 22
        c = ev.get("color") or event_colors[i % len(event_colors)]
        out.append(f'<circle cx="{xx}" cy="{yy-4}" r="9" fill="{c}"/>')
        out.append(svg_text(xx, yy, str(i+1), "badge", "middle"))
        out.append(svg_text(xx + 20, yy, f'{ev.get("display_date", ev["date"])} — {ev["label"]}', "legend"))
    bin_box_x = x_dist + 34; bin_box_y = 18; bin_box_w = 242; bin_box_h = 128
    out.append(f'<rect x="{bin_box_x}" y="{bin_box_y}" width="{bin_box_w}" height="{bin_box_h}" rx="12" fill="#FBFCFE" stroke="#DCE3EA"/>')
    out.append(svg_text(bin_box_x + 14, bin_box_y + 19, "Age (current version) bins", "legend-title"))
    for i, b in enumerate(bins):
        yy = bin_box_y + 40 + i * 19
        out.append(f'<rect x="{bin_box_x+15}" y="{yy-10}" width="15" height="15" rx="3" fill="{current_bins[i]}"/>')
        out.append(svg_text(bin_box_x + 41, yy + 1, str(b["label"]), "legend"))
    panel_y = header_h; panel_h = H - panel_y - 28
    for x, w in ((x_topic, topic_w), (x_age, age_w), (x_dist, dist_w)):
        out.append(f'<rect x="{x}" y="{panel_y}" width="{w}" height="{panel_h}" rx="10" fill="white" stroke="#DCE3EA"/>')
    out.append(svg_text(x_topic + 12, header_h + 25, "Policy topic", "section"))
    out.append(svg_text(row_x + 120, header_h + 25, "Changes", "section", "middle"))
    ly = header_h + 47; cx = row_x + 20
    for label, color in (("Added", palette["added"]), ("Modified", palette["modified"]), ("Deleted", palette["deleted"])):
        out.append(f'<circle cx="{cx}" cy="{ly-4}" r="5.5" fill="{color}"/>'); out.append(svg_text(cx + 10, ly, label, "subsection")); cx += 72
    out.append(svg_text(current_num_x, header_h + 25, "Current", "section", "end")); out.append(svg_text(current_num_x, header_h + 43, "instruments", "subsection", "end"))
    out.append(svg_text(x_age + 14, header_h + 25, "Average current-version age", "section"))
    out.append(svg_text(x_dist + 14, header_h + 25, "Age distribution of current versions", "section"))
    axis_y = table_y - 10
    out.append(f'<line x1="{age_plot_x0}" y1="{axis_y}" x2="{age_plot_x1}" y2="{axis_y}" stroke="{palette["grid"]}" stroke-width="1"/>')
    for t in [0, 5, 10, 15]:
        x = age_x(t); out.append(f'<line x1="{x}" y1="{axis_y-5}" x2="{x}" y2="{table_y+table_h}" stroke="{palette["grid"]}" stroke-width="1"/>'); out.append(svg_text(x, axis_y - 9, f"{t}y", "axis", "middle"))
    for i, ev in enumerate(events):
        x = age_x(years_between(cfg["current_date_obj"], parse_date(ev["date"]))); c = ev.get("color") or event_colors[i % len(event_colors)]
        out.append(f'<line x1="{x}" y1="{axis_y}" x2="{x}" y2="{table_y+table_h}" stroke="{c}" stroke-width="1.3" stroke-dasharray="5 4" opacity="0.85"/>')
        out.append(f'<circle cx="{x}" cy="{axis_y}" r="9" fill="{c}" stroke="white" stroke-width="1.4"/>')
        out.append(svg_text(x, axis_y + 3.5, str(i+1), "badge", "middle"))
    colw = dist_plot_w / len(bins)
    for i, b in enumerate(bins):
        out.append(svg_text(dist_x0 + colw*(i+0.5), axis_y - 9, str(b["label"]), "axis", "middle"))
    for idx, topic in enumerate(topics):
        group_top = table_y + idx * row_pair_h; base_y = group_top + 21; cur_y = group_top + 48
        name = topic["name"]; label_y = group_top + 35
        if len(name) > 30 and " / " in name:
            a,b = name.split(" / ", 1); out.append(svg_text(x_topic + 12, label_y - 6, a + " /", "topic")); out.append(svg_text(x_topic + 12, label_y + 10, b, "topic"))
        elif len(name) > 31 and " & " in name:
            a,b = name.split(" & ", 1); out.append(svg_text(x_topic + 12, label_y - 6, a + " &", "topic")); out.append(svg_text(x_topic + 12, label_y + 10, b, "topic"))
        else:
            out.append(svg_text(x_topic + 12, label_y + 2, name, "topic"))
        out.append(f'<rect x="{row_x}" y="{group_top+2}" width="{topic_w-topic_name_w-4}" height="27" rx="4" fill="{palette["row_baseline"]}"/>')
        out.append(f'<rect x="{row_x}" y="{group_top+31}" width="{topic_w-topic_name_w-4}" height="29" rx="4" fill="{palette["row_current"]}"/>')
        out.append(svg_text(row_x + 10, base_y, "Jul 1", "base")); out.append(svg_text(current_num_x, base_y, str(topic["baseline"]["count"]), "metric", "end"))
        out.append(svg_text(row_x + 10, cur_y, "Current", "current"))
        out.append(svg_text(changes_start_x + 0, cur_y, str(topic["changes"]["added"]), "change-add"))
        out.append(svg_text(changes_start_x + 47, cur_y, str(topic["changes"]["modified"]), "change-mod"))
        out.append(svg_text(changes_start_x + 94, cur_y, str(topic["changes"]["deleted"]), "change-del"))
        out.append(svg_text(current_num_x, cur_y, str(topic["current"]["count"]), "current", "end"))
        bx = age_x(topic["baseline"]["avg_age"]); cx2 = age_x(topic["current"]["avg_age"])
        out.append(f'<line x1="{age_plot_x0}" y1="{base_y-5}" x2="{bx}" y2="{base_y-5}" stroke="{palette["baseline_line"]}" stroke-width="1.8"/>'); out.append(f'<circle cx="{bx}" cy="{base_y-5}" r="5.5" fill="{palette["baseline_line"]}"/>'); out.append(svg_text(min(bx+9, age_plot_x1-2), base_y - 1, fmt_age(topic["baseline"]["avg_age"]), "age-base"))
        out.append(f'<line x1="{age_plot_x0}" y1="{cur_y-5}" x2="{cx2}" y2="{cur_y-5}" stroke="{palette["current_line"]}" stroke-width="2.1"/>'); out.append(f'<circle cx="{cx2}" cy="{cur_y-5}" r="6" fill="{palette["current_line"]}"/>'); out.append(svg_text(min(cx2+9, age_plot_x1-2), cur_y - 1, fmt_age(topic["current"]["avg_age"]), "age-current"))
        for snap, yy, colors, opacity in (("baseline", base_y-14, baseline_bins, 0.48), ("current", cur_y-14, current_bins, 1.0)):
            total = topic[snap]["count"]; x = dist_x0
            for bi, n in enumerate(topic[snap]["bins"]):
                w = dist_plot_w * (n / total) if total else 0
                if w <= 0: continue
                out.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{w:.1f}" height="22" fill="{colors[bi]}" opacity="{opacity}"/>')
                if w >= 34:
                    label = f"{n} · {fmt_pct(n, total)}" if w >= 64 else str(n); fill = "#3A3200" if bi == 2 else "#FFFFFF"; out.append(svg_text(x + w/2, yy + 15, label, "bintext", "middle", fill=fill))
                x += w
            out.append(f'<rect x="{dist_x0}" y="{yy}" width="{dist_plot_w}" height="22" fill="none" stroke="#E2E6EA"/>')
        if idx < len(topics)-1:
            sy = group_top + row_pair_h; out.append(f'<line x1="{x_topic+8}" y1="{sy}" x2="{W-margin-8}" y2="{sy}" stroke="#E6EBF0" stroke-width="1"/>')
    fy = table_y + table_h + 24
    out.append(svg_text(30, fy, "Muted upper sub-row = start-of-quarter baseline. Saturated lower sub-row = current snapshot.", "foot"))
    out.append(svg_text(30, fy + 17, "Quarter changes: green = added, yellow = modified, red = deleted. Context lines situate policy age and do not imply causation.", "foot"))
    out.append('</svg>')
    return ''.join(out)

PROFILE_START = "<!-- policy-hawk:currency-profile:start -->"
PROFILE_END = "<!-- policy-hawk:currency-profile:end -->"


def currency_profile_section(cfg, image_path: str) -> str:
    return f"""{PROFILE_START}\n## Policy suite currency profile\n\nThis quarter-level view tracks the **currency and change profile of the policy suite as a whole**. It is intentionally kept separate from the instrument-by-instrument analyses below.\n\n![Policy suite currency profile]({image_path})\n\n- **Muted upper rows** show the start-of-quarter baseline ({cfg['baseline_date']}).\n- **Saturated lower rows** show the current snapshot ({cfg['current_date']}).\n- Quarter-to-date changes are shown as **added** (green), **modified** (yellow), and **deleted** (red) instruments.\n- The lollipop chart compares average current-version age at the baseline and current snapshot.\n- The distribution strips group current-version ages into `<12 months`, `1–3 years`, `3–5 years`, `5–10 years`, and `10+ years`.\n- Vertical reference lines provide historical context only; they do **not** imply causation.\n\n{PROFILE_END}"""


def update_quarterly_report(report_path: Path, cfg, image_path: str) -> None:
    section = currency_profile_section(cfg, image_path)
    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
    else:
        text = ""

    if PROFILE_START in text and PROFILE_END in text:
        start = text.index(PROFILE_START)
        end = text.index(PROFILE_END) + len(PROFILE_END)
        text = text[:start] + section + text[end:]
    else:
        # Keep the overview beside the heatmap and ahead of detailed dated entries.
        heatmap_marker = "<!-- policy-hawk:latest-heatmap -->"
        if heatmap_marker in text:
            marker_pos = text.index(heatmap_marker)
            rule_pos = text.find("\n---", marker_pos)
            if rule_pos != -1:
                text = text[:rule_pos] + "\n\n" + section + "\n" + text[rule_pos:]
            else:
                text = text + "\n\n" + section + "\n"
        elif text:
            first_rule = text.find("\n---")
            if first_rule != -1:
                text = text[:first_rule] + "\n\n" + section + "\n" + text[first_rule:]
            else:
                text = text.rstrip() + "\n\n" + section + "\n"
        else:
            text = section + "\n"

    report_path.write_text(text.rstrip() + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--logo", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None, help="Optional quarterly Markdown report to insert/update")
    parser.add_argument("--image-path", default=None, help="Markdown image path; defaults to the output path")
    args = parser.parse_args()
    cfg = json.loads(args.input.read_text(encoding="utf-8"))
    svg = render_svg(cfg, load_logo_data_uri(args.logo))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    if args.report:
        image_path = args.image_path or args.output.as_posix()
        update_quarterly_report(args.report, cfg, image_path)
if __name__ == "__main__":
    main()
