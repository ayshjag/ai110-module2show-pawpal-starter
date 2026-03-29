"""Tests for PawPal+ scheduling logic."""
import pytest
from datetime import time, date
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan, ScheduledTask


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


# ---------------------------------------------------------------------------
# Sorting — sort_by_time()
# ---------------------------------------------------------------------------

def test_sort_by_time_named_periods(scheduler):
    """Named periods should sort morning < afternoon < evening."""
    tasks = [
        Task(title="Evening", duration_minutes=10, preferred_time="evening"),
        Task(title="Morning", duration_minutes=10, preferred_time="morning"),
        Task(title="Afternoon", duration_minutes=10, preferred_time="afternoon"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    titles = [t.title for t in sorted_tasks]
    assert titles == ["Morning", "Afternoon", "Evening"]


def test_sort_by_time_hhmm_strings(scheduler):
    """HH:MM strings should sort chronologically."""
    tasks = [
        Task(title="Late",  duration_minutes=10, preferred_time="14:00"),
        Task(title="Early", duration_minutes=10, preferred_time="07:30"),
        Task(title="Mid",   duration_minutes=10, preferred_time="10:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    titles = [t.title for t in sorted_tasks]
    assert titles == ["Early", "Mid", "Late"]


def test_sort_by_time_no_preference_sorts_last(scheduler):
    """Tasks with no preferred_time should appear after all others."""
    tasks = [
        Task(title="No pref",  duration_minutes=10),
        Task(title="Morning",  duration_minutes=10, preferred_time="morning"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert sorted_tasks[0].title == "Morning"
    assert sorted_tasks[-1].title == "No pref"


def test_sort_by_time_mixed_formats(scheduler):
    """HH:MM values should slot correctly between named periods."""
    tasks = [
        Task(title="Afternoon", duration_minutes=10, preferred_time="afternoon"),
        Task(title="08:00",     duration_minutes=10, preferred_time="08:00"),
        Task(title="Morning",   duration_minutes=10, preferred_time="morning"),
        Task(title="13:00",     duration_minutes=10, preferred_time="13:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    titles = [t.title for t in sorted_tasks]
    # morning(0) < 08:00(480) < afternoon(720) < 13:00(780)
    assert titles.index("Morning") < titles.index("08:00")
    assert titles.index("08:00") < titles.index("Afternoon")
    assert titles.index("Afternoon") < titles.index("13:00")


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_by_status_pending(scheduler, pet):
    """filter_by_status(completed=False) returns only incomplete tasks."""
    done = Task(title="Done", duration_minutes=10)
    done.completed = True
    pet.add_task(done)
    pet.add_task(Task(title="Pending", duration_minutes=10))
    result = scheduler.filter_by_status(pet.tasks, completed=False)
    assert all(not t.completed for t in result)
    assert len(result) == 1


def test_filter_by_status_completed(scheduler, pet):
    """filter_by_status(completed=True) returns only completed tasks."""
    done = Task(title="Done", duration_minutes=10)
    done.completed = True
    pet.add_task(done)
    pet.add_task(Task(title="Pending", duration_minutes=10))
    result = scheduler.filter_by_status(pet.tasks, completed=True)
    assert all(t.completed for t in result)
    assert len(result) == 1


def test_filter_by_category(scheduler, pet):
    """filter_by_category returns only tasks of the given category."""
    pet.add_task(Task(title="Walk",     duration_minutes=30, category="exercise"))
    pet.add_task(Task(title="Feed",     duration_minutes=10, category="feeding"))
    pet.add_task(Task(title="Grooming", duration_minutes=15, category="grooming"))
    result = scheduler.filter_by_category(pet.tasks, "exercise")
    assert len(result) == 1
    assert result[0].title == "Walk"


def test_filter_by_priority(scheduler, pet):
    """filter_by_priority returns only tasks of the given priority."""
    pet.add_task(Task(title="High task",   duration_minutes=10, priority="high"))
    pet.add_task(Task(title="Medium task", duration_minutes=10, priority="medium"))
    pet.add_task(Task(title="Low task",    duration_minutes=10, priority="low"))
    highs = scheduler.filter_by_priority(pet.tasks, "high")
    assert len(highs) == 1
    assert highs[0].title == "High task"


def test_filter_by_pet_returns_correct_tasks(scheduler, owner):
    """filter_by_pet returns tasks belonging to the named pet only."""
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Whisker", species="cat")
    dog.add_task(Task(title="Walk",    duration_minutes=20))
    cat.add_task(Task(title="Feeding", duration_minutes=5))
    owner.add_pet(dog)
    owner.add_pet(cat)
    result = scheduler.filter_by_pet(owner, "Mochi")
    assert len(result) == 1
    assert result[0].title == "Walk"


def test_filter_by_pet_unknown_name_returns_empty(scheduler, owner):
    """filter_by_pet returns [] for a pet name that doesn't exist."""
    assert scheduler.filter_by_pet(owner, "Ghost") == []


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------

def test_daily_task_is_due_every_day():
    """A daily task is due on every weekday."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")
    for weekday in range(7):
        assert task.is_due_today(weekday) is True


def test_weekly_task_is_due_only_on_specified_days():
    """A weekly task is due only on its configured days_of_week."""
    task = Task(title="Bath", duration_minutes=20, frequency="weekly", days_of_week=[0, 3])
    assert task.is_due_today(0) is True   # Monday
    assert task.is_due_today(3) is True   # Thursday
    assert task.is_due_today(1) is False  # Tuesday


def test_as_needed_task_is_never_auto_due():
    """An as-needed task is never automatically due."""
    task = Task(title="Vet", duration_minutes=60, frequency="as-needed")
    for weekday in range(7):
        assert task.is_due_today(weekday) is False


def test_next_occurrence_daily_advances_one_day():
    """Daily task next_occurrence returns due_date = today + 1 day."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")
    today = date(2026, 3, 29)
    next_task = task.next_occurrence(today)
    assert next_task is not None
    assert next_task.due_date == date(2026, 3, 30)
    assert next_task.completed is False


def test_next_occurrence_weekly_advances_seven_days():
    """Weekly task next_occurrence returns due_date = today + 7 days."""
    task = Task(title="Bath", duration_minutes=20, frequency="weekly")
    today = date(2026, 3, 29)
    next_task = task.next_occurrence(today)
    assert next_task is not None
    assert next_task.due_date == date(2026, 4, 5)


def test_next_occurrence_as_needed_returns_none():
    """As-needed tasks should not auto-recur."""
    task = Task(title="Vet", duration_minutes=60, frequency="as-needed")
    assert task.next_occurrence(date(2026, 3, 29)) is None


def test_next_occurrence_does_not_mutate_original():
    """next_occurrence() must not modify the original task."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")
    task.next_occurrence(date(2026, 3, 29))
    assert task.completed is False
    assert task.due_date is None


def test_mark_complete_with_pet_and_today_appends_next_occurrence(scheduler, pet):
    """mark_complete() with pet + today should add a new task to the pet."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")
    pet.add_task(task)
    today = date(2026, 3, 29)
    next_task = scheduler.mark_complete(task, pet=pet, today=today)
    assert task.completed is True
    assert next_task is not None
    assert next_task in pet.tasks
    assert next_task.due_date == date(2026, 3, 30)


def test_mark_complete_without_today_does_not_create_recurrence(scheduler, pet):
    """mark_complete() without today should not create a next occurrence."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")
    pet.add_task(task)
    result = scheduler.mark_complete(task, pet=pet)
    assert result is None
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_no_conflicts_for_sequential_tasks(owner, pet, scheduler):
    """Sequential non-overlapping tasks should produce no conflicts."""
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=10, priority="medium"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert plan.conflicts == []


def test_detect_overlap_between_manually_placed_tasks(scheduler):
    """Two tasks sharing a time window should trigger an overlap warning."""
    walk    = Task(title="Walk",    duration_minutes=30)
    feeding = Task(title="Feeding", duration_minutes=15)
    overlapping = [
        ScheduledTask(task=walk,    start_time=time(8, 0),  end_time=time(8, 30), reason=""),
        ScheduledTask(task=feeding, start_time=time(8, 15), end_time=time(8, 30), reason=""),
    ]
    conflicts = scheduler.detect_conflicts(overlapping)
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]


def test_detect_same_category_too_close(owner, pet, scheduler):
    """Two feeding tasks placed within 2 hours should trigger a proximity warning."""
    tasks = [
        Task(title="First feed",  duration_minutes=10, priority="high", category="feeding"),
        Task(title="Second feed", duration_minutes=10, priority="high", category="feeding"),
    ]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert any("too close" in w.lower() or "close" in w.lower() for w in plan.conflicts)


def test_detect_medication_outside_preferred_window(scheduler):
    """Medication scheduled outside its preferred window should raise a warning."""
    from datetime import time as dtime
    meds = Task(title="Evening meds", duration_minutes=5, category="medication", preferred_time="evening")
    scheduled = [
        ScheduledTask(task=meds, start_time=dtime(8, 0), end_time=dtime(8, 5), reason="")
    ]
    conflicts = scheduler.detect_conflicts(scheduled)
    assert any("evening" in w.lower() for w in conflicts)


def test_no_conflict_for_medication_in_correct_window(scheduler):
    """Medication scheduled inside its preferred window should produce no warning."""
    from datetime import time as dtime
    meds = Task(title="Morning meds", duration_minutes=5, category="medication", preferred_time="morning")
    scheduled = [
        ScheduledTask(task=meds, start_time=dtime(8, 0), end_time=dtime(8, 5), reason="")
    ]
    conflicts = scheduler.detect_conflicts(scheduled)
    assert conflicts == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_returns_empty_plan(owner, scheduler):
    """A pet with zero tasks should produce an empty plan with no errors."""
    pet = Pet(name="Ghost", species="cat")
    plan = scheduler.build_plan(owner, pet)
    assert plan.scheduled == []
    assert plan.skipped == []
    assert plan.conflicts == []


def test_pet_with_all_tasks_completed_returns_empty_plan(owner, scheduler):
    """A pet whose every task is done should schedule nothing."""
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=20)
    task.completed = True
    pet.add_task(task)
    plan = scheduler.build_plan(owner, pet)
    assert plan.scheduled == []


def test_task_duration_exactly_equals_budget(scheduler):
    """A task whose duration exactly matches the budget should be scheduled, not skipped."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    tasks = [Task(title="Exact fit", duration_minutes=30, priority="high")]
    plan = scheduler.build_plan(owner, pet, tasks)
    assert len(plan.scheduled) == 1
    assert plan.skipped == []


def test_conflict_detection_on_empty_schedule(scheduler):
    """An empty scheduled list should produce no conflict warnings."""
    assert scheduler.detect_conflicts([]) == []


def test_conflict_detection_single_task_no_conflict(scheduler):
    """A single scheduled task can never conflict with itself."""
    task = Task(title="Walk", duration_minutes=30)
    scheduled = [ScheduledTask(task=task, start_time=time(8, 0), end_time=time(8, 30), reason="")]
    assert scheduler.detect_conflicts(scheduled) == []


def test_filter_by_category_no_match_returns_empty(scheduler, pet):
    """filter_by_category returns [] when no tasks match the category."""
    pet.add_task(Task(title="Walk", duration_minutes=20, category="exercise"))
    result = scheduler.filter_by_category(pet.tasks, "medication")
    assert result == []


def test_owner_with_no_pets_returns_empty_task_list(owner):
    """An owner with no pets should have no tasks."""
    assert owner.all_tasks() == []
    assert owner.all_pending_tasks() == []


def test_next_occurrence_preserves_all_task_attributes():
    """next_occurrence() should copy all attributes except due_date and completed."""
    task = Task(
        title="Walk", duration_minutes=30, priority="high",
        category="exercise", preferred_time="morning", frequency="daily",
        description="Slow walk", days_of_week=[0, 1, 2]
    )
    next_task = task.next_occurrence(date(2026, 3, 29))
    assert next_task.title == task.title
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.priority == task.priority
    assert next_task.category == task.category
    assert next_task.preferred_time == task.preferred_time
    assert next_task.description == task.description
    assert next_task.days_of_week == task.days_of_week
    assert next_task.completed is False


def test_sort_by_time_single_task_returns_that_task(scheduler):
    """sort_by_time on a single-task list should return that task unchanged."""
    task = Task(title="Walk", duration_minutes=20, preferred_time="morning")
    result = scheduler.sort_by_time([task])
    assert result == [task]


def test_weekly_task_not_due_today_excluded_from_due_today(scheduler):
    """due_today() should exclude a weekly task not scheduled for today's weekday."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    # Only due on Monday (0) and Friday (4)
    task = Task(title="Bath", duration_minutes=20, frequency="weekly", days_of_week=[0, 4])
    pet.add_task(task)
    owner.add_pet(pet)
    # Tuesday = weekday 1 — should not appear
    due = scheduler.due_today(owner, weekday=1)
    assert task not in due
