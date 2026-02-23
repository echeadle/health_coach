from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from .agent import run_pdf_agent, run_worksheet_agent


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


def run() -> int:
    args = parse_args()
    args.reports.mkdir(parents=True, exist_ok=True)
    args.archive.mkdir(parents=True, exist_ok=True)

    if args.worksheet_only:
        return run_worksheet_agent(args)

    if not args.pdf:
        args.inbox.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(args.inbox.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {args.inbox}")
            return 0
        for pdf in pdfs:
            run_pdf_agent(args=args, pdf_path=pdf)
        return 0

    return run_pdf_agent(args=args, pdf_path=args.pdf)
