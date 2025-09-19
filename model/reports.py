from pathlib import Path
from typing import Any

def write_miss_report(
        output_root: Path, 
        job_code: int | str,
        misses: dict[str, dict[str, list[str]]],
        failed_paths: list[str] | None = None,
):

    failed_paths = failed_paths or []
    lines: list[str] = []
    lines.append("=== JobScan Miss Report ===")
    lines.append(f"Job: {job_code}")
    lines.append(f"Output: {output_root.resolve()}")
    lines.append("")

    def section(title: str):
        lines.append(title)
        lines.append("-" * len(title))
        lines.append("")

    section("By Category / Type (Not Found)")

    for cat in ("nc", "dxf", "pdf"):
        cat_misses = misses.get(cat, {})
        for subcat in ("mainmark", "part"):
            items = sorted(set(cat_misses.get(subcat, [])))
            label = f"{cat} {subcat.capitalize()}"
            if items:
                lines.append(f"{label}:")
                for item in items:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{label}: (none)")
            lines.append("")

    section("Failed Copies")
    if failed_paths:
        for path in failed_paths:
            lines.append(f"- {path}")
    else:
        lines.append("All files Copied Successfully")

    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "JobScan_Miss_Report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
