from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from .models import ClassifiedMeal, DayInterview, DaySummary, PeriodCheckin, WeeklySession

PERIODS = ("After Breaking Fast", "Around Noon", "After Dinner", "Before Bed")
MEAL_LABELS = ("Breakfast", "Lunch", "Dinner", "Snack")


def fmt_day_heading(value: date) -> str:
    return f"{value.strftime('%A')}, {value.strftime('%b')} {value.day}, {value.year}"


def fmt_clock(value: time) -> str:
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{hour}:{value.minute:02d} {suffix}"


def infer_meal_label(at_time: time) -> str:
    if time(4, 0) <= at_time < time(11, 0):
        return "Breakfast"
    if time(11, 0) <= at_time < time(16, 0):
        return "Lunch"
    if time(16, 0) <= at_time < time(22, 0):
        return "Dinner"
    return "Snack"


def parse_time_input(response: str) -> Optional[time]:
    text = response.strip().upper()
    if not text:
        return None
    return datetime.strptime(text, "%I:%M %p").time()


def _prompt(prompt: str) -> str:
    return input(prompt).strip()


def classify_meals(summary: DaySummary, non_interactive: bool) -> list[ClassifiedMeal]:
    out: list[ClassifiedMeal] = []
    day_label = fmt_day_heading(summary.day)
    for meal in summary.meals:
        default = infer_meal_label(meal.at.time())
        if non_interactive:
            label = default
        else:
            response = _prompt(
                f"{day_label} {fmt_clock(meal.at.time())} '{meal.details}' -> Breakfast/Lunch/Dinner/Snack [{default}]: "
            ).title()
            label = response if response in MEAL_LABELS else default
        out.append(ClassifiedMeal(label=label, event=meal))
    return out


def _period_anchor(period: str, meals: list[ClassifiedMeal], before_bed_time: Optional[time]) -> Optional[time]:
    if period == "Before Bed":
        return before_bed_time
    if period == "Around Noon":
        return time(12, 0)
    if period == "After Breaking Fast":
        breakfast = [m.event.at.time() for m in meals if m.label == "Breakfast"]
        return breakfast[0] if breakfast else (meals[0].event.at.time() if meals else None)
    dinner = [m.event.at.time() for m in meals if m.label == "Dinner"]
    return dinner[-1] if dinner else None


def _prompt_before_bed(day_label: str, non_interactive: bool) -> Optional[time]:
    if non_interactive:
        return None
    response = _prompt(f"{day_label} Before Bed time (e.g., 10:00 PM; blank for none): ")
    if not response:
        return None
    try:
        return parse_time_input(response)
    except ValueError:
        print("Invalid time; using Not available.")
        return None


def _prompt_period_fields(day_label: str, period: str, non_interactive: bool) -> tuple[str, str]:
    if non_interactive:
        return "Not provided", "Not provided"
    energy = _prompt(f"{day_label} {period} energy (blank => Not provided): ") or "Not provided"
    mood = _prompt(
        f"{day_label} {period} mood (1-5 scale, where 1=low and 5=great; blank => Not provided): "
    ) or "Not provided"
    return energy, mood


def run_interview(patient_name: str, day_summaries: list[DaySummary], source_pdf: Optional[str], non_interactive: bool) -> WeeklySession:
    if not day_summaries:
        raise ValueError("No day summaries available for interview.")

    ordered = sorted(day_summaries, key=lambda d: d.day, reverse=True)
    interviewed_days: list[DayInterview] = []

    for summary in ordered:
        day_label = fmt_day_heading(summary.day)
        meals = classify_meals(summary=summary, non_interactive=non_interactive)
        before_bed_time = _prompt_before_bed(day_label=day_label, non_interactive=non_interactive)

        checkins: list[PeriodCheckin] = []
        for period in PERIODS:
            anchor = _period_anchor(period=period, meals=meals, before_bed_time=before_bed_time)
            energy, mood = _prompt_period_fields(day_label=day_label, period=period, non_interactive=non_interactive)
            checkins.append(PeriodCheckin(period=period, time_of_day=anchor, energy=energy, mood=mood))

        interviewed_days.append(
            DayInterview(day=summary.day, meals=meals, activity=summary.activity, checkins=checkins)
        )

    start = min(d.day for d in ordered)
    end = max(d.day for d in ordered)
    return WeeklySession(
        patient_name=patient_name,
        start=start,
        end=end,
        days=interviewed_days,
        source_pdf=source_pdf,
    )
