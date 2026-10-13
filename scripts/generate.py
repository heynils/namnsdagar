#!/usr/bin/env python3
"""Hämtar svenska namnsdagar från Wikipedia och skriver JSON + iCalendar-feed.

Kör från repots rot:  python3 scripts/generate.py
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_TITLE = "Lista över namnsdagar i Sverige i datumordning"
WIKI_URL = "https://sv.wikipedia.org/w/index.php?" + urllib.parse.urlencode(
    {"title": WIKI_TITLE, "action": "raw"}
)
PAGE_URL = "https://sv.wikipedia.org/wiki/" + urllib.parse.quote(WIKI_TITLE.replace(" ", "_"))
USER_AGENT = "namnsdagar/1.0 (https://github.com/heynils/namnsdagar)"

FEED_URL = "https://heynils.github.io/namnsdagar/namnsdagar.ics"
UID_DOMAIN = "heynils.github.io"
BASE_YEAR = 2022  # nuvarande namnlängd gäller från 2022
DTSTAMP = "20261013T000000Z"  # fast värde så att filen blir deterministisk
SEQUENCE = 1  # öka när befintliga händelser ändras, så att kalendrar hämtar om dem
EXPECTED_DAYS = 359  # 366 dagar minus 7 dagar utan namnsdag

MONTHS = {
    "januari": 1, "februari": 2, "mars": 3, "april": 4, "maj": 5, "juni": 6,
    "juli": 7, "augusti": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
}

ROW_RE = re.compile(r"^\|\s*\[\[(\d{1,2}) (\w+)\]\]\s*\|\|(.*)$")
NOTE_RE = re.compile(r"''\(.*?\)''")
LINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")


def fetch_wikitext() -> str:
    req = urllib.request.Request(WIKI_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse(wikitext: str) -> dict[str, list[str]]:
    days: dict[str, list[str]] = {}
    for line in wikitext.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        day, month_name, rest = int(m.group(1)), m.group(2).lower(), m.group(3)
        if month_name not in MONTHS:
            raise ValueError(f"Okänd månad: {line!r}")
        if "ingen namnsdag" in rest:
            continue
        rest = NOTE_RE.sub("", rest)
        names = [n.strip() for n in LINK_RE.findall(rest) if n.strip()]
        if not names:
            raise ValueError(f"Inga namn hittades: {line!r}")
        key = f"{MONTHS[month_name]:02d}-{day:02d}"
        if key in days:
            raise ValueError(f"Dubblett för {key}: {line!r}")
        days[key] = names
    return dict(sorted(days.items()))


def validate(days: dict[str, list[str]]) -> None:
    if len(days) != EXPECTED_DAYS:
        raise ValueError(f"Förväntade {EXPECTED_DAYS} dagar, fick {len(days)}")
    months = {k[:2] for k in days}
    if len(months) != 12:
        raise ValueError(f"Saknar månader, hittade bara {sorted(months)}")
    for key in days:
        date(2024, int(key[:2]), int(key[3:]))  # kastar vid ogiltigt datum
    if "02-29" in days:
        raise ValueError("Skottdagen ska inte ha namnsdag")


def escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    )


def fold(line: str) -> str:
    """Radvik enligt RFC 5545: max 75 oktetter per rad, utan att dela UTF-8-tecken."""
    out, current, limit = [], "", 75
    for ch in line:
        if len((current + ch).encode("utf-8")) > limit:
            out.append(current)
            current, limit = " " + ch, 75
        else:
            current += ch
    out.append(current)
    return "\r\n".join(out)


def build_ics(days: dict[str, list[str]]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//heynils//namnsdagar//SV",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Namnsdagar",
        "X-WR-CALDESC:" + escape("Svenska namnsdagar enligt almanackan. Källa: Wikipedia."),
        "X-WR-TIMEZONE:Europe/Stockholm",
        "REFRESH-INTERVAL;VALUE=DURATION:P1W",
        "X-PUBLISHED-TTL:P1W",
        "SOURCE;VALUE=URI:" + FEED_URL,
    ]
    for key, names in days.items():
        start = date(BASE_YEAR, int(key[:2]), int(key[3:]))
        end = start + timedelta(days=1)
        lines += [
            "BEGIN:VEVENT",
            f"UID:namnsdag-{key.replace('-', '')}@{UID_DOMAIN}",
            f"DTSTAMP:{DTSTAMP}",
            f"SEQUENCE:{SEQUENCE}",
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            "RRULE:FREQ=YEARLY",
            "SUMMARY:" + escape(", ".join(names)),
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def main() -> int:
    try:
        days = parse(fetch_wikitext())
        validate(days)
    except Exception as exc:  # noqa: BLE001
        print(f"Fel: {exc}", file=sys.stderr)
        print("Inga filer skrevs.", file=sys.stderr)
        return 1

    payload = {"source": PAGE_URL, "days": days}
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in (ROOT / "data" / "namnsdagar.json", ROOT / "docs" / "namnsdagar.json"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_text, encoding="utf-8")

    ics_path = ROOT / "docs" / "namnsdagar.ics"
    ics_path.write_bytes(build_ics(days).encode("utf-8"))

    total_names = sum(len(n) for n in days.values())
    print(f"Skrev {len(days)} dagar ({total_names} namn) till data/, docs/namnsdagar.json och docs/namnsdagar.ics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
