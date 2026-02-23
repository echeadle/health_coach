from __future__ import annotations

from datetime import date, datetime

from health_coach import interview
from health_coach.interview import run_interview
from health_coach.models import DaySummary, Event
from health_coach.reports import build_mood_intake_worksheet, build_weekly_report


def test_run_interview_non_interactive_builds_checkins() -> None:
    days = [
        DaySummary(
            day=date(2026, 2, 22),
            meals=[
                Event("Meal", "Egg omelette", datetime(2026, 2, 22, 9, 40), 117),
                Event("Meal", "Soup", datetime(2026, 2, 22, 18, 5), 104),
            ],
            activity=[Event("Walking", "33 min • 88 BPM", datetime(2026, 2, 22, 10, 56), 108)],
        )
    ]

    session = run_interview(
        patient_name="Edward Cheadle",
        day_summaries=days,
        source_pdf="sample.pdf",
        non_interactive=True,
    )

    assert session.patient_name == "Edward Cheadle"
    assert len(session.days) == 1
    assert session.days[0].meals[0].label == "Breakfast"
    assert session.days[0].meals[1].label == "Dinner"
    assert session.days[0].checkins[0].period == "After Breaking Fast"
    assert session.days[0].checkins[1].period == "Around Noon"


def test_reports_render_expected_headers() -> None:
    days = [
        DaySummary(
            day=date(2026, 2, 22),
            meals=[Event("Meal", "Egg omelette", datetime(2026, 2, 22, 9, 40), 117)],
            activity=[Event("Walking", "33 min • 88 BPM", datetime(2026, 2, 22, 10, 56), 108)],
        )
    ]
    session = run_interview(
        patient_name="Edward Cheadle",
        day_summaries=days,
        source_pdf="clarity_2026-02-22.pdf",
        non_interactive=True,
    )

    report = build_weekly_report(session)
    worksheet = build_mood_intake_worksheet(session)

    assert "| Event | Time of Day | Details | Energy (Description) | Mood (Description & Score 1-5) |" in report
    assert "| **After Breaking Fast** | 9:40 AM |  | Not provided | Not provided |" in report
    assert "| Breakfast | 9:40 AM | Egg omelette |  |  |" in report
    assert "# Mood Intake Worksheet" in worksheet
    assert "| **Around Noon** | 12:00 PM | Not provided | Not provided |" in worksheet


def test_mood_prompt_mentions_scale(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_prompt(text: str) -> str:
        prompts.append(text)
        return ""

    monkeypatch.setattr(interview, "_prompt", fake_prompt)
    energy, mood = interview._prompt_period_fields(
        day_label="Sunday, Feb 22, 2026",
        period="After Breaking Fast",
        non_interactive=False,
    )

    assert energy == "Not provided"
    assert mood == "Not provided"
    assert any("1-5 scale" in prompt for prompt in prompts)
