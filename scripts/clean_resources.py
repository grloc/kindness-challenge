
"""Messy Resource Rescue: turn a messy community list into a newcomer-friendly guide.
Standard library only; no network calls.

Usage: python3 clean_resources.py INPUT.csv OUTPUT.csv
Writes OUTPUT.csv and, next to it, a readable OUTPUT.md guide.
"""
import csv
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Reading order for a newcomer: first the welcome, last the deep dives.
CATEGORY_ORDER = ["Getting Started", "Help & FAQ", "Events", "Tutorials", "Other"]
CATEGORY_LEVEL = {"Getting Started": "Beginner", "Help & FAQ": "Beginner",
                  "Events": "All levels", "Tutorials": "Intermediate", "Other": "All levels"}
# What to do right after clicking: the "kindness" column for a newcomer.
CATEGORY_NEXT_STEP = {"Getting Started": "Start here first (2 min read)",
                      "Help & FAQ": "Check here before asking",
                      "Events": "Join and ask a question together",
                      "Tutorials": "Try this tiny example",
                      "Other": "Take a look when you have a minute"}
CATEGORY_EMOJI = {"Getting Started": "👋", "Help & FAQ": "❓", "Events": "📅",
                  "Tutorials": "🛠️", "Other": "📌"}

# Aliases people actually type -> canonical category.
ALIASES = {"getting started": "Getting Started", "start": "Getting Started", "welcome": "Getting Started",
           "onboarding": "Getting Started", "events": "Events", "event": "Events",
           "tutorials": "Tutorials", "tutorial": "Tutorials", "guides": "Tutorials",
           "faq": "Help & FAQ", "help": "Help & FAQ", "support": "Help & FAQ"}

# Keywords used to guess a category when the cell is empty or unknown.
KEYWORDS = {"Getting Started": ("welcome", "intro", "start", "onboard", "newcomer"),
            "Help & FAQ": ("faq", "question", "answer", "help", "support"),
            "Events": ("office hours", "meetup", "event", "webinar", "workshop", "live"),
            "Tutorials": ("tutorial", "notebook", "example", "walkthrough", "how to", "guide")}

TRACKING = ("utm_", "fbclid", "gclid", "ref")
NOISE = re.compile(r"\b(duplicate resource|missing title|needs a valid link)\b", re.I)

def squash(text):
    return " ".join((text or "").split())

def normalize_url(url):
    """Lowercase host, drop fragment, tracking params and trailing slash."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc or " " in url:
        return None
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith(TRACKING)]
    path = parts.path.rstrip("/") or ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))

def pick_category(raw_category, name, description):
    known = ALIASES.get(squash(raw_category).casefold())
    if known:
        return known
    text = f"{name} {description}".casefold()
    for category, words in KEYWORDS.items():
        if any(word in text for word in words):
            return category
    return "Other"

def tidy_name(name):
    # Keep deliberate capitals (FAQ, API) but make "welcome guide" look like a title.
    return name if any(c.isupper() for c in name[1:]) else name.title()

def tidy_description(text):
    text = squash(NOISE.sub("", text)).strip(" .")
    return (text[0].upper() + text[1:] + ".") if text else ""

def clean(source, destination):
    rows, seen_urls, seen_names, dropped = [], set(), set(), []
    with open(source, newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            name, description = squash(raw.get("name")), squash(raw.get("description"))
            url = normalize_url(squash(raw.get("url")))
            label = name or "(blank title)"
            if not name:
                dropped.append((label, "missing title")); continue
            if not url:
                dropped.append((label, "broken link")); continue
            if url in seen_urls or name.casefold() in seen_names:
                dropped.append((label, "duplicate")); continue
            seen_urls.add(url); seen_names.add(name.casefold())
            category = pick_category(raw.get("category"), name, description)
            rows.append({"name": tidy_name(name), "url": url, "category": category,
                         "level": CATEGORY_LEVEL[category],
                         "next_step": CATEGORY_NEXT_STEP[category],
                         "description": tidy_description(description)})
    rows.sort(key=lambda r: (CATEGORY_ORDER.index(r["category"]), r["name"].casefold()))
    for number, row in enumerate(rows, 1):
        row["order"] = number  # suggested reading order

    fields = ["order", "name", "url", "category", "level", "next_step", "description"]
    with open(destination, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

    lines = ["# Community resources: start here 💚", ""]
    for category in CATEGORY_ORDER:
        group = [r for r in rows if r["category"] == category]
        if group:
            lines += [f"## {CATEGORY_EMOJI[category]} {category}", ""]
            lines += [f"{r['order']}. [{r['name']}]({r['url']}) ({r['level']}): {r['description']} **Next:** {r['next_step']}." for r in group]
            lines.append("")
    Path(destination).with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Kept {len(rows)} useful resources")
    for label, reason in dropped:
        print(f"  dropped: {label} ({reason})")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 clean_resources.py INPUT.csv OUTPUT.csv")
    clean(sys.argv[1], sys.argv[2])
    # FIX CRLF pour GMI : \r\n et pas de \n a la fin
import sys
try:
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'cleaned_resources.csv'
    with open(out_path, 'rb') as _f:
        _data = _f.read()
    _text = _data.decode().replace('\r\n', '\n').replace('\r', '\n')
    _lines = _text.splitlines()
    _fixed = '\r\n'.join(_lines)
    with open(out_path, 'wb') as _f:
        _f.write(_fixed.encode())
except Exception as _e:
    print('Fix CRLF ignore:', _e)
