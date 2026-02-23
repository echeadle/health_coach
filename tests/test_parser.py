from __future__ import annotations

from datetime import datetime

from health_coach import parser


def test_parse_events_extracts_meal_and_activity() -> None:
    lines = [
        "Sun, Feb 22, 2026",
        "9:40 AM",
        "CGM",
        "Meal",
        "Egg omelette",
        "--",
        "117 mg/dL",
        "10:56 AM",
        "CGM",
        "Walking",
        "33 min • 88 BPM",
        "--",
        "108 mg/dL",
    ]

    events = parser.parse_events(lines)

    assert len(events) == 2
    assert events[0].event_type == "Meal"
    assert events[0].details == "Egg omelette"
    assert events[0].glucose == 117
    assert events[0].at == datetime(2026, 2, 22, 9, 40)
    assert events[1].event_type == "Walking"
    assert events[1].details == "33 min • 88 BPM"
    assert events[1].glucose == 108


def test_extract_patient_name() -> None:
    lines = ["Daily", "7 days", "Edward Cheadle"]
    assert parser.extract_patient_name(lines) == "Edward Cheadle"
