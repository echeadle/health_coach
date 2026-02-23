from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from health_coach import cli
from health_coach.models import DayInterview, DaySummary, PeriodCheckin, WeeklySession


def test_cli_no_pdf_no_worksheet_returns_zero_when_inbox_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inbox = tmp_path / "inbox"
    monkeypatch.setattr("sys.argv", ["prog", "--inbox", str(inbox), "--reports", str(tmp_path / "reports")])

    rc = cli.run()

    assert rc == 0
    captured = capsys.readouterr()
    assert "No PDFs found in" in captured.out


def test_worksheet_only_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--worksheet-only",
            "--reports",
            str(tmp_path),
            "--start-date",
            "2026-02-16",
            "--end-date",
            "2026-02-22",
            "--patient-name",
            "Edward Cheadle",
            "--non-interactive",
        ],
    )

    rc = cli.run()

    assert rc == 0
    out = tmp_path / "mood_intake_2026-02-16_to_2026-02-22.md"
    assert out.exists()
    assert "# Mood Intake Worksheet" in out.read_text(encoding="utf-8")


def test_worksheet_only_day_filter_writes_single_day_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--worksheet-only",
            "--reports",
            str(tmp_path),
            "--start-date",
            "2026-02-16",
            "--end-date",
            "2026-02-22",
            "--day",
            "2026-02-20",
            "--patient-name",
            "Edward Cheadle",
            "--non-interactive",
        ],
    )

    rc = cli.run()

    assert rc == 0
    out = tmp_path / "mood_intake_2026-02-20_to_2026-02-20.md"
    assert out.exists()


def test_pdf_flow_archives_source_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    reports = tmp_path / "reports"
    archive = tmp_path / "archive"
    inbox.mkdir()
    source_pdf = inbox / "weekly.pdf"
    source_pdf.write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--inbox",
            str(inbox),
            "--reports",
            str(reports),
            "--archive",
            str(archive),
            "--non-interactive",
        ],
    )

    monkeypatch.setattr(
        cli,
        "parse_pdf",
        lambda _path: ("Edward Cheadle", [DaySummary(day=date(2026, 2, 22), meals=[], activity=[])]),
    )
    monkeypatch.setattr(
        cli,
        "run_interview",
        lambda **_kwargs: WeeklySession(
            patient_name="Edward Cheadle",
            start=date(2026, 2, 22),
            end=date(2026, 2, 22),
            days=[
                DayInterview(
                    day=date(2026, 2, 22),
                    meals=[],
                    activity=[],
                    checkins=[PeriodCheckin(period="After Breaking Fast", time_of_day=None, energy="Not provided", mood="Not provided")],
                )
            ],
            source_pdf="weekly.pdf",
        ),
    )
    monkeypatch.setattr(cli, "build_weekly_report", lambda _session: "# report\n")
    monkeypatch.setattr(cli, "build_mood_intake_worksheet", lambda _session: "# worksheet\n")

    rc = cli.run()

    assert rc == 0
    assert (reports / "report_2026-02-22_to_2026-02-22.md").exists()
    assert (reports / "mood_intake_2026-02-22_to_2026-02-22.md").exists()
    assert (archive / "clarity_2026-02-22_to_2026-02-22.pdf").exists()
    assert not source_pdf.exists()
