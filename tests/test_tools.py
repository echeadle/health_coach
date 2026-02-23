from __future__ import annotations

from datetime import date
from pathlib import Path

from health_coach.models import WeeklySession
from health_coach.tools import save_outputs


def test_save_outputs_writes_files_and_archives_pdf(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    archive_dir = tmp_path / "archive"
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_text("pdf", encoding="utf-8")

    session = WeeklySession(
        patient_name="Edward Cheadle",
        start=date(2026, 2, 20),
        end=date(2026, 2, 20),
        days=[],
        source_pdf="source.pdf",
    )

    outputs = save_outputs(
        session=session,
        report_text="# report\n",
        worksheet_text="# worksheet\n",
        reports_dir=reports_dir,
        archive_dir=archive_dir,
        source_pdf=source_pdf,
    )

    assert outputs["report"].exists()
    assert outputs["worksheet"].exists()
    assert outputs["session"].exists()
    assert outputs["archive"].exists()
    assert not source_pdf.exists()
