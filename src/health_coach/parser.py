from __future__ import annotations

import re
import subprocess
from datetime import date, datetime
from pathlib import Path

from .models import DaySummary, Event

DAY_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([A-Za-z]{3}) (\d{1,2}), (\d{4})$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2} [AP]M$")
GLUCOSE_RE = re.compile(r"^(\d+)\s*mg/dL$")


def pdf_to_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def clean_lines(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def parse_events(lines: list[str]) -> list[Event]:
    events: list[Event] = []
    current_day: date | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        day_match = DAY_RE.match(line)
        if day_match:
            current_day = datetime.strptime(line, "%a, %b %d, %Y").date()
            i += 1
            continue

        if current_day and TIME_RE.match(line):
            if i + 5 < len(lines) and lines[i + 1] == "CGM":
                event_type = lines[i + 2]
                details = lines[i + 3]
                glucose_val: int | None = None
                glucose_idx = i + 5 if lines[i + 4] == "--" else i + 4
                if glucose_idx < len(lines):
                    glucose_match = GLUCOSE_RE.match(lines[glucose_idx])
                    if glucose_match:
                        glucose_val = int(glucose_match.group(1))
                at = datetime.combine(current_day, datetime.strptime(line, "%I:%M %p").time())
                events.append(Event(event_type=event_type, details=details, at=at, glucose=glucose_val))
                i = glucose_idx + 1
                continue
        i += 1
    return events


def split_days(events: list[Event]) -> dict[date, DaySummary]:
    by_day: dict[date, DaySummary] = {}
    for event in events:
        if event.at.date() not in by_day:
            by_day[event.at.date()] = DaySummary(day=event.at.date(), meals=[], activity=[])
        if event.event_type.lower() == "meal":
            by_day[event.at.date()].meals.append(event)
        elif event.event_type.lower() in {"walking", "activity", "exercise", "running"}:
            by_day[event.at.date()].activity.append(event)
    for summary in by_day.values():
        summary.meals.sort(key=lambda item: item.at)
        summary.activity.sort(key=lambda item: item.at)
    return by_day


def extract_patient_name(lines: list[str]) -> str:
    for i, line in enumerate(lines):
        if line == "Daily" and i + 2 < len(lines):
            return lines[i + 2]
    return "Unknown Patient"


def parse_pdf(pdf_path: Path) -> tuple[str, list[DaySummary]]:
    text = pdf_to_text(pdf_path)
    lines = clean_lines(text)
    patient_name = extract_patient_name(lines)
    events = parse_events(lines)
    days = list(split_days(events).values())
    if not days:
        raise ValueError(f"No meal/activity data parsed from {pdf_path.name}")
    return patient_name, days
