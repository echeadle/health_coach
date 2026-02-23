#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

import streamlit as st

from health_coach.interview import PERIODS, infer_meal_label
from health_coach.models import ClassifiedMeal, DayInterview, PeriodCheckin, WeeklySession
from health_coach.tools import choose_days, parse_clarity_pdf, render_outputs, save_outputs

MEAL_LABELS = ["Breakfast", "Lunch", "Dinner", "Snack"]


def _parse_time_or_none(value: str) -> time | None:
    text = value.strip().upper()
    if not text:
        return None
    return datetime.strptime(text, "%I:%M %p").time()


def _period_anchor(period: str, meals: list[ClassifiedMeal], before_bed_time: time | None) -> time | None:
    if period == "Before Bed":
        return before_bed_time
    if period == "Around Noon":
        return time(12, 0)
    if period == "After Breaking Fast":
        breakfast = [m.event.at.time() for m in meals if m.label == "Breakfast"]
        return breakfast[0] if breakfast else (meals[0].event.at.time() if meals else None)
    dinner = [m.event.at.time() for m in meals if m.label == "Dinner"]
    return dinner[-1] if dinner else None


def _persist_uploaded_pdf(inbox_dir: Path, name: str, data: bytes) -> Path:
    inbox_dir.mkdir(parents=True, exist_ok=True)
    target = inbox_dir / name
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = inbox_dir / f"{stem}_{ts}{suffix}"
    target.write_bytes(data)
    return target


def main() -> None:
    st.set_page_config(page_title="Health Coach Agent", page_icon=":clipboard:", layout="wide")
    st.title("Health Coach Agent")
    st.caption("Upload Clarity PDF, answer guided questions, and generate report + mood worksheet.")

    with st.sidebar:
        st.header("Settings")
        inbox_dir = Path(st.text_input("Inbox directory", value="Clarity_Inbox"))
        reports_dir = Path(st.text_input("Reports directory", value="Reports"))
        archive_dir = Path(st.text_input("Archive directory", value="Clarity_Reports"))
        patient_override = st.text_input("Patient name override (optional)", value="")

    uploaded = st.file_uploader("Upload Clarity PDF", type=["pdf"])
    if uploaded and st.button("Load PDF", type="primary"):
        pdf_path = _persist_uploaded_pdf(inbox_dir, uploaded.name, uploaded.getvalue())
        patient_name, day_summaries = parse_clarity_pdf(pdf_path)
        st.session_state["pdf_path"] = str(pdf_path)
        st.session_state["patient_name"] = patient_name
        st.session_state["day_summaries"] = day_summaries
        st.success(f"Loaded {uploaded.name}")

    if "day_summaries" not in st.session_state:
        st.info("Upload and load a PDF to begin.")
        return

    day_summaries = st.session_state["day_summaries"]
    available = [d.day.isoformat() for d in day_summaries]
    default_days = available
    selected_day_labels = st.multiselect("What day or days do you want to work on?", options=available, default=default_days)

    if not selected_day_labels:
        st.warning("Select at least one day.")
        return

    selected_days = [datetime.strptime(item, "%Y-%m-%d").date() for item in selected_day_labels]
    selected = choose_days(day_summaries=day_summaries, selected_days=selected_days)

    st.divider()
    for summary in selected:
        st.subheader(summary.day.strftime("%A, %b %d, %Y"))
        st.markdown("**Meal Classification**")
        for i, meal in enumerate(summary.meals):
            key = f"meal_label_{summary.day.isoformat()}_{i}"
            default = infer_meal_label(meal.at.time())
            if key not in st.session_state:
                st.session_state[key] = default
            st.selectbox(
                f"{meal.at.strftime('%I:%M %p')} - {meal.details}",
                MEAL_LABELS,
                key=key,
            )

        before_bed_key = f"before_bed_{summary.day.isoformat()}"
        st.text_input(
            "Before Bed time (e.g., 10:00 PM)",
            key=before_bed_key,
            placeholder="Optional",
        )

        st.markdown("**Period Check-ins**")
        for period in PERIODS:
            cols = st.columns(2)
            with cols[0]:
                st.text_input(
                    f"{period} Energy",
                    key=f"energy_{summary.day.isoformat()}_{period}",
                    placeholder="Not provided",
                )
            with cols[1]:
                st.text_input(
                    f"{period} Mood",
                    key=f"mood_{summary.day.isoformat()}_{period}",
                    placeholder="1-5 scale (1=low, 5=great)",
                    help="Use 1-5 scale as reminder.",
                )
        st.divider()

    if st.button("Generate Report + Worksheet", type="primary"):
        day_interviews: list[DayInterview] = []
        for summary in selected:
            classified_meals: list[ClassifiedMeal] = []
            for i, meal in enumerate(summary.meals):
                label = st.session_state.get(f"meal_label_{summary.day.isoformat()}_{i}", infer_meal_label(meal.at.time()))
                classified_meals.append(ClassifiedMeal(label=label, event=meal))

            before_bed_raw = st.session_state.get(f"before_bed_{summary.day.isoformat()}", "")
            try:
                before_bed_time = _parse_time_or_none(before_bed_raw)
            except ValueError:
                st.error(f"Invalid before-bed time for {summary.day.isoformat()}. Use format like 10:00 PM.")
                return

            checkins: list[PeriodCheckin] = []
            for period in PERIODS:
                energy = st.session_state.get(f"energy_{summary.day.isoformat()}_{period}", "").strip() or "Not provided"
                mood = st.session_state.get(f"mood_{summary.day.isoformat()}_{period}", "").strip() or "Not provided"
                checkins.append(
                    PeriodCheckin(
                        period=period,
                        time_of_day=_period_anchor(period=period, meals=classified_meals, before_bed_time=before_bed_time),
                        energy=energy,
                        mood=mood,
                    )
                )

            day_interviews.append(
                DayInterview(
                    day=summary.day,
                    meals=classified_meals,
                    activity=summary.activity,
                    checkins=checkins,
                )
            )

        patient_name = patient_override.strip() or st.session_state.get("patient_name", "Unknown Patient")
        ordered = sorted(day_interviews, key=lambda d: d.day, reverse=True)
        session = WeeklySession(
            patient_name=patient_name,
            start=min(d.day for d in ordered),
            end=max(d.day for d in ordered),
            days=ordered,
            source_pdf=Path(st.session_state["pdf_path"]).name,
        )

        report_text, worksheet_text = render_outputs(session=session)
        outputs = save_outputs(
            session=session,
            report_text=report_text,
            worksheet_text=worksheet_text,
            reports_dir=reports_dir,
            archive_dir=archive_dir,
            source_pdf=Path(st.session_state["pdf_path"]),
        )

        st.success("Generated outputs successfully.")
        st.write(f"Report: `{outputs['report']}`")
        st.write(f"Mood worksheet: `{outputs['worksheet']}`")
        st.write(f"Session artifact: `{outputs['session']}`")
        if "archive" in outputs:
            st.write(f"Archived PDF: `{outputs['archive']}`")

        st.download_button("Download report markdown", data=report_text, file_name=outputs["report"].name)
        st.download_button("Download mood worksheet", data=worksheet_text, file_name=outputs["worksheet"].name)


if __name__ == "__main__":
    main()
