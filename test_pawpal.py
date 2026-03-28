"""Tests for PawPal+ scheduling logic."""
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan, PRIORITY_RANK


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner():
    return Owner(name="Jordan", available_minutes=90)


@pytest.fixture
def pet():
    return Pet(name="Mochi", species="dog")


@pytest.fixture
def scheduler():
    return Scheduler()


# ---------------------------------------------------------------------------
# Task validation
# ---------------------------------------------------------------------------

def test_task_rejects_zero_duration():
    with pytest.raises(ValueError):
        Task(title="Bad", duration_minutes=0)


def test_task_rejects_invalid_priority():
    with pytest.raises(ValueError):
        Task(title="Bad", duration_minutes=10, priority="urgent")


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

def test_no_tasks_returns_empty_plan(owner, pet, scheduler):
    plan = scheduler.build_plan(owner, pet, [])
    assert plan.scheduled == []
    assert plan.skipped == []


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

def test_high_priority_scheduled_before_low(owner, pet, scheduler):
    tasks = [
        Task(title="Low task", duration_minutes=10, priority="low"),
        Task(title="High task", duration_minutes=10, priority="high"),
        Task(title="Medium task", duration_minutes=10, priority="medium"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    titles = [s.task.title for s in plan.scheduled]
    assert titles.index("High task") < titles.index("Medium task")
    assert titles.index("Medium task") < titles.index("Low task")


# ---------------------------------------------------------------------------
# Time budget enforcement
# ---------------------------------------------------------------------------

def test_tasks_within_budget_are_all_scheduled(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=60)
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=15, priority="high"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert len(plan.scheduled) == 2
    assert plan.skipped == []


def test_task_exceeding_budget_is_skipped(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=20)
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert len(plan.scheduled) == 0
    assert len(plan.skipped) == 1
    assert plan.skipped[0][0].title == "Walk"


def test_total_scheduled_minutes_never_exceed_budget(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=45)
    tasks = [
        Task(title="Task A", duration_minutes=20, priority="high"),
        Task(title="Task B", duration_minutes=20, priority="medium"),
        Task(title="Task C", duration_minutes=20, priority="low"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert plan.total_minutes <= owner.available_minutes


# ---------------------------------------------------------------------------
# Sequential time assignment
# ---------------------------------------------------------------------------

def test_scheduled_times_are_sequential(pet, scheduler):
    from datetime import time as dtime
    owner = Owner(name="Jordan", available_minutes=120, day_start=dtime(8, 0))
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=15, priority="medium"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert len(plan.scheduled) == 2
    first, second = plan.scheduled
    assert first.start_time == dtime(8, 0)
    assert first.end_time == dtime(8, 30)
    assert second.start_time == dtime(8, 30)


# ---------------------------------------------------------------------------
# Tie-breaking: shorter tasks first within same priority
# ---------------------------------------------------------------------------

def test_shorter_task_scheduled_first_within_same_priority(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=120)
    tasks = [
        Task(title="Long high", duration_minutes=40, priority="high"),
        Task(title="Short high", duration_minutes=10, priority="high"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    titles = [s.task.title for s in plan.scheduled]
    assert titles[0] == "Short high"


# ---------------------------------------------------------------------------
# Plan summary
# ---------------------------------------------------------------------------

def test_summary_contains_owner_and_pet_names(owner, pet, scheduler):
    tasks = [Task(title="Walk", duration_minutes=20, priority="high")]
    plan = scheduler.build_plan(owner, pet, tasks)
    summary = plan.summary()
    assert "Jordan" in summary
    assert "Mochi" in summary


def test_summary_lists_skipped_tasks(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=10)
    tasks = [Task(title="Long walk", duration_minutes=60, priority="high")]
    plan = scheduler.build_plan(owner, pet, tasks)
    summary = plan.summary()
    assert "Long walk" in summary
    assert "Skipped" in summary
