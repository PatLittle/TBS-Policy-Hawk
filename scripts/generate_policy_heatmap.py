#!/usr/bin/env python3

import argparse
import csv
import io
import re
from collections import Counter
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.request import Request, urlopen


README_HEATMAP_MARKER = "<!-- policy-hawk:latest-heatmap -->"
README_DATASETS_HEADING = "## Main Datasets"
VALID_DATE_COLUMNS = {"pubDate", "updated_date"}
IMAGE_SOFTWARE = "TBS-Policy-Hawk (github.com/PatLittle/TBS-Policy-Hawk)"
IMAGE_COPYRIGHT = "© Pat Little, 2026"
IMAGE_COPYRIGHT_EXIF = "(c) Pat Little, 2026"
IMAGE_SUBJECT_LOCATION = "90 Elgin St, Ottawa, ON"


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


def collect_counts(
    csv_text: str,
    start: date,
    end: date,
    column: str,
) -> Counter:
    if column not in VALID_DATE_COLUMNS:
        raise ValueError(f"Date column must be one of {sorted(VALID_DATE_COLUMNS)}.")

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or column not in reader.fieldnames:
        raise ValueError(f"CSV does not contain the requested date column {column!r}.")

    counts = Counter()
    for row_number, row in enumerate(reader, start=2):
        try:
            current = row_date(row, column)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid {column} value on CSV row {row_number}: {exc}") from exc
        if start <= current <= end:
            counts[current] += 1
    return counts


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
    start: date,
    end: date,
    date_column: str,
    output: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import FancyBboxPatch

    months = list(month_starts(start, end))
    month_count = len(months)
    group_height = 3.15

    fig_height = max(5.2, 2.4 + month_count * 1.55)
    fig = plt.figure(figsize=(13.5, fig_height), dpi=150, facecolor="#ffffff")
    ax = fig.add_axes([0.12, 0.17, 0.81, 0.67])
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
            -1.65,
            y_base + 0.5,
            month_start.strftime("%B %Y"),
            ha="left",
            va="center",
            fontsize=11,
            fontweight="semibold",
            color="#24292f",
        )

        if month_index > 0:
            divider_y = y_base - 0.62
            ax.plot(
                [-1.65, 15.5],
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

    date_label = "publication date" if date_column == "pubDate" else "collection date"
    fig.text(
        0.09,
        0.93,
        "TBS Policy Hawk activity",
        fontsize=22,
        fontweight="bold",
        color="#24292f",
    )
    fig.text(
        0.09,
        0.87,
        f"Policy records by {date_label} · {display_date(start)}–{display_date(end)}",
        fontsize=11.5,
        color="#57606a",
    )
    fig.text(
        0.09,
        0.075,
        f"{sum(counts.values())} records across {len(counts)} active days",
        fontsize=10.5,
        fontweight="semibold",
        color="#24292f",
    )

    legend_x = 0.70
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
        0.93,
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
        "--no-update-readme",
        action="store_true",
        help="Generate the image without changing README.md.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start, end = resolve_dates(args.start, args.end)
    csv_text = read_csv(args.source)
    counts = collect_counts(csv_text, start, end, args.date_column)
    output = args.output_dir / heatmap_filename(start, end)

    draw_heatmap(counts, start, end, args.date_column, output)
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
