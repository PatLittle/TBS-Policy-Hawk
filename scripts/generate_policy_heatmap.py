#!/usr/bin/env python3

import argparse
import csv
import io
import re
from collections import Counter
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.request import Request, urlopen


README_HEATMAP_MARKER = "<!-- policy-hawk:latest-heatmap -->"
README_DATASETS_HEADING = "## Main Datasets"
VALID_DATE_COLUMNS = {"pubDate", "updated_date"}
IMAGE_SOFTWARE = "TBS-Policy-Hawk (github.com/PatLittle/TBS-Policy-Hawk)"
IMAGE_COPYRIGHT = "© Pat Little, 2026"
IMAGE_COPYRIGHT_EXIF = "(c) Pat Little, 2026"
IMAGE_SUBJECT_LOCATION = "90 Elgin St, Ottawa, ON"
DEFAULT_LOGO = Path("assets/tbs-policy-hawk-logo-100px-transparent.png")
INSTRUMENT_COLORS = {
    "Directive": "#0969da",
    "Policy": "#8250df",
    "Standard": "#bf8700",
    "Guideline": "#1a7f37",
    "Guidelines": "#1f883d",
    "Guide": "#0a7f80",
    "Policy framework": "#bf3989",
    "Mandatory Procedure": "#d1242f",
    "Hierarchy": "#57606a",
}
FALLBACK_INSTRUMENT_COLORS = (
    "#1f883d",
    "#bf3989",
    "#9a6700",
    "#0550ae",
    "#bc4c00",
)


def current_gc_fiscal_quarter(today: Optional[date] = None) -> Tuple[date, date]:
    """Return inclusive bounds for the current Government of Canada fiscal quarter."""
    today = today or date.today()
    if 4 <= today.month <= 6:
        return date(today.year, 4, 1), date(today.year, 6, 30)
    if 7 <= today.month <= 9:
        return date(today.year, 7, 1), date(today.year, 9, 30)
    if 10 <= today.month <= 12:
        return date(today.year, 10, 1), date(today.year, 12, 31)
    return date(today.year, 1, 1), date(today.year, 3, 31)


def completed_gc_fiscal_quarters(
    today: Optional[date] = None,
    first_fiscal_year: int = 2026,
) -> List[Tuple[str, date, date]]:
    """Return completed fiscal quarters beginning with 2026-27 Q1."""
    today = today or date.today()
    completed = []
    fiscal_year = first_fiscal_year

    while True:
        quarter_bounds = (
            (
                f"{fiscal_year}-{str(fiscal_year + 1)[-2:]}Q1",
                date(fiscal_year, 4, 1),
                date(fiscal_year, 6, 30),
            ),
            (
                f"{fiscal_year}-{str(fiscal_year + 1)[-2:]}Q2",
                date(fiscal_year, 7, 1),
                date(fiscal_year, 9, 30),
            ),
            (
                f"{fiscal_year}-{str(fiscal_year + 1)[-2:]}Q3",
                date(fiscal_year, 10, 1),
                date(fiscal_year, 12, 31),
            ),
            (
                f"{fiscal_year}-{str(fiscal_year + 1)[-2:]}Q4",
                date(fiscal_year + 1, 1, 1),
                date(fiscal_year + 1, 3, 31),
            ),
        )
        for label, start, end in quarter_bounds:
            if end >= today:
                return completed
            completed.append((label, start, end))
        fiscal_year += 1


def gc_fiscal_quarters_to_date(
    today: Optional[date] = None,
    first_fiscal_year: int = 2026,
) -> List[Tuple[str, date, date]]:
    """Return completed quarters plus the current quarter with a TD suffix."""
    today = today or date.today()
    quarters = completed_gc_fiscal_quarters(today, first_fiscal_year)
    current_start, current_end = current_gc_fiscal_quarter(today)
    first_start = date(first_fiscal_year, 4, 1)
    if current_start < first_start:
        return quarters

    if current_start.month == 1:
        fiscal_year = current_start.year - 1
        quarter_number = 4
    else:
        fiscal_year = current_start.year
        quarter_number = {
            4: 1,
            7: 2,
            10: 3,
        }[current_start.month]
    label = (
        f"{fiscal_year}-{str(fiscal_year + 1)[-2:]}"
        f"Q{quarter_number}TD"
    )
    quarters.append((label, current_start, min(current_end, today)))
    return quarters


def resolve_dates(
    start: Optional[str],
    end: Optional[str],
    today: Optional[date] = None,
) -> Tuple[date, date]:
    if start is None and end is None:
        return current_gc_fiscal_quarter(today)
    if start is None or end is None:
        raise ValueError("Set both --start and --end, or omit both.")
    resolved_start = date.fromisoformat(start)
    resolved_end = date.fromisoformat(end)
    if resolved_start > resolved_end:
        raise ValueError("--start must be on or before --end.")
    return resolved_start, resolved_end


def read_csv(source: str) -> str:
    if source.startswith(("https://", "http://")):
        request = Request(
            source,
            headers={"User-Agent": "TBS-Policy-Hawk-heatmap/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8-sig")
    return Path(source).read_text(encoding="utf-8-sig")


def row_date(row: Dict[str, str], column: str) -> date:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"Missing value for date column {column!r}.")
    if column == "pubDate":
        return parsedate_to_datetime(value).date()
    if column == "updated_date":
        return datetime.fromisoformat(value).date()
    raise ValueError(f"Unsupported date column: {column}")


def collect_activity_counts(
    csv_text: str,
    start: date,
    end: date,
    column: str,
) -> Tuple[Counter, Counter]:
    if column not in VALID_DATE_COLUMNS:
        raise ValueError(f"Date column must be one of {sorted(VALID_DATE_COLUMNS)}.")

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or column not in reader.fieldnames:
        raise ValueError(f"CSV does not contain the requested date column {column!r}.")

    counts = Counter()
    instrument_counts = Counter()
    for row_number, row in enumerate(reader, start=2):
        try:
            current = row_date(row, column)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid {column} value on CSV row {row_number}: {exc}") from exc
        if start <= current <= end:
            counts[current] += 1
            instrument_type = (row.get("category") or "Unspecified").strip()
            instrument_counts[instrument_type or "Unspecified"] += 1
    return counts, instrument_counts


def collect_counts(
    csv_text: str,
    start: date,
    end: date,
    column: str,
) -> Counter:
    """Return daily counts while preserving the original public helper API."""
    counts, _ = collect_activity_counts(csv_text, start, end, column)
    return counts


def collect_completed_quarter_instrument_counts(
    csv_text: str,
    column: str,
    today: Optional[date] = None,
) -> List[Tuple[str, Counter]]:
    """Return instrument-type counts for every completed quarter since 2026-27."""
    completed_counts = []
    for label, start, end in completed_gc_fiscal_quarters(today):
        _, instrument_counts = collect_activity_counts(csv_text, start, end, column)
        completed_counts.append((label, instrument_counts))
    return completed_counts


def collect_quarter_instrument_counts(
    csv_text: str,
    column: str,
    today: Optional[date] = None,
) -> List[Tuple[str, Counter]]:
    """Return instrument counts for completed and current-to-date quarters."""
    today = today or date.today()
    quarter_counts = []
    for label, start, end in gc_fiscal_quarters_to_date(today):
        _, instrument_counts = collect_activity_counts(csv_text, start, end, column)
        quarter_counts.append((label, instrument_counts))
    return quarter_counts


def month_starts(start: date, end: date) -> Iterable[date]:
    current = start.replace(day=1)
    while current <= end:
        yield current
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )


def display_date(value: date) -> str:
    return f"{value:%B} {value.day}, {value.year}"


def pie_value_label(percentage: float, total: int) -> str:
    """Convert a pie-slice percentage back to its whole-number count."""
    value = int(round(percentage * total / 100))
    return str(value) if value else ""


def heatmap_filename(start: date, end: date) -> str:
    return f"tbs_policy_hawk_heatmap_{start.isoformat()}_to_{end.isoformat()}.png"


def embed_image_metadata(output: Path) -> None:
    """Embed standards-compatible EXIF and exact Unicode PNG metadata."""
    from PIL import Image, PngImagePlugin

    png_metadata = PngImagePlugin.PngInfo()
    png_metadata.add_itxt("Software", IMAGE_SOFTWARE)
    png_metadata.add_itxt("Copyright", IMAGE_COPYRIGHT)
    png_metadata.add_itxt("SubjectLocation", IMAGE_SUBJECT_LOCATION)

    exif = Image.Exif()
    exif[305] = IMAGE_SOFTWARE  # Software
    # EXIF's Copyright field is ASCII-only, so use an ASCII-compatible form.
    exif[33432] = IMAGE_COPYRIGHT_EXIF  # Copyright
    # EXIF SubjectLocation (41492) requires pixel coordinates, not an address.
    # Preserve the requested address and Unicode copyright in UserComment.
    exif_comment = (
        f"Copyright: {IMAGE_COPYRIGHT}\n"
        f"SubjectLocation: {IMAGE_SUBJECT_LOCATION}"
    )
    exif[37510] = b"UNICODE\0" + exif_comment.encode("utf-16-be")  # UserComment

    with Image.open(output) as source:
        source.load()
        image = source.copy()
        save_options = {
            "pnginfo": png_metadata,
            "exif": exif,
        }
        if "dpi" in source.info:
            save_options["dpi"] = source.info["dpi"]
        if "icc_profile" in source.info:
            save_options["icc_profile"] = source.info["icc_profile"]

    image.save(output, format="PNG", **save_options)


def draw_heatmap(
    counts: Counter,
    quarter_instrument_counts: List[Tuple[str, Counter]],
    start: date,
    end: date,
    date_column: str,
    output: Path,
    logo_path: Path = DEFAULT_LOGO,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import FancyBboxPatch

    months = list(month_starts(start, end))
    month_count = len(months)
    group_height = 3.15
    pie_column_count = max(1, (len(quarter_instrument_counts) + 3) // 4)
    extra_width = (pie_column_count - 1) * 0.95

    fig_height = max(5.2, 2.4 + month_count * 1.55)
    fig_width = 13.5 + extra_width
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=150, facecolor="#ffffff")
    main_left = 2.70 + extra_width
    ax = fig.add_axes([main_left / fig_width, 0.17, 9.99 / fig_width, 0.67])
    ax.set_xlim(-1.75, 15.65)
    ax.set_ylim(month_count * group_height - 0.45, -1.0)
    ax.set_aspect("equal")
    ax.axis("off")

    colors = ["#ebedf0", "#9be9a8", "#40c463", "#216e39"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, float("inf")], cmap.N)

    for month_index, month_start in enumerate(months):
        y_base = month_index * group_height
        ax.text(
            -0.42,
            y_base - 0.52,
            month_start.strftime("%B %Y"),
            ha="left",
            va="bottom",
            fontsize=11,
            fontweight="semibold",
            color="#24292f",
        )

        if month_index > 0:
            divider_y = y_base - 0.95
            ax.plot(
                [-0.42, 15.5],
                [divider_y, divider_y],
                color="#8c959f",
                linewidth=1.1,
                zorder=5,
            )

        for day_number in range(1, 33):
            try:
                current = date(month_start.year, month_start.month, day_number)
            except ValueError:
                current = None

            row = 0 if day_number <= 16 else 1
            column = day_number - 1 if row == 0 else day_number - 17
            y = y_base + row
            in_range = current is not None and start <= current <= end
            value = counts[current] if in_range else 0
            face = cmap(norm(value)) if in_range else "#f6f8fa"
            edge = (
                "#d0d7de"
                if in_range and value == 0
                else (face if in_range else "#e4e7eb")
            )

            ax.add_patch(
                FancyBboxPatch(
                    (column - 0.42, y - 0.42),
                    0.84,
                    0.84,
                    boxstyle="round,pad=0.02,rounding_size=0.10",
                    facecolor=face,
                    edgecolor=edge,
                    linewidth=0.7,
                )
            )

            if current is not None:
                ax.text(
                    column - 0.31,
                    y - 0.27,
                    str(day_number),
                    ha="left",
                    va="top",
                    fontsize=5.8,
                    color="#8c959f" if value == 0 else "#24292f",
                )
            if in_range:
                ax.text(
                    column,
                    y + 0.06,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#ffffff" if value >= 2 else "#1f2328",
                )

    all_instruments = sorted(
        {
            instrument
            for _, instrument_counts in quarter_instrument_counts
            for instrument in instrument_counts
        }
    )
    unknown_instruments = [
        instrument
        for instrument in all_instruments
        if instrument not in INSTRUMENT_COLORS
    ]
    instrument_color = {
        instrument: INSTRUMENT_COLORS[instrument]
        for instrument in all_instruments
        if instrument in INSTRUMENT_COLORS
    }
    instrument_color.update(
        {
            instrument: FALLBACK_INSTRUMENT_COLORS[
                index % len(FALLBACK_INSTRUMENT_COLORS)
            ]
            for index, instrument in enumerate(unknown_instruments)
        }
    )

    for column_index in range(pie_column_count):
        column_quarters = quarter_instrument_counts[
            column_index * 4 : (column_index + 1) * 4
        ]
        if not column_quarters:
            continue
        row_count = len(column_quarters)
        if row_count == 1:
            row_positions = [0.50]
        elif row_count == 2:
            row_positions = [0.52, 0.32]
        elif row_count == 3:
            row_positions = [0.59, 0.39, 0.19]
        else:
            row_positions = [0.62, 0.47, 0.32, 0.17]

        for row_position, (quarter_label, instrument_counts) in zip(
            row_positions,
            column_quarters,
        ):
            pie_ax = fig.add_axes(
                [
                    (0.20 + column_index * 0.95) / fig_width,
                    row_position,
                    0.80 / fig_width,
                    0.12,
                ]
            )
            pie_ax.set_aspect("equal")
            pie_ax.axis("off")
            pie_ax.set_title(
                quarter_label,
                fontsize=8,
                fontweight="semibold",
                color="#24292f",
                pad=1,
            )
            if instrument_counts:
                instruments = sorted(
                    instrument_counts,
                    key=lambda name: (-instrument_counts[name], name),
                )
                values = [instrument_counts[name] for name in instruments]
                total = sum(values)
                wedges, _, value_labels = pie_ax.pie(
                    values,
                    colors=[instrument_color[name] for name in instruments],
                    startangle=90,
                    counterclock=False,
                    wedgeprops={"edgecolor": "#ffffff", "linewidth": 1},
                    autopct=lambda percentage, total=total: pie_value_label(
                        percentage,
                        total,
                    ),
                    pctdistance=0.62,
                    textprops={
                        "fontsize": 7,
                        "fontweight": "bold",
                    },
                )
                for wedge, value_label in zip(wedges, value_labels):
                    red, green, blue, _ = wedge.get_facecolor()
                    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                    value_label.set_color(
                        "#24292f" if luminance > 0.62 else "#ffffff"
                    )
            else:
                pie_ax.text(
                    0.5,
                    0.5,
                    "No changes",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#57606a",
                    transform=pie_ax.transAxes,
                )

    if all_instruments:
        from matplotlib.patches import Patch

        fig.legend(
            [
                Patch(
                    facecolor=instrument_color[instrument],
                    edgecolor="none",
                    label=instrument,
                )
                for instrument in all_instruments
            ],
            all_instruments,
            loc="upper left",
            bbox_to_anchor=(0.20 / fig_width, 0.825),
            frameon=False,
            fontsize=7,
            handlelength=0.8,
            handletextpad=0.4,
            labelspacing=0.25,
            ncol=min(2, len(all_instruments)),
        )

    date_label = "publication date" if date_column == "pubDate" else "collection date"
    fig.text(
        0.47 / fig_width,
        0.93,
        "TBS-Policy-Hawk: Tracked Policy Suite Changes in Current FQ.",
        fontsize=19,
        fontweight="bold",
        color="#24292f",
    )
    fig.text(
        0.47 / fig_width,
        0.87,
        f"Policy records by {date_label} · {display_date(start)}–{display_date(end)}",
        fontsize=11.5,
        color="#57606a",
    )

    if not logo_path.is_file():
        raise FileNotFoundError(f"Heatmap logo not found: {logo_path}")
    logo = plt.imread(logo_path)
    logo_ax = fig.add_axes(
        [(fig_width - 1.22) / fig_width, 0.86, 0.88 / fig_width, 0.105]
    )
    logo_ax.imshow(logo)
    logo_ax.axis("off")

    fig.text(
        main_left / fig_width,
        0.075,
        f"{sum(counts.values())} records across {len(counts)} active days",
        fontsize=10.5,
        fontweight="semibold",
        color="#24292f",
    )

    legend_x = (fig_width - 4.05) / fig_width
    fig.text(
        legend_x - 0.055,
        0.075,
        "Less",
        fontsize=9,
        color="#57606a",
        ha="right",
    )
    for index, color in enumerate(colors):
        legend_ax = fig.add_axes([legend_x + index * 0.025, 0.057, 0.019, 0.045])
        legend_ax.add_patch(
            FancyBboxPatch(
                (0.1, 0.1),
                0.8,
                0.8,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor=color,
                edgecolor="#d0d7de" if index == 0 else color,
                linewidth=0.6,
            )
        )
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(0, 1)
        legend_ax.axis("off")
    fig.text(
        legend_x + 0.108,
        0.075,
        "More",
        fontsize=9,
        color="#57606a",
        ha="left",
    )
    fig.text(
        (fig_width - 0.95) / fig_width,
        0.025,
        "Source: PatLittle/TBS-Policy-Hawk · data/items.csv",
        fontsize=8.5,
        color="#6e7781",
        ha="right",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        bbox_inches="tight",
        pad_inches=0.12,
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    embed_image_metadata(output)


def update_readme_heatmap(
    readme_path: Path,
    image_path: str,
    start: date,
    end: date,
) -> None:
    text = readme_path.read_text(encoding="utf-8")
    alt = f"TBS Policy Hawk activity heatmap for {start.isoformat()} to {end.isoformat()}"
    block = f"{README_HEATMAP_MARKER}\n![{alt}]({image_path})"
    marked_block = re.compile(
        rf"{re.escape(README_HEATMAP_MARKER)}\n!\[[^\n]*\]\([^\n]*\)"
    )

    if marked_block.search(text):
        updated = marked_block.sub(block, text, count=1)
    else:
        heading_index = text.find(README_DATASETS_HEADING)
        if heading_index < 0:
            raise ValueError(f"README is missing the {README_DATASETS_HEADING!r} heading.")
        before = text[:heading_index].rstrip()
        after = text[heading_index:].lstrip()
        updated = f"{before}\n\n{block}\n\n{after}"

    readme_path.write_text(updated, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the current fiscal-quarter TBS Policy Hawk activity heatmap."
    )
    parser.add_argument("--source", default="data/items.csv")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument(
        "--date-column",
        choices=sorted(VALID_DATE_COLUMNS),
        default="pubDate",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("screenshots"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument(
        "--logo",
        type=Path,
        default=DEFAULT_LOGO,
        help="Logo image placed in the top-right corner.",
    )
    parser.add_argument(
        "--no-update-readme",
        action="store_true",
        help="Generate the image without changing README.md.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start, end = resolve_dates(args.start, args.end)
    csv_text = read_csv(args.source)
    counts, _ = collect_activity_counts(
        csv_text,
        start,
        end,
        args.date_column,
    )
    quarter_instrument_counts = collect_quarter_instrument_counts(
        csv_text,
        args.date_column,
    )
    output = args.output_dir / heatmap_filename(start, end)

    draw_heatmap(
        counts,
        quarter_instrument_counts,
        start,
        end,
        args.date_column,
        output,
        args.logo,
    )
    if not args.no_update_readme:
        try:
            image_path = output.relative_to(args.readme.parent).as_posix()
        except ValueError:
            image_path = output.as_posix()
        update_readme_heatmap(args.readme, image_path, start, end)

    print(f"Period: {start.isoformat()} to {end.isoformat()}")
    print(f"Records: {sum(counts.values())}; active days: {len(counts)}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
