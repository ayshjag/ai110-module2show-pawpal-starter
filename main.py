"""
main.py — run a quick demo of the PawPal+ scheduling system.
Usage: python main.py
"""

# 1. Import classes from pawpal_system.py
from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler

# 2. Create an Owner and two Pets
jordan = Owner(name="Jordan", available_minutes=90, day_start=time(7, 0))

mochi = Pet(name="Mochi", species="dog", age_years=3.0, special_needs=["joint support"])
whisker = Pet(name="Whisker", species="cat", age_years=5.0)

jordan.add_pet(mochi)
jordan.add_pet(whisker)

# 3. Add tasks with different preferred times to each pet
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    category="exercise",
    preferred_time="morning",
))
mochi.add_task(Task(
    title="Joint supplement",
    duration_minutes=5,
    priority="high",
    category="medication",
    preferred_time="morning",
))
mochi.add_task(Task(
    title="Enrichment toy",
    duration_minutes=15,
    priority="low",
    category="enrichment",
    preferred_time="afternoon",
))

whisker.add_task(Task(
    title="Breakfast",
    duration_minutes=5,
    priority="high",
    category="feeding",
    preferred_time="morning",
))
whisker.add_task(Task(
    title="Grooming",
    duration_minutes=10,
    priority="medium",
    category="grooming",
    preferred_time="evening",
))

# 4. Print Today's Schedule for each pet
scheduler = Scheduler()

print("=" * 60)
print(f"  TODAY'S SCHEDULE  —  Owner: {jordan.name}")
print("=" * 60)

for pet in jordan.pets:
    plan = scheduler.build_plan(jordan, pet)
    print()
    print(f"🐾 {pet.name} ({pet.species})")
    print("-" * 40)
    if plan.scheduled:
        for s in plan.scheduled:
            print(f"  {s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}"
                  f"  [{s.task.priority.upper()}]  {s.task.title}")
    else:
        print("  No tasks scheduled.")

    if plan.skipped:
        print("  Skipped:")
        for task, reason in plan.skipped:
            print(f"    ✗ {task.title}: {reason}")

print()
print("=" * 60)
