from __future__ import annotations

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

from .interview import run_interview
from .models import DaySummary
from .parser import parse_pdf
from .reports import build_mood_intake_worksheet, build_weekly_report


def parse_iso_date(value: str) -> date:
    from datetime import datetime

    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_args() -> argparse.Namespace:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Interview-driven Clarity weekly report builder")
    parser.add_argument("--pdf", type=Path, help="Path to Clarity PDF")
    parser.add_argument("--inbox", type=Path, default=Path(os.getenv("CLARITY_INBOX_DIR", "Clarity_Inbox")))
    parser.add_argument("--archive", type=Path, default=Path(os.getenv("CLARITY_ARCHIVE_DIR", "Clarity_Reports")))
    parser.add_argument("--reports", type=Path, default=Path(os.getenv("REPORTS_OUTPUT_DIR", "Reports")))
    parser.add_argument("--patient-name", default=os.getenv("PATIENT_NAME", "Unknown Patient"))
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--worksheet-only", action="store_true")
    parser.add_argument("--start-date", type=str, help="Worksheet start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="Worksheet end date YYYY-MM-DD")
    parser.add_argument(
        "--day",
        action="append",
        default=[],
        help="Specific day to work on (YYYY-MM-DD). Repeat to include multiple days.",
    )
    return parser.parse_args()


def _days_for_range(start: date, end: date) -> list[DaySummary]:
    days: list[DaySummary] = []
    current = start
    while current <= end:
        days.append(DaySummary(day=current, meals=[], activity=[]))
        current += timedelta(days=1)
    return sorted(days, key=lambda d: d.day, reverse=True)


def _filter_days(day_summaries: list[DaySummary], selected_days: list[date]) -> list[DaySummary]:
    if not selected_days:
        return day_summaries
    selected = set(selected_days)
    filtered = [day for day in day_summaries if day.day in selected]
    if not filtered:
        raise ValueError("No matching days found for --day selection.")
    return filtered


def _choose_days_interactively(day_summaries: list[DaySummary], non_interactive: bool) -> list[DaySummary]:
    if non_interactive:
        return day_summaries
    if not day_summaries:
        return day_summaries

    dates = ", ".join(day.day.isoformat() for day in day_summaries)
    response = input(f"Available days: {dates}\nEnter date(s) to work on (comma-separated), or press Enter for all: ").strip()
    if not response:
        return day_summaries

    selected_days: list[date] = []
    for part in response.split(","):
        item = part.strip()
        if not item:
            continue
        selected_days.append(parse_iso_date(item))
    return _filter_days(day_summaries=day_summaries, selected_days=selected_days)


def _next_available_archive_path(archive_dir: Path, base_name: str) -> Path:
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


def _run_pdf_flow(args: argparse.Namespace, pdf_path: Path) -> int:
    patient_name, day_summaries = parse_pdf(pdf_path)
    if args.patient_name != "Unknown Patient":
        patient_name = args.patient_name

    if args.day:
        selected_days = [parse_iso_date(item) for item in args.day]
        day_summaries = _filter_days(day_summaries=day_summaries, selected_days=selected_days)
    else:
        day_summaries = _choose_days_interactively(day_summaries=day_summaries, non_interactive=args.non_interactive)

    session = run_interview(
        patient_name=patient_name,
        day_summaries=day_summaries,
        source_pdf=pdf_path.name,
        non_interactive=args.non_interactive,
    )

    report_path = args.reports / f"report_{session.start.isoformat()}_to_{session.end.isoformat()}.md"
    mood_path = args.reports / f"mood_intake_{session.start.isoformat()}_to_{session.end.isoformat()}.md"
    report_path.write_text(build_weekly_report(session), encoding="utf-8")
    mood_path.write_text(build_mood_intake_worksheet(session), encoding="utf-8")

    archive_name = f"clarity_{session.start.isoformat()}_to_{session.end.isoformat()}.pdf"
    archive_path = _next_available_archive_path(args.archive, archive_name)
    pdf_path.rename(archive_path)

    print(f"Created report: {report_path}")
    print(f"Created mood worksheet: {mood_path}")
    print(f"Archived source PDF: {archive_path}")
    return 0


def run() -> int:
    args = parse_args()
    args.reports.mkdir(parents=True, exist_ok=True)
    args.archive.mkdir(parents=True, exist_ok=True)

    if args.worksheet_only:
        if args.start_date:
            start = parse_iso_date(args.start_date)
        else:
            start = parse_iso_date(input("Start date (YYYY-MM-DD): ").strip())
        if args.end_date:
            end = parse_iso_date(args.end_date)
        else:
            end = parse_iso_date(input("End date (YYYY-MM-DD): ").strip())
        if start > end:
            raise ValueError("Start date must be on or before end date.")

        day_summaries = _days_for_range(start=start, end=end)
        if args.day:
            selected_days = [parse_iso_date(item) for item in args.day]
            day_summaries = _filter_days(day_summaries=day_summaries, selected_days=selected_days)
        else:
            day_summaries = _choose_days_interactively(day_summaries=day_summaries, non_interactive=args.non_interactive)

        session = run_interview(
            patient_name=args.patient_name,
            day_summaries=day_summaries,
            source_pdf=None,
            non_interactive=args.non_interactive,
        )
        mood_path = args.reports / f"mood_intake_{session.start.isoformat()}_to_{session.end.isoformat()}.md"
        mood_path.write_text(build_mood_intake_worksheet(session), encoding="utf-8")
        print(f"Created mood worksheet: {mood_path}")
        return 0

    if not args.pdf:
        args.inbox.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(args.inbox.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {args.inbox}")
            return 0
        for pdf in pdfs:
            _run_pdf_flow(args=args, pdf_path=pdf)
        return 0

    return _run_pdf_flow(args=args, pdf_path=args.pdf)
