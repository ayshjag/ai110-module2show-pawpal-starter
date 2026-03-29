# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond basic priority ordering, the scheduler includes several logic improvements:

**Sorting**
- `sort_tasks()` orders tasks by priority → preferred time → duration.
- `sort_by_time()` sorts by the `preferred_time` field, supporting both named periods (`"morning"`, `"afternoon"`, `"evening"`) and exact `"HH:MM"` strings — both converted to minutes since midnight for consistent ordering.

**Filtering**
- `filter_by_status(tasks, completed)` — separate done vs. pending tasks.
- `filter_by_category(tasks, category)` — isolate tasks by type (feeding, medication, etc.).
- `filter_by_priority(tasks, priority)` — pull only high/medium/low tasks.
- `filter_by_pet(owner, pet_name)` — get all tasks belonging to a named pet.

**Recurring tasks**
- Every `Task` has a `frequency` field: `"daily"`, `"weekly"`, or `"as-needed"`.
- `Task.is_due_today(weekday)` determines whether a task should appear in today's plan.
- `Task.next_occurrence(today)` uses `timedelta` to clone the task with an updated `due_date` — one day ahead for daily tasks, one week for weekly.
- `Scheduler.mark_complete(task, pet, today)` marks the task done and automatically appends the next occurrence to the pet's task list.

**Conflict detection**
- `detect_conflicts(scheduled)` inspects a built plan and returns human-readable warnings (never crashes).
- Detects three problem types: time overlaps between any two tasks, same-category tasks placed too close together (e.g. two feedings < 2 hours apart), and medication scheduled outside its preferred time window.
- Warnings are attached to `DailyPlan.conflicts` and displayed in `summary()`.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
