# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The system is built around three core actions a user needs to perform:

1. **Set up a pet profile.** The user enters their own name and their pet's name, species, age, and any special needs (e.g., medication, joint support). This information is captured in two classes — `Owner` and `Pet` — and flows into the scheduler so that task reasoning can be personalized. For example, if a pet has a special need, the scheduler will call that out explicitly when it explains why a related task was chosen.

2. **Build and manage a task list.** The user adds care tasks one at a time, specifying a title, duration in minutes, priority (high / medium / low), category (exercise, feeding, medication, grooming, enrichment, or general), and an optional preferred time of day. Each task is a `Task` object. The user can also remove individual tasks or clear the whole list before generating a plan.

3. **Generate and read today's schedule.** The user sets how many minutes they have available and what time their day starts, then clicks "Generate schedule." The `Scheduler` class takes the `Owner`, `Pet`, and list of `Task` objects and returns a `DailyPlan` — an ordered list of `ScheduledTask` entries, each with a start time, end time, and plain-language explanation of why it was chosen. Tasks that don't fit in the time budget are listed separately as skipped, with a reason.

The five classes in the system and their responsibilities:

| Class | Responsibility |
|---|---|
| `Task` | Holds what needs to happen, how long it takes, its priority, category, and preferred time |
| `Pet` | Holds the animal's name, species, age, and special needs |
| `Owner` | Holds the person's name, total time available, and day start time |
| `Scheduler` | Sorts tasks by priority and fits them into the owner's time budget; produces a `DailyPlan` |
| `DailyPlan` | Stores the ordered list of scheduled tasks and any skipped tasks; can render a text summary |

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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
