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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
