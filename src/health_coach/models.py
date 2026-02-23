from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional


@dataclass
class Event:
    event_type: str
    details: str
    at: datetime
    glucose: Optional[int]


@dataclass
class DaySummary:
    day: date
    meals: list[Event]
    activity: list[Event]


@dataclass
class ClassifiedMeal:
    label: str
    event: Event


@dataclass
class PeriodCheckin:
    period: str
    time_of_day: Optional[time]
    energy: str
    mood: str


@dataclass
class DayInterview:
    day: date
    meals: list[ClassifiedMeal]
    activity: list[Event]
    checkins: list[PeriodCheckin]


@dataclass
class WeeklySession:
    patient_name: str
    start: date
    end: date
    days: list[DayInterview]
    source_pdf: Optional[str] = None
