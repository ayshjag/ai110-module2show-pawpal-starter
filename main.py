"""
main.py — demo of conflict detection in PawPal+.
Usage: python main.py
"""

from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask

scheduler = Scheduler()

# ---------------------------------------------------------------------------
# Scenario 1: Normal schedule — no conflicts
# ---------------------------------------------------------------------------

print("=" * 60)
print("SCENARIO 1: Normal schedule (no conflicts)")
print("=" * 60)

jordan = Owner(name="Jordan", available_minutes=120, day_start=time(7, 0))
mochi  = Pet(name="Mochi", species="dog")
jordan.add_pet(mochi)

mochi.add_task(Task(title="Morning walk",     duration_minutes=30, priority="high",   category="exercise",  preferred_time="morning"))
mochi.add_task(Task(title="Joint supplement", duration_minutes=5,  priority="high",   category="medication",preferred_time="morning"))
mochi.add_task(Task(title="Breakfast",        duration_minutes=10, priority="medium", category="feeding",   preferred_time="morning"))

plan = scheduler.build_plan(jordan, mochi)
for s in plan.scheduled:
    print(f"  {s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}  {s.task.title}")

if plan.conflicts:
    for w in plan.conflicts:
        print(f"  ⚠ {w}")
else:
    print("  ✓ No conflicts detected.")

# ---------------------------------------------------------------------------
# Scenario 2: Forced overlap — two tasks manually placed at the same time
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("SCENARIO 2: Forced overlap (two tasks at the same time)")
print("=" * 60)

whisker = Pet(name="Whisker", species="cat")
owner2  = Owner(name="Alex", available_minutes=120, day_start=time(8, 0))
owner2.add_pet(whisker)

walk    = Task(title="Walk Whisker",    duration_minutes=30, priority="high",   category="exercise")
feeding = Task(title="Feed Whisker",    duration_minutes=15, priority="high",   category="feeding")
groomed = Task(title="Groom Whisker",   duration_minutes=20, priority="medium", category="grooming")

# Manually construct two ScheduledTasks that overlap at 08:00–08:30
overlapping = [
    ScheduledTask(task=walk,    start_time=time(8, 0),  end_time=time(8, 30), reason="manually placed"),
    ScheduledTask(task=feeding, start_time=time(8, 15), end_time=time(8, 30), reason="manually placed — overlaps walk"),
    ScheduledTask(task=groomed, start_time=time(8, 30), end_time=time(8, 50), reason="no overlap"),
]

print("  Manually scheduled slots:")
for s in overlapping:
    print(f"  {s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}  {s.task.title}")

print()
conflicts = scheduler.detect_conflicts(overlapping)
if conflicts:
    print("  Conflict warnings:")
    for w in conflicts:
        print(f"  ⚠ {w}")
else:
    print("  ✓ No conflicts detected.")

# ---------------------------------------------------------------------------
# Scenario 3: Same-category tasks too close (feeding within 2 hours)
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("SCENARIO 3: Two feedings scheduled 30 minutes apart")
print("=" * 60)

owner3 = Owner(name="Sam", available_minutes=120, day_start=time(7, 0))
bunny  = Pet(name="Biscuit", species="rabbit")
owner3.add_pet(bunny)

bunny.add_task(Task(title="Morning feed", duration_minutes=10, priority="high",   category="feeding"))
bunny.add_task(Task(title="Second feed",  duration_minutes=10, priority="high",   category="feeding"))
bunny.add_task(Task(title="Playtime",     duration_minutes=15, priority="medium", category="enrichment"))

plan3 = scheduler.build_plan(owner3, bunny)
for s in plan3.scheduled:
    print(f"  {s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}  {s.task.title}")

print()
if plan3.conflicts:
    print("  Conflict warnings:")
    for w in plan3.conflicts:
        print(f"  ⚠ {w}")
else:
    print("  ✓ No conflicts detected.")

print()
print("=" * 60)
