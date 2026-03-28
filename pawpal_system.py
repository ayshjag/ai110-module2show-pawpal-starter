"""
PawPal+ core system: data model + scheduling logic.

Classes
-------
Task            - a single care activity (walk, feed, meds, …)
Pet             - the animal being cared for
Owner           - the person doing the caring (holds daily constraints)
ScheduledTask   - a Task placed at a specific start time with reasoning
DailyPlan       - the full ordered schedule for one day
Scheduler       - produces a DailyPlan from an Owner, Pet, and task list
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time, timedelta, datetime
from typing import Literal

Priority = Literal["high", "medium", "low"]
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = "medium"
    category: str = "general"
    preferred_time: str | None = None   # "morning", "afternoon", "evening", or None

    def __post_init__(self):
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")


@dataclass
class Pet:
    name: str
    species: str = "dog"
    age_years: float = 1.0
    special_needs: list[str] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    available_minutes: int = 120        # total care time available today
    day_start: time = time(7, 0)        # when the owner's day begins

    def __post_init__(self):
        if self.available_minutes <= 0:
            raise ValueError("available_minutes must be positive")


@dataclass
class ScheduledTask:
    task: Task
    start_time: time
    end_time: time
    reason: str

    @property
    def duration_minutes(self) -> int:
        return self.task.duration_minutes


@dataclass
class DailyPlan:
    owner: Owner
    pet: Pet
    scheduled: list[ScheduledTask]
    skipped: list[tuple[Task, str]]     # (task, reason_skipped)

    @property
    def total_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.scheduled)

    def summary(self) -> str:
        lines = [
            f"Daily plan for {self.owner.name} and {self.pet.name}",
            f"Total scheduled: {self.total_minutes} min / {self.owner.available_minutes} min available",
            "",
        ]
        if self.scheduled:
            lines.append("Schedule:")
            for s in self.scheduled:
                lines.append(
                    f"  {_fmt(s.start_time)}–{_fmt(s.end_time)}  "
                    f"[{s.task.priority.upper()}] {s.task.title}  ({s.task.duration_minutes} min)"
                )
                lines.append(f"    → {s.reason}")
        else:
            lines.append("No tasks could be scheduled.")

        if self.skipped:
            lines.append("")
            lines.append("Skipped:")
            for task, reason in self.skipped:
                lines.append(f"  ✗ {task.title}: {reason}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Greedy priority-first scheduler.

    Algorithm
    ---------
    1. Sort tasks: high → medium → low; ties broken by duration (shorter first).
    2. Walk through the sorted list; place each task if time remains.
    3. Record skipped tasks with a human-readable explanation.
    """

    def build_plan(self, owner: Owner, pet: Pet, tasks: list[Task]) -> DailyPlan:
        if not tasks:
            return DailyPlan(owner=owner, pet=pet, scheduled=[], skipped=[])

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (PRIORITY_RANK[t.priority], t.duration_minutes),
        )

        budget = owner.available_minutes
        cursor = _to_minutes(owner.day_start)
        scheduled: list[ScheduledTask] = []
        skipped: list[tuple[Task, str]] = []

        for task in sorted_tasks:
            if task.duration_minutes > budget:
                skipped.append(
                    (
                        task,
                        f"not enough time remaining ({budget} min left, needs {task.duration_minutes} min)",
                    )
                )
                continue

            start = _from_minutes(cursor)
            end = _from_minutes(cursor + task.duration_minutes)
            reason = self._reason(task, pet, len(scheduled))

            scheduled.append(ScheduledTask(task=task, start_time=start, end_time=end, reason=reason))
            cursor += task.duration_minutes
            budget -= task.duration_minutes

        return DailyPlan(owner=owner, pet=pet, scheduled=scheduled, skipped=skipped)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reason(self, task: Task, pet: Pet, position: int) -> str:
        priority_label = {
            "high": "high priority — scheduled first",
            "medium": "medium priority",
            "low": "low priority — scheduled if time allows",
        }[task.priority]

        parts = [priority_label]

        if position == 0:
            parts.append("placed at the start of the day")
        elif task.preferred_time:
            parts.append(f"preferred time: {task.preferred_time}")

        if task.category == "medication":
            parts.append("medication tasks are time-sensitive")
        elif task.category == "feeding":
            parts.append("regular feeding keeps energy stable")
        elif task.category == "exercise":
            parts.append(f"exercise supports {pet.name}'s health")

        if pet.special_needs:
            for need in pet.special_needs:
                if need.lower() in task.title.lower() or need.lower() in task.category.lower():
                    parts.append(f"required by {pet.name}'s special need: {need}")

        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Private utilities
# ---------------------------------------------------------------------------

def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    m = m % (24 * 60)
    return time(m // 60, m % 60)


def _fmt(t: time) -> str:
    suffix = "AM" if t.hour < 12 else "PM"
    hour = t.hour % 12 or 12
    return f"{hour}:{t.minute:02d} {suffix}"
