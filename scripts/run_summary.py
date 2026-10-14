"""Markdown summary of the latest run for the GitHub Actions job page."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    try:
        run = json.loads((ROOT / "data" / "run.json").read_text())
        brief = json.loads((ROOT / "data" / "brief.json").read_text())
    except (OSError, ValueError):
        print("### Gear deals\nNo run data was produced.")
        return
    counts = run.get("counts", {})
    print("### Gear deals")
    print(f"Data from {run.get('generated_at')}: {counts.get('collected', 0)} listings collected, {counts.get('published', 0)} published, {counts.get('new', 0)} new.\n")
    print("| Store | Status | Listings | Notes |\n|---|---|---|---|")
    for report in run.get("reports", []):
        notes = report.get("error") or "; ".join(report.get("notes") or [])
        print(f"| {report['name']} | {report['status']} | {report['offers']} | {notes[:140]} |")
    print(f"\nBrief: {(brief.get('house', {}).get('ski') or {}).get('headline', 'none')}")


if __name__ == "__main__":
    main()
