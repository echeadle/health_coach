from __future__ import annotations

from datetime import date, time

from .models import DayInterview, WeeklySession


def fmt_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def fmt_day_heading(value: date) -> str:
    return f"{value.strftime('%A')}, {value.strftime('%b')} {value.day}, {value.year}"


def fmt_clock(value: time) -> str:
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{hour}:{value.minute:02d} {suffix}"


def _meal_rows(day: DayInterview, period: str) -> list[str]:
    period_meals = []
    if period == "After Breaking Fast":
        period_meals = [m for m in day.meals if m.label in {"Breakfast", "Snack"}]
    elif period == "Around Noon":
        period_meals = [m for m in day.meals if m.label in {"Lunch", "Snack"}]
    elif period == "After Dinner":
        period_meals = [m for m in day.meals if m.label in {"Dinner", "Snack"}]

    rows = [f"| {m.label} | {fmt_clock(m.event.at.time())} | {m.event.details} |  |  |" for m in period_meals]

    if period != "Before Bed":
        for item in day.activity:
            t = item.at.time()
            if period == "After Breaking Fast" and not (time(4, 0) <= t < time(11, 0)):
                continue
            if period == "Around Noon" and not (time(11, 0) <= t < time(16, 0)):
                continue
            if period == "After Dinner" and not (t >= time(16, 0) or t < time(4, 0)):
                continue
            rows.append(f"| Exercise | {fmt_clock(item.at.time())} | {item.details} |  |  |")
    return rows


def build_weekly_report(session: WeeklySession) -> str:
    out: list[str] = []
    out.append(f"# {len(session.days)}-Day Food, Energy, and Mood Journal")
    out.append("")
    out.append(f"**Name:** {session.patient_name}")
    out.append("")
    out.append(f"**Dates:** {fmt_date(session.start)} - {fmt_date(session.end)}")
    out.append("")
    if session.source_pdf:
        out.append(f"**Source PDF:** {session.source_pdf}")
        out.append("")
    out.append("---")
    out.append("")

    for idx, day in enumerate(session.days, start=1):
        out.append(f"### **Day {idx}: {fmt_day_heading(day.day)}**")
        out.append("")
        out.append("| Event | Time of Day | Details | Energy (Description) | Mood (Description & Score 1-5) |")
        out.append("| --- | --- | --- | --- | --- |")

        for checkin in day.checkins:
            t = fmt_clock(checkin.time_of_day) if checkin.time_of_day else "Not available"
            out.append(f"| **{checkin.period}** | {t} |  | {checkin.energy} | {checkin.mood} |")
            out.extend(_meal_rows(day=day, period=checkin.period))

        out.append("")
        out.append("---")
        out.append("")

    return "\n".join(out).strip() + "\n"


def build_mood_intake_worksheet(session: WeeklySession) -> str:
    out: list[str] = []
    out.append("# Mood Intake Worksheet")
    out.append("")
    out.append(f"**Name:** {session.patient_name}")
    out.append("")
    out.append(f"**Dates:** {fmt_date(session.start)} - {fmt_date(session.end)}")
    out.append("")
    out.append("---")
    out.append("")

    for idx, day in enumerate(session.days, start=1):
        out.append(f"### **Day {idx}: {fmt_day_heading(day.day)}**")
        out.append("")
        out.append("| Time of Day | Time | Energy | Mood |")
        out.append("| --- | --- | --- | --- |")
        for checkin in day.checkins:
            t = fmt_clock(checkin.time_of_day) if checkin.time_of_day else "Not available"
            out.append(f"| **{checkin.period}** | {t} | {checkin.energy} | {checkin.mood} |")
        out.append("")
        out.append("---")
        out.append("")

    return "\n".join(out).strip() + "\n"
