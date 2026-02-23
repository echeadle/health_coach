from __future__ import annotations

from pathlib import Path

import pytest

from health_coach import cli


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


def test_pdf_flow_uses_agent_for_inbox_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    reports = tmp_path / "reports"
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
                "--non-interactive",
            ],
        )

    calls: list[Path] = []

    def fake_run_pdf_agent(args, pdf_path: Path) -> int:  # type: ignore[no-untyped-def]
        calls.append(pdf_path)
        return 0

    monkeypatch.setattr(cli, "run_pdf_agent", fake_run_pdf_agent)

    rc = cli.run()

    assert rc == 0
    assert calls == [source_pdf]
