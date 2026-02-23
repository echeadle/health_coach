from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from .interview import run_interview
from .models import DaySummary, WeeklySession
from .parser import parse_pdf
from .reports import build_mood_intake_worksheet, build_weekly_report

InputFn = Callable[[str], str]


def parse_iso_date(value: str) -> date:
    from datetime import datetime

    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_clarity_pdf(pdf_path: Path) -> tuple[str, list[DaySummary]]:
    return parse_pdf(pdf_path)


def build_days_for_range(start: date, end: date) -> list[DaySummary]:
    if start > end:
        raise ValueError("Start date must be on or before end date.")
    days: list[DaySummary] = []
    current = start
    while current <= end:
        days.append(DaySummary(day=current, meals=[], activity=[]))
        current += timedelta(days=1)
    return sorted(days, key=lambda d: d.day, reverse=True)


def choose_days(day_summaries: list[DaySummary], selected_days: list[date]) -> list[DaySummary]:
    if not selected_days:
        return day_summaries
    selected = set(selected_days)
    filtered = [day for day in day_summaries if day.day in selected]
    if not filtered:
        raise ValueError("No matching days found for selected day filter.")
    return filtered


def ask_day_selection(day_summaries: list[DaySummary], non_interactive: bool, input_fn: InputFn = input) -> list[DaySummary]:
    if non_interactive or not day_summaries:
        return day_summaries

    available = ", ".join(day.day.isoformat() for day in day_summaries)
    response = input_fn(
        f"What day or days do you want to work on?\n"
        f"Available days: {available}\n"
        f"Enter date(s) as YYYY-MM-DD, comma-separated, or press Enter for all: "
    ).strip()

    if not response:
        return day_summaries

    selected_days: list[date] = []
    for part in response.split(","):
        item = part.strip()
        if item:
            selected_days.append(parse_iso_date(item))
    return choose_days(day_summaries=day_summaries, selected_days=selected_days)


def run_interview_session(
    patient_name: str,
    day_summaries: list[DaySummary],
    source_pdf: str | None,
    non_interactive: bool,
) -> WeeklySession:
    return run_interview(
        patient_name=patient_name,
        day_summaries=day_summaries,
        source_pdf=source_pdf,
        non_interactive=non_interactive,
    )


def render_outputs(session: WeeklySession) -> tuple[str, str]:
    return build_weekly_report(session), build_mood_intake_worksheet(session)


def next_available_archive_path(archive_dir: Path, base_name: str) -> Path:
    candidate = archive_dir / base_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        alt = archive_dir / f"{stem}_{counter}{suffix}"
        if not alt.exists():
            return alt
        counter += 1


def write_session_artifact(session: WeeklySession, reports_dir: Path) -> Path:
    path = reports_dir / f"session_{session.start.isoformat()}_to_{session.end.isoformat()}.json"
    payload = asdict(session)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def save_outputs(
    session: WeeklySession,
    report_text: str,
    worksheet_text: str,
    reports_dir: Path,
    archive_dir: Path,
    source_pdf: Path | None,
) -> dict[str, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"report_{session.start.isoformat()}_to_{session.end.isoformat()}.md"
    mood_path = reports_dir / f"mood_intake_{session.start.isoformat()}_to_{session.end.isoformat()}.md"
    report_path.write_text(report_text, encoding="utf-8")
    mood_path.write_text(worksheet_text, encoding="utf-8")

    session_path = write_session_artifact(session=session, reports_dir=reports_dir)

    archive_path: Path | None = None
    if source_pdf is not None:
        archive_name = f"clarity_{session.start.isoformat()}_to_{session.end.isoformat()}.pdf"
        archive_path = next_available_archive_path(archive_dir=archive_dir, base_name=archive_name)
        source_pdf.rename(archive_path)

    result: dict[str, Path] = {
        "report": report_path,
        "worksheet": mood_path,
        "session": session_path,
    }
    if archive_path:
        result["archive"] = archive_path
    return result
