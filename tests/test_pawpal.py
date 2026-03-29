"""Tests for PawPal+ scheduling logic."""
import pytest
from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner():
    return Owner(name="Jordan", available_minutes=90, day_start=time(7, 0))


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


def test_task_defaults_are_sensible():
    task = Task(title="Walk", duration_minutes=20)
    assert task.priority == "medium"
    assert task.category == "general"
    assert task.completed is False
    assert task.frequency == "daily"


# ---------------------------------------------------------------------------
# Pet task management
# ---------------------------------------------------------------------------

def test_pet_add_task(pet):
    task = Task(title="Walk", duration_minutes=20, priority="high")
    pet.add_task(task)
    assert task in pet.tasks


def test_pet_remove_task(pet):
    pet.add_task(Task(title="Walk", duration_minutes=20))
    pet.remove_task("Walk")
    assert all(t.title != "Walk" for t in pet.tasks)


def test_pet_pending_tasks_excludes_completed(pet):
    task = Task(title="Walk", duration_minutes=20)
    task.completed = True
    pet.add_task(task)
    pet.add_task(Task(title="Feed", duration_minutes=10))
    assert len(pet.pending_tasks()) == 1
    assert pet.pending_tasks()[0].title == "Feed"


# ---------------------------------------------------------------------------
# Owner pet management
# ---------------------------------------------------------------------------

def test_owner_add_pet(owner, pet):
    owner.add_pet(pet)
    assert pet in owner.pets


def test_owner_remove_pet(owner, pet):
    owner.add_pet(pet)
    owner.remove_pet("Mochi")
    assert all(p.name != "Mochi" for p in owner.pets)


def test_owner_all_tasks_spans_all_pets(owner):
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Whisker", species="cat")
    dog.add_task(Task(title="Walk", duration_minutes=20))
    cat.add_task(Task(title="Feeding", duration_minutes=5))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.all_tasks()) == 2


def test_owner_all_pending_tasks_excludes_completed(owner):
    dog = Pet(name="Mochi", species="dog")
    done = Task(title="Walk", duration_minutes=20)
    done.completed = True
    dog.add_task(done)
    dog.add_task(Task(title="Feed", duration_minutes=10))
    owner.add_pet(dog)
    assert len(owner.all_pending_tasks()) == 1


# ---------------------------------------------------------------------------
# Scheduler — priority ordering
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


def test_preferred_time_orders_within_same_priority(owner, pet, scheduler):
    tasks = [
        Task(title="Evening task", duration_minutes=10, priority="high", preferred_time="evening"),
        Task(title="Morning task", duration_minutes=10, priority="high", preferred_time="morning"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    titles = [s.task.title for s in plan.scheduled]
    assert titles.index("Morning task") < titles.index("Evening task")


# ---------------------------------------------------------------------------
# Scheduler — time budget
# ---------------------------------------------------------------------------

def test_tasks_within_budget_all_scheduled(pet, scheduler):
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
    tasks = [Task(title="Long walk", duration_minutes=60, priority="high")]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert len(plan.scheduled) == 0
    assert len(plan.skipped) == 1


def test_total_scheduled_minutes_never_exceed_budget(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=45)
    tasks = [
        Task(title="A", duration_minutes=20, priority="high"),
        Task(title="B", duration_minutes=20, priority="medium"),
        Task(title="C", duration_minutes=20, priority="low"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert plan.total_minutes <= owner.available_minutes


# ---------------------------------------------------------------------------
# Scheduler — sequential time slots
# ---------------------------------------------------------------------------

def test_scheduled_times_are_sequential(pet, scheduler):
    owner = Owner(name="Jordan", available_minutes=120, day_start=time(8, 0))
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=15, priority="medium"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    first, second = plan.scheduled
    assert first.start_time == time(8, 0)
    assert first.end_time == time(8, 30)
    assert second.start_time == time(8, 30)


# ---------------------------------------------------------------------------
# Scheduler — state management
# ---------------------------------------------------------------------------

def test_mark_complete_excludes_task_from_next_plan(owner, pet, scheduler):
    task = Task(title="Walk", duration_minutes=20, priority="high")
    pet.add_task(task)
    pet.add_task(Task(title="Feed", duration_minutes=10, priority="medium"))
    scheduler.mark_complete(task)
    plan = scheduler.build_plan(owner, pet)
    titles = [s.task.title for s in plan.scheduled]
    assert "Walk" not in titles
    assert "Feed" in titles


def test_reset_all_restores_all_tasks(owner, scheduler):
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=20)
    task.completed = True
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler.reset_all(owner)
    assert task.completed is False


# ---------------------------------------------------------------------------
# Two focused tests (task completion + task addition)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_task_status(scheduler):
    """mark_complete() should set task.completed to True."""
    task = Task(title="Walk", duration_minutes=20)
    assert task.completed is False
    scheduler.mark_complete(task)
    assert task.completed is True


def test_adding_task_increases_pet_task_count(pet):
    """add_task() should increase the pet's task list by one each time."""
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Walk", duration_minutes=20))
    assert len(pet.tasks) == 1
    pet.add_task(Task(title="Feed", duration_minutes=10))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Scheduler — empty input
# ---------------------------------------------------------------------------

def test_no_tasks_returns_empty_plan(owner, pet, scheduler):
    plan = scheduler.build_plan(owner, pet, [])
    assert plan.scheduled == []
    assert plan.skipped == []


def test_build_plan_without_explicit_tasks_uses_pet_tasks(owner, scheduler):
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    plan = scheduler.build_plan(owner, pet)
    assert len(plan.scheduled) == 1
    assert plan.scheduled[0].task.title == "Walk"


# ---------------------------------------------------------------------------
# DailyPlan summary
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
    assert "Long walk" in plan.summary()
    assert "Skipped" in plan.summary()
