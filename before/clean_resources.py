"""Synthetic community resource cleanup. Standard library only; no network calls."""
import csv
import sys
from urllib.parse import urlsplit

def clean(source, destination):
    rows, seen = [], set()
    with open(source, newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = {key: " ".join((raw.get(key) or "").split()) for key in
                   ("name", "url", "category", "description")}
            parts = urlsplit(row["url"])
            if not row["name"] or parts.scheme not in ("https", "http") or not parts.netloc:
                continue
            if row["url"] in seen:
                continue
            seen.add(row["url"])
            row["category"] = row["category"].title() or "Uncategorized"
            rows.append(row)
    rows.sort(key=lambda row: (row["category"].casefold(), row["name"].casefold()))
    with open(destination, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "url", "category", "description"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} useful resources")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 clean_resources.py INPUT.csv OUTPUT.csv")
    clean(sys.argv[1], sys.argv[2])
