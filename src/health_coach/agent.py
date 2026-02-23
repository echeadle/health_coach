from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from .tools import (
    ask_day_selection,
    build_days_for_range,
    choose_days,
    parse_clarity_pdf,
    parse_iso_date,
    render_outputs,
    run_interview_session,
    save_outputs,
)


def _resolve_selected_days(args: Namespace) -> list:
    return [parse_iso_date(item) for item in args.day] if args.day else []


def run_pdf_agent(args: Namespace, pdf_path: Path) -> int:
    patient_name, day_summaries = parse_clarity_pdf(pdf_path)
    if args.patient_name != "Unknown Patient":
        patient_name = args.patient_name

    selected_days = _resolve_selected_days(args)
    if selected_days:
        day_summaries = choose_days(day_summaries=day_summaries, selected_days=selected_days)
    else:
        day_summaries = ask_day_selection(day_summaries=day_summaries, non_interactive=args.non_interactive)

    session = run_interview_session(
        patient_name=patient_name,
        day_summaries=day_summaries,
        source_pdf=pdf_path.name,
        non_interactive=args.non_interactive,
    )
    report_text, worksheet_text = render_outputs(session=session)
    outputs = save_outputs(
        session=session,
        report_text=report_text,
        worksheet_text=worksheet_text,
        reports_dir=args.reports,
        archive_dir=args.archive,
        source_pdf=pdf_path,
    )

    print(f"Created report: {outputs['report']}")
    print(f"Created mood worksheet: {outputs['worksheet']}")
    print(f"Created session artifact: {outputs['session']}")
    if "archive" in outputs:
        print(f"Archived source PDF: {outputs['archive']}")
    return 0


def run_worksheet_agent(args: Namespace) -> int:
    if args.start_date:
        start = parse_iso_date(args.start_date)
    else:
        start = parse_iso_date(input("Start date (YYYY-MM-DD): ").strip())
    if args.end_date:
        end = parse_iso_date(args.end_date)
    else:
        end = parse_iso_date(input("End date (YYYY-MM-DD): ").strip())

    day_summaries = build_days_for_range(start=start, end=end)
    selected_days = _resolve_selected_days(args)
    if selected_days:
        day_summaries = choose_days(day_summaries=day_summaries, selected_days=selected_days)
    else:
        day_summaries = ask_day_selection(day_summaries=day_summaries, non_interactive=args.non_interactive)

    session = run_interview_session(
        patient_name=args.patient_name,
        day_summaries=day_summaries,
        source_pdf=None,
        non_interactive=args.non_interactive,
    )
    report_text, worksheet_text = render_outputs(session=session)
    outputs = save_outputs(
        session=session,
        report_text=report_text,
        worksheet_text=worksheet_text,
        reports_dir=args.reports,
        archive_dir=args.archive,
        source_pdf=None,
    )

    print(f"Created mood worksheet: {outputs['worksheet']}")
    print(f"Created session artifact: {outputs['session']}")
    return 0
