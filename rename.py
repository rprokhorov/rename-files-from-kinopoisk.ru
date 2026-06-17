#!/usr/bin/env python3
"""Rename movie files into a tidy, consistent format using the Kinopoisk API.

For every file in the source directory the script queries kinopoisk.ru (via the
unofficial API at https://kinopoiskapiunofficial.tech), shows up to a handful of
matches and lets you pick one. The chosen file is renamed/moved using a
configurable template (default: "Russian Name (English Name) Year").

Usage:
    export KINOPOISK_API_KEY="your-key"             # get one at the URL above
    python3 rename.py /path/to/movies               # rename in place
    python3 rename.py /path/to/movies -o /sorted    # move renamed files elsewhere
    python3 rename.py /path/to/movies --dry-run     # show what would happen only
    python3 rename.py /path/to/movies -p "{rus} {year}"   # custom name pattern
"""

import argparse
import os
import re
import sys
from pathlib import Path

import requests

API_BASE = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
# Extensions we treat as video files worth renaming.
VIDEO_EXTENSIONS = {
    ".mkv", ".avi", ".mp4", ".m4v", ".mov", ".wmv",
    ".flv", ".mpg", ".mpeg", ".ts", ".webm",
}
# Characters that are illegal in file names on common file systems.
ILLEGAL_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MAX_RESULTS = 6

# Default naming template. Available placeholders: {rus} {eng} {year}
# {duration} {ext}. Groups wrapped in ( ), [ ] or { } that end up empty
# (e.g. a film with no English title) are dropped automatically.
DEFAULT_PATTERN = "{rus} ({eng}) {year}"
PLACEHOLDERS = ("rus", "eng", "year", "duration", "ext")


def get_api_key() -> str:
    key = os.environ.get("KINOPOISK_API_KEY")
    if not key:
        sys.exit(
            "Error: set the KINOPOISK_API_KEY environment variable.\n"
            "Get a free key at https://kinopoiskapiunofficial.tech/"
        )
    return key


def sanitize(name: str) -> str:
    """Make a string safe to use as (part of) a file name."""
    cleaned = ILLEGAL_FS_CHARS.sub("", name)
    # Collapse whitespace and trim trailing dots/spaces (problematic on Windows).
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return cleaned


def search(keyword: str, api_key: str) -> list[dict]:
    """Return a list of candidate films for the given search keyword."""
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    try:
        response = requests.get(
            API_BASE,
            headers=headers,
            params={"keyword": keyword, "page": 1},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  Request failed: {exc}")
        return []
    return response.json().get("films", [])[:MAX_RESULTS]


def build_name(film: dict, extension: str, pattern: str) -> str:
    """Render `pattern` for one API film record into a target file name.

    Placeholders that resolve to an empty value, and any ( ), [ ] or { }
    group left empty as a result, are stripped so the name stays clean.
    """
    year = (film.get("year") or "").strip()
    rus = sanitize(film.get("nameRu") or "")
    eng = sanitize(film.get("nameEn") or film.get("nameOriginal") or "")
    # Don't repeat the same title twice when Russian and English match.
    if eng and eng.lower() == rus.lower():
        eng = ""

    values = {
        "rus": rus,
        "eng": eng,
        "year": "" if year in ("", "null") else year,
        "duration": (film.get("filmLength") or "").strip(),
        "ext": extension.lstrip("."),
    }

    # Drop bracketed groups whose placeholders are all empty, e.g. "(  )".
    def drop_empty_group(match: re.Match) -> str:
        return match.group(0) if match.group("body").format(**values).strip() else ""

    result = re.sub(
        r"[(\[{](?P<body>[^()\[\]{}]*)[)\]}]", drop_empty_group, pattern
    )
    result = result.format(**values)
    # Tidy up whitespace and leftover empty brackets/separators.
    result = re.sub(r"[(\[{]\s*[)\]}]", "", result)
    result = re.sub(r"\s+", " ", result).strip(" -.,")

    return f"{result or 'Unknown'}{extension}"


def prompt_choice(count: int) -> str:
    return input(
        f"Rename (1-{count}). Skip (n). Edit search term (e): "
    ).strip().lower()


def process_file(
    file_path: Path, out_dir: Path, api_key: str, pattern: str, dry_run: bool
) -> None:
    keyword = file_path.stem
    while True:
        print(f"\n[F] {file_path.name}")
        films = search(keyword, api_key)

        if not films:
            print("  No matches found.")
        else:
            for index, film in enumerate(films, start=1):
                print(f"  [{index}] {build_name(film, file_path.suffix, pattern)}")

        answer = prompt_choice(len(films))

        if answer == "n" or answer == "":
            print("  Skipped.")
            return
        if answer == "e":
            new_keyword = input("  New search term: ").strip()
            if new_keyword:
                keyword = new_keyword
            continue
        if answer.isdigit() and 1 <= int(answer) <= len(films):
            new_name = build_name(films[int(answer) - 1], file_path.suffix, pattern)
            destination = out_dir / new_name
            if dry_run:
                print(f"  [dry-run] {file_path.name} -> {destination}")
            elif destination.exists():
                print(f"  Skipped: '{destination}' already exists.")
            else:
                file_path.rename(destination)
                print(f"  Renamed -> {destination}")
            return
        print("  Invalid choice, try again.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename movie files using data from kinopoisk.ru."
    )
    parser.add_argument("source", type=Path, help="Directory with files to rename")
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Directory to move renamed files into (default: rename in place)",
    )
    parser.add_argument(
        "-p", "--pattern", default=DEFAULT_PATTERN,
        help=(
            "Naming template. Placeholders: "
            + ", ".join("{%s}" % p for p in PLACEHOLDERS)
            + f". Default: {DEFAULT_PATTERN!r}"
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without touching any files",
    )
    return parser.parse_args()


def validate_pattern(pattern: str) -> None:
    """Exit with a clear message if the pattern uses unknown placeholders."""
    used = set(re.findall(r"\{(\w+)\}", pattern))
    unknown = used - set(PLACEHOLDERS)
    if unknown:
        sys.exit(
            f"Error: unknown placeholder(s) in pattern: "
            f"{', '.join('{%s}' % p for p in sorted(unknown))}.\n"
            f"Available: {', '.join('{%s}' % p for p in PLACEHOLDERS)}"
        )


def main() -> None:
    args = parse_args()
    validate_pattern(args.pattern)
    api_key = get_api_key()

    source: Path = args.source
    if not source.is_dir():
        sys.exit(f"Error: '{source}' is not a directory.")

    out_dir: Path = args.output or source
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in source.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not files:
        print(f"No video files found in '{source}'.")
        return

    print(f"Found {len(files)} file(s).")
    for file_path in files:
        process_file(file_path, out_dir, api_key, args.pattern, args.dry_run)


if __name__ == "__main__":
    main()
