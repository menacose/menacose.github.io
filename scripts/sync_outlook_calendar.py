#!/usr/bin/env python3
"""Fetch an Outlook-published ICS calendar and sync the homepage events section."""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HOMEPAGE_PATH = REPO_ROOT / "_data" / "homepage.yml"
POSTS_DIR = REPO_ROOT / "_posts"
DEFAULT_AUTHOR = os.environ.get("CALENDAR_POST_AUTHOR", "MENACOSE")


def unfold_ics_lines(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    unfolded: list[str] = []
    for line in lines:
        if not line:
            unfolded.append("")
            continue
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def parse_property(line: str) -> tuple[str, dict[str, str], str]:
    key_part, _, value = line.partition(":")
    segments = key_part.split(";")
    name = segments[0].upper()
    params: dict[str, str] = {}
    for raw_param in segments[1:]:
        param_name, _, param_value = raw_param.partition("=")
        params[param_name.upper()] = param_value
    return name, params, value


def parse_ics_events(text: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in unfold_ics_lines(text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue

        name, params, value = parse_property(line)
        if name in {"SUMMARY", "DESCRIPTION", "LOCATION", "URL", "UID", "STATUS"}:
            current[name] = value.strip()
        elif name in {"DTSTART", "DTEND"}:
            current[name] = value.strip()
            if "VALUE" in params:
                current[f"{name}_VALUE"] = params["VALUE"]
            if "TZID" in params:
                current[f"{name}_TZID"] = params["TZID"]

    return events


def normalize_text(value: str) -> str:
    cleaned = value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").strip()
    return " ".join(cleaned.split())


def decode_ics_text(value: str) -> str:
    return (
        value.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .strip()
    )


def strip_urls(value: str) -> str:
    return re.sub(r"https?://\S+|www\.\S+", "", value).strip()


def clean_multiline_text(value: str) -> str:
    decoded = decode_ics_text(value)
    without_urls = strip_urls(decoded)
    lines = [" ".join(line.split()) for line in without_urls.splitlines()]
    lines = [line for line in lines if line]
    return "\n\n".join(lines)


def summarize_text(value: str, max_length: int = 220) -> str:
    summary = normalize_text(strip_urls(value))
    if len(summary) <= max_length:
        return summary
    shortened = summary[: max_length - 3].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened + "..."


def slugify(value: str) -> str:
    ascii_value = value.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or "event"


def parse_ics_datetime(raw_value: str, value_type: str | None) -> tuple[str, bool]:
    if value_type == "DATE":
        parsed = dt.datetime.strptime(raw_value, "%Y%m%d").date()
        return parsed.isoformat(), True

    if raw_value.endswith("Z"):
        parsed = dt.datetime.strptime(raw_value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
        return parsed.isoformat().replace("+00:00", "Z"), False

    parsed = dt.datetime.strptime(raw_value, "%Y%m%dT%H%M%S")
    return parsed.isoformat(), False


def event_sort_key(event: dict[str, str]) -> tuple[str, str]:
    return event.get("date", ""), event.get("title", "").lower()


def iso_date_only(raw_value: str) -> dt.date:
    return dt.date.fromisoformat(raw_value[:10])


def format_display_datetime(raw_value: str) -> str:
    if len(raw_value) == 10:
        return dt.date.fromisoformat(raw_value).strftime("%A, %d %B %Y")

    normalized = raw_value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        return parsed.strftime("%A, %d %B %Y at %H:%M UTC")
    return parsed.strftime("%A, %d %B %Y at %H:%M")


def safe_location(value: str) -> str:
    cleaned = normalize_text(strip_urls(value))
    return cleaned


def build_post_body(event: dict[str, str]) -> str:
    lines: list[str] = []

    description = event.get("page_description", "").strip()
    if description:
        lines.append("### Description")
        lines.append(description)
        lines.append("")

    lines.append("### Event Details")
    lines.append(f'- **Date:** {format_display_datetime(event["date"])}')
    if event.get("end_date"):
        lines.append(f'- **Ends:** {format_display_datetime(event["end_date"])}')
    if event.get("location"):
        lines.append(f'- **Location:** {event["location"]}')
    lines.append("")
    lines.append("This page was generated automatically from the Outlook calendar invitation.")
    return "\n".join(lines).rstrip() + "\n"


def build_post_front_matter(event: dict[str, str]) -> str:
    front_matter = [
        "---",
        "layout: event",
        f'title: {yaml_quote(event["title"])}',
        f'date: {yaml_quote(event["date"])}',
        "tags: events",
        "categories: [events]",
        f'author: {yaml_quote(DEFAULT_AUTHOR)}',
        "featured: false",
        f'permalink: {yaml_quote(event["link"])}',
        "sync_source: outlook",
        "---",
        "",
    ]
    return "\n".join(front_matter)


def is_outlook_synced_post(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "sync_source: outlook" in content


def write_synced_posts(events: list[dict[str, str]]) -> None:
    expected_files: set[Path] = set()

    for event in events:
        post_filename = f'{event["date"][:10]}-{event["slug"]}.md'
        post_path = POSTS_DIR / post_filename
        expected_files.add(post_path)
        post_content = build_post_front_matter(event) + build_post_body(event)
        post_path.write_text(post_content, encoding="utf-8")

    legacy_synced_dir = POSTS_DIR / "synced"
    if legacy_synced_dir.exists():
        for existing_file in legacy_synced_dir.glob("*.md"):
            existing_file.unlink()
        try:
            legacy_synced_dir.rmdir()
        except OSError:
            pass

    for existing_file in POSTS_DIR.glob("*.md"):
        if existing_file not in expected_files and is_outlook_synced_post(existing_file):
            existing_file.unlink()


def transform_events(raw_events: list[dict[str, str]]) -> list[dict[str, str]]:
    today = dt.date.today()
    lookback_days = int(os.environ.get("CALENDAR_LOOKBACK_DAYS", "30"))
    lookahead_days = int(os.environ.get("CALENDAR_LOOKAHEAD_DAYS", "730"))
    window_start = today - dt.timedelta(days=lookback_days)
    window_end = today + dt.timedelta(days=lookahead_days)

    transformed: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw_event in raw_events:
        if raw_event.get("STATUS", "").upper() == "CANCELLED":
            continue
        if "SUMMARY" not in raw_event or "DTSTART" not in raw_event:
            continue

        date_value, is_all_day = parse_ics_datetime(
            raw_event["DTSTART"],
            raw_event.get("DTSTART_VALUE"),
        )
        event_day = iso_date_only(date_value)
        if event_day < window_start or event_day > window_end:
            continue

        event: dict[str, str] = {
            "title": normalize_text(raw_event["SUMMARY"]),
            "date": date_value,
        }
        event["slug"] = slugify(event["title"])
        event["link"] = f'/{event["slug"]}.html'

        if "DTEND" in raw_event:
            end_value, _ = parse_ics_datetime(raw_event["DTEND"], raw_event.get("DTEND_VALUE"))
            if end_value != date_value:
                event["end_date"] = end_value

        if raw_event.get("DESCRIPTION"):
            event["description"] = summarize_text(raw_event["DESCRIPTION"])
            event["page_description"] = clean_multiline_text(raw_event["DESCRIPTION"])
        if raw_event.get("LOCATION"):
            location = safe_location(raw_event["LOCATION"])
            if location:
                event["location"] = location
        if not event.get("description"):
            event["description"] = (
                f'Join us for "{event["title"]}" on {format_display_datetime(event["date"])}.'
            )
        if not event.get("page_description"):
            event["page_description"] = event["description"]

        dedupe_key = (event["title"], event["date"])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        transformed.append(event)

    transformed.sort(key=event_sort_key)
    return transformed


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump_events_block(events: list[dict[str, str]]) -> str:
    lines: list[str] = ["events:"]
    ordered_keys = ["title", "date", "end_date", "description", "location", "link"]
    if not events:
        lines[0] = "events: []"
        return "\n".join(lines) + "\n"

    for event in events:
        lines.append(f'  - title : {yaml_quote(event["title"])}')
        for key in ordered_keys[1:]:
            if key in event and event[key]:
                lines.append(f"    {key} : " + yaml_quote(event[key]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def replace_events_section(homepage_text: str, events_block: str) -> str:
    pattern = re.compile(r"(?ms)^events:\n.*?(?=^################## |\Z)")
    if pattern.search(homepage_text):
        return pattern.sub(events_block, homepage_text)
    return homepage_text.rstrip() + "\n\n" + events_block


def fetch_ics(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "menacose-calendar-sync/1.0",
            "Accept": "text/calendar,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def main() -> int:
    ics_url = os.environ.get("OUTLOOK_CALENDAR_ICS_URL", "").strip()
    if not ics_url:
        print("OUTLOOK_CALENDAR_ICS_URL is not set.", file=sys.stderr)
        return 1

    ics_text = fetch_ics(ics_url)
    events = transform_events(parse_ics_events(ics_text))
    allow_empty_sync = os.environ.get("CALENDAR_ALLOW_EMPTY_SYNC", "false").lower() == "true"

    if not events and not allow_empty_sync:
        print(
            "No calendar events were found in the Outlook feed. "
            "Keeping the existing homepage events unchanged.",
        )
        return 0

    homepage_text = HOMEPAGE_PATH.read_text(encoding="utf-8")
    updated_homepage = replace_events_section(homepage_text, dump_events_block(events))
    HOMEPAGE_PATH.write_text(updated_homepage, encoding="utf-8")
    write_synced_posts(events)
    print(f"Synced {len(events)} event(s) into {HOMEPAGE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
