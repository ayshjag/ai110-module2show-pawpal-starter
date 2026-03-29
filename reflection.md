# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML identified six classes organized into two layers: a data layer of plain objects that hold information, and a logic layer with one class responsible for all scheduling behavior.

The data layer contains four classes:

- **`Owner`** holds the person's name, how many minutes they have available for pet care today, and what time their day starts. It acts as the source of scheduling constraints — the scheduler reads these values to know its time budget and starting point.
- **`Pet`** holds the animal's name, species, age, and a list of any special needs (e.g. medication, joint support). Special needs are used by the scheduler to flag when a task is directly required by the pet's condition.
- **`Task`** represents a single care activity. It holds a title, duration in minutes, priority (high / medium / low), category (exercise, feeding, medication, grooming, enrichment, or general), and an optional preferred time of day. It validates itself on creation — rejecting a zero duration or an unrecognized priority.
- **`ScheduledTask`** is a `Task` that has been placed in time. It adds a start time, end time, and a plain-language reason explaining why the task was chosen and when it was placed.

The logic layer contains two classes:

- **`Scheduler`** is the only class with real behavior. It takes an `Owner`, a `Pet`, and a list of `Task` objects, sorts them by priority (high → medium → low), and fits them into the owner's time budget one by one. Tasks that don't fit are recorded as skipped with an explanation. It returns a `DailyPlan`.
- **`DailyPlan`** is the output object. It holds the ordered list of `ScheduledTask` entries and the list of skipped tasks, and can produce a formatted text summary of the full plan.

The key design decision was to keep all scheduling logic inside `Scheduler` and make every other class a pure data holder. This made each class easy to test independently and kept the algorithm in one place.

**b. Design changes**

After reviewing the code with AI feedback, two meaningful gaps between the UML design and the implementation were identified:

**1. `Owner` has no relationship to `Pet`.**
The final UML diagram explicitly modeled `Owner "1" --> "*" Pet : owns`, but in the implemented code `Owner` and `Pet` are completely independent — they are just two separate arguments passed into `Scheduler.build_plan()`. Nothing in the code enforces or expresses that an owner has pets. This was left as-is for now because the app currently only handles one pet at a time, but it is a known gap between the design and the implementation that would need to be addressed if multi-pet support were added.

**2. `preferred_time` on `Task` is declared but never used by the scheduler.**
The `Task` class stores a `preferred_time` attribute ("morning", "afternoon", "evening"), and it appears in the UML and in the UI. However, `build_plan()` never uses it to influence when a task is actually placed — it only appears in the reasoning text. This means the scheduler ignores a constraint that the design promised to support. This was identified as a logic bottleneck: the attribute is present but has no effect on the output, which could confuse a user who sets a preferred time and sees it ignored in the schedule.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints, listed from most to least influential in the algorithm:

1. **Time budget** — the owner's `available_minutes` is a hard ceiling. Any task that would push the total over the limit is skipped rather than partially scheduled. This was treated as the highest-priority constraint because exceeding it would give the owner an impossible plan.

2. **Task priority** — tasks are sorted high → medium → low before placement. Within the same priority, ties are broken by preferred time (morning before afternoon before evening), then by shortest duration first. Priority was ranked second because the scenario explicitly required the scheduler to "consider priority" — a vet medication is always more important than enrichment play regardless of preference.

3. **Preferred time of day** — `preferred_time` acts as a soft sorting hint within the same priority tier, not a hard constraint. A high-priority task will always be placed before a lower-priority one even if the lower-priority task has a more suitable time preference. This decision was made to keep the algorithm simple and predictable — a hard time window would require backtracking logic.

4. **Recurrence frequency** — `daily` tasks are always included; `weekly` tasks only appear on their configured days; `as-needed` tasks are never auto-included. This constraint operates at the task-selection stage before scheduling begins, acting as a filter rather than a sort key.

**b. Tradeoffs**

The scheduler's conflict detection uses a greedy, warning-only approach rather than preventing conflicts at schedule-build time. Specifically, `detect_conflicts()` checks for overlapping durations between any two tasks using interval math (`a_start < b_end and b_start < a_end`), but it only runs *after* the schedule is already built and returns a list of warning strings rather than rejecting or reordering conflicting tasks.

This means a conflict can exist in the final plan — the scheduler will flag it but still hand it back to the user unchanged. A stricter design could refuse to schedule a task that conflicts, or automatically reorder tasks to avoid the overlap. The tradeoff was made deliberately for two reasons:

1. **In normal use, conflicts shouldn't happen.** `build_plan()` places tasks sequentially with no gaps, so two tasks for the same pet can never overlap when scheduled through the standard path. Conflicts only arise if tasks are manually constructed or injected — which is an edge case, not the main flow.

2. **Warnings are more useful than crashes for a pet owner.** If the scheduler silently dropped or reordered tasks without explanation, a user might miss that their pet's medication was moved or skipped. Surfacing the conflict as a readable warning — "medication 'Joint supplement' is scheduled outside its preferred morning window" — gives the owner information to act on rather than hiding the problem.

The limitation this creates is that the scheduler does not automatically resolve conflicts it detects. A future improvement would be to attempt rescheduling before falling back to a warning.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every phase of the project, but in different roles:

- **Phase 1 (design):** Used to generate and review a Mermaid.js UML diagram. The most useful prompt was asking it to identify missing relationships — this caught the `Owner → Pet` association that was absent from the first draft.
- **Phase 2 (implementation):** Used to generate class skeletons and method stubs, then to review the implementation for gaps. The prompt "review #file:pawpal_system.py and identify missing relationships or logic bottlenecks" surfaced the fact that `preferred_time` was declared but never used by the scheduler.
- **Phase 3 (algorithms):** Used to suggest improvements to `detect_conflicts()` and to implement the recurring task feature via Agent mode. The most effective prompts were specific and scoped — "implement `next_occurrence()` using `dataclasses.replace()` and `timedelta`" produced usable code immediately, whereas broad prompts like "improve the scheduler" produced vague suggestions.
- **Phase 4 (testing):** Used to identify edge cases not covered by the existing suite. Asking "what are the most important edge cases for a pet scheduler with sorting and recurring tasks?" surfaced 10 additional test scenarios including boundary conditions (task duration exactly equals budget) and false-positive risks (single-task conflict detection).

The most effective prompt pattern throughout was: **give the AI a specific class or method as context, state the exact behavior you want, and ask for a focused implementation** — not a broad improvement.

**b. Judgment and verification**

When asked to simplify `detect_conflicts()`, the AI suggested replacing the three clearly-structured loops with nested list comprehensions using the walrus operator (`:=`). The compressed version was shorter but significantly harder to read — a future contributor would struggle to add a fourth conflict type without breaking the comprehension structure.

The suggestion was rejected on readability grounds. The decision was verified by running the existing tests against both versions to confirm identical output, then choosing the version that would be easier to extend. This was an important moment: the AI optimized for conciseness, but the human judgment was that maintainability mattered more than line count for a system that would likely grow. The rule applied was: "three similar lines of code is better than a premature abstraction."

---

## 4. Testing and Verification

**a. What you tested**

The final test suite contains 58 tests across eight areas:

- **Task validation** — zero duration and invalid priority raise `ValueError`; defaults are sensible
- **Pet and Owner management** — add/remove tasks and pets; cross-pet task access via `all_tasks()` and `all_pending_tasks()`
- **Scheduling** — priority ordering; time budget enforcement; sequential time slot assignment from `day_start`
- **Sorting** — named periods (`morning < afternoon < evening`); `HH:MM` strings sorted chronologically; mixed formats interleave correctly; tasks with no preference sort last
- **Filtering** — `filter_by_status`, `filter_by_category`, `filter_by_priority`, `filter_by_pet`; each returns empty list when no match
- **Recurring tasks** — `is_due_today()` respects frequency and `days_of_week`; `next_occurrence()` advances `due_date` by correct interval; original task is never mutated; `mark_complete()` with and without `today` behaves differently
- **Conflict detection** — overlaps caught; same-category proximity flagged; medication outside window warned; empty schedule and single-task produce no false positives
- **Edge cases** — pet with no tasks; all tasks completed; task duration exactly equals budget; owner with no pets; weekly task excluded on wrong weekday; `next_occurrence()` preserves all attributes

These tests mattered because they verified behavior at the boundaries — the places where assumptions break and bugs hide. Testing that a task with duration exactly equal to the budget is scheduled (not skipped) found a potential off-by-one risk in the budget check that would otherwise only surface in real use.

**b. Confidence**

**★★★★☆ — High confidence in the logic layer, limited confidence in the UI layer.**

The scheduling logic, sorting, filtering, recurring tasks, and conflict detection are all covered by automated tests that run in under 200ms. Any regression in `pawpal_system.py` would be caught immediately.

The gap is `app.py`: the Streamlit UI has no automated tests. Session state persistence, button interactions, and the visual display of conflict warnings are only verifiable manually. The next tests to add would be integration tests using `streamlit.testing.v1` (Streamlit's built-in testing library) to simulate form submissions and verify that clicking "Generate schedule" produces the expected plan display.

---

## 5. Reflection

**a. What went well**

The most satisfying part of the project is the relationship between the test suite and the implementation. Every significant feature — sorting, filtering, recurring tasks, conflict detection — has direct test coverage, and running `python -m pytest` gives immediate, trustworthy feedback on whether the system is working. This made refactoring and extending the code feel safe rather than risky. Adding `next_occurrence()` and wiring it into `mark_complete()` was straightforward because existing tests immediately caught any regressions.

The `Scheduler` class also came together well as a genuine "brain" — it evolved from a single `build_plan()` method into a class with four distinct responsibility groups (retrieval, organisation, state management, plan generation), each with its own clearly named methods. This made the AI-assisted phases easier because scoped prompts like "add filtering methods to Scheduler" had a clear home to target.

**b. What you would improve**

The shared time budget problem is the most significant design gap remaining. Currently `build_plan()` is called once per pet, giving each pet the full `available_minutes` budget independently. A real pet owner with two pets and 90 minutes total would expect those 90 minutes to be shared, not duplicated. Fixing this would require a multi-pet planning method that deducts time across pets rather than resetting the budget for each one.

The second improvement would be making `preferred_time` a hard constraint for medication tasks specifically. Currently it is a sort hint only. A medication that must be given in the morning should be flagged as a critical miss if the owner's day starts too late for it to fit in the morning window — not silently placed at whatever time fits.

**c. Key takeaway**

The most important thing learned was that **AI is a strong implementer but a weak architect**. When given a clear, scoped specification — "implement `next_occurrence()` using `dataclasses.replace()` and `timedelta` with these exact behaviours" — it produces correct, usable code quickly. When asked broad questions like "how should the scheduler work?" it produces plausible-sounding but often shallow designs that skip the hard tradeoffs.

The human role in this project was to make the architectural decisions: which constraints matter most, which tradeoffs to accept, which AI suggestions to reject, and how to structure the system so it can grow. The AI handled a large volume of correct, well-structured code — but every meaningful design choice required a human to evaluate it, verify it against tests, and decide whether it fit the system's direction. Being the "lead architect" meant staying in control of the why, even when delegating the how.
