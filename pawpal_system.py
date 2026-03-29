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
from datetime import time
from typing import Literal

Priority = Literal["high", "medium", "low"]
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
TIME_RANK = {"morning": 0, "afternoon": 1, "evening": 2}  # used to sort within same priority


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

Frequency = Literal["daily", "weekly", "as-needed"]

@dataclass
class Task:
    title: str
    duration_minutes: int               # how long the activity takes (the "time" attribute)
    description: str = ""               # longer explanation of what the task involves
    priority: Priority = "medium"
    category: str = "general"
    frequency: Frequency = "daily"      # how often this task recurs
    preferred_time: str | None = None   # "morning", "afternoon", "evening", or None
    completed: bool = False             # whether this task is done for today

    def __post_init__(self):
        """Validate duration and priority on creation."""
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
    tasks: list[Task] = field(default_factory=list)     # care tasks belonging to this pet

    def add_task(self, task: Task) -> None:
        """Append a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove all tasks matching the given title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def pending_tasks(self) -> list[Task]:
        """Return tasks not yet completed today."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int = 120        # total care time available today
    day_start: time = time(7, 0)        # when the owner's day begins
    pets: list[Pet] = field(default_factory=list)   # Owner "1" --> "*" Pet

    def __post_init__(self):
        """Validate that available_minutes is a positive number."""
        if self.available_minutes <= 0:
            raise ValueError("available_minutes must be positive")

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name from this owner's list."""
        self.pets = [p for p in self.pets if p.name != name]

    def all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def all_pending_tasks(self) -> list[Task]:
        """Return incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.pending_tasks()]


@dataclass
class ScheduledTask:
    task: Task
    start_time: time
    end_time: time
    reason: str

    @property
    def duration_minutes(self) -> int:
        """Return the duration of the wrapped task in minutes."""
        return self.task.duration_minutes


@dataclass
class DailyPlan:
    owner: Owner
    pet: Pet
    scheduled: list[ScheduledTask]
    skipped: list[tuple[Task, str]]     # (task, reason_skipped)

    @property
    def total_minutes(self) -> int:
        """Return the total scheduled time in minutes."""
        return sum(s.duration_minutes for s in self.scheduled)

    def summary(self) -> str:
        """Return a formatted text summary of the full plan including skipped tasks."""
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
    The "brain" of PawPal+.

    Responsibilities
    ----------------
    - Retrieve pending tasks from the owner's pets
    - Organise tasks by priority, preferred time, and duration
    - Manage task completion state
    - Build a time-slotted DailyPlan that fits the owner's available time

    Algorithm
    ---------
    1. Pull pending (incomplete) tasks from all of the owner's pets.
    2. Sort: high → medium → low priority; ties broken by preferred time
       (morning → afternoon → evening → none), then shorter duration first.
    3. Walk the sorted list; place each task if time remains.
    4. Record skipped tasks with a human-readable explanation.
    """

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_tasks_for_pet(self, pet: Pet) -> list[Task]:
        """Return all tasks belonging to a specific pet."""
        return pet.tasks

    def get_pending_tasks_for_pet(self, pet: Pet) -> list[Task]:
        """Return incomplete tasks for a specific pet."""
        return pet.pending_tasks()

    def get_all_pending_tasks(self, owner: Owner) -> list[Task]:
        """Return incomplete tasks across every pet the owner has."""
        return owner.all_pending_tasks()

    # ------------------------------------------------------------------
    # Organisation
    # ------------------------------------------------------------------

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority → preferred time → duration."""
        return sorted(
            tasks,
            key=lambda t: (
                PRIORITY_RANK[t.priority],
                TIME_RANK.get(t.preferred_time, 3),
                t.duration_minutes,
            ),
        )

    def tasks_by_priority(self, tasks: list[Task]) -> dict[str, list[Task]]:
        """Group tasks into a dict keyed by priority level."""
        groups: dict[str, list[Task]] = {"high": [], "medium": [], "low": []}
        for task in tasks:
            groups[task.priority].append(task)
        return groups

    def tasks_by_pet(self, owner: Owner) -> dict[str, list[Task]]:
        """Group pending tasks by pet name."""
        return {pet.name: pet.pending_tasks() for pet in owner.pets}

    # ------------------------------------------------------------------
    # Task state management
    # ------------------------------------------------------------------

    def mark_complete(self, task: Task) -> None:
        """Mark a task as done for today."""
        task.completed = True

    def reset_all(self, owner: Owner) -> None:
        """Reset completion status on all tasks (call at the start of a new day)."""
        for task in owner.all_tasks():
            task.completed = False

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def build_plan(self, owner: Owner, pet: Pet, tasks: list[Task] | None = None) -> DailyPlan:
        """
        Build a DailyPlan for one pet.

        If tasks is None, pending tasks are pulled automatically from pet.
        Pass an explicit list to override (e.g. for testing or custom filtering).
        """
        task_list = tasks if tasks is not None else pet.pending_tasks()

        if not task_list:
            return DailyPlan(owner=owner, pet=pet, scheduled=[], skipped=[])

        sorted_tasks = self.sort_tasks(task_list)

        budget = owner.available_minutes
        cursor = _to_minutes(owner.day_start)
        scheduled: list[ScheduledTask] = []
        skipped: list[tuple[Task, str]] = []

        for task in sorted_tasks:
            if task.duration_minutes > budget:
                skipped.append((
                    task,
                    f"not enough time remaining ({budget} min left, needs {task.duration_minutes} min)",
                ))
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
        """Build a plain-language explanation of why and when a task was scheduled."""
        priority_label = {
            "high": "high priority — scheduled first",
            "medium": "medium priority",
            "low": "low priority — scheduled if time allows",
        }[task.priority]

        parts = [priority_label]

        if position == 0:
            parts.append("placed at the start of the day")
        if task.preferred_time:
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
    """Convert a time object to total minutes since midnight."""
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    """Convert total minutes since midnight back to a time object."""
    m = m % (24 * 60)
    return time(m // 60, m % 60)


def _fmt(t: time) -> str:
    """Format a time object as a readable 12-hour string (e.g. 7:05 AM)."""
    suffix = "AM" if t.hour < 12 else "PM"
    hour = t.hour % 12 or 12
    return f"{hour}:{t.minute:02d} {suffix}"
