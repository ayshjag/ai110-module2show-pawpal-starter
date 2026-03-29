# PawPal+ — Final UML Class Diagram

Paste the code block below into https://mermaid.live to render the diagram,
then export it as uml_final.png.

```mermaid
classDiagram
    class Task {
        +String title
        +int duration_minutes
        +String description
        +String priority
        +String category
        +String frequency
        +String preferred_time
        +bool completed
        +date due_date
        +list~int~ days_of_week
        +validate()
        +is_due_today(weekday) bool
        +next_occurrence(today) Task
    }

    class Pet {
        +String name
        +String species
        +float age_years
        +list~String~ special_needs
        +list~Task~ tasks
        +add_task(task)
        +remove_task(title)
        +pending_tasks() list
        +due_today_tasks(weekday) list
    }

    class Owner {
        +String name
        +int available_minutes
        +time day_start
        +list~Pet~ pets
        +add_pet(pet)
        +remove_pet(name)
        +all_tasks() list
        +all_pending_tasks() list
    }

    class ScheduledTask {
        +Task task
        +time start_time
        +time end_time
        +String reason
        +duration_minutes() int
    }

    class DailyPlan {
        +Owner owner
        +Pet pet
        +list~ScheduledTask~ scheduled
        +list skipped
        +list~String~ conflicts
        +total_minutes() int
        +summary() str
    }

    class Scheduler {
        +build_plan(owner, pet, tasks) DailyPlan
        +sort_tasks(tasks) list
        +sort_by_time(tasks) list
        +tasks_by_priority(tasks) dict
        +tasks_by_pet(owner) dict
        +filter_by_status(tasks, completed) list
        +filter_by_category(tasks, category) list
        +filter_by_priority(tasks, priority) list
        +filter_by_pet(owner, pet_name) list
        +due_today(owner, weekday) list
        +detect_conflicts(scheduled) list
        +mark_complete(task, pet, today) Task
        +reset_all(owner)
        +get_tasks_for_pet(pet) list
        +get_pending_tasks_for_pet(pet) list
        +get_all_pending_tasks(owner) list
    }

    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Scheduler ..> Owner : reads
    Scheduler ..> Pet : reads
    Scheduler ..> Task : uses
    Scheduler --> DailyPlan : produces
    DailyPlan "1" --> "*" ScheduledTask : contains
    DailyPlan --> Owner : references
    DailyPlan --> Pet : references
    ScheduledTask --> Task : wraps
```

## Changes from initial UML

| Change | Why |
|---|---|
| `Owner "1" --> "*" Pet` relationship added | Closes the gap identified in design review — Owner now holds a pets list |
| `Pet "1" --> "*" Task` relationship added | Tasks belong to pets, not a separate floating list |
| `Task` gained `frequency`, `due_date`, `days_of_week`, `is_due_today()`, `next_occurrence()` | Recurring task support added in Phase 3 |
| `DailyPlan` gained `conflicts: list[str]` | Conflict detection output stored on the plan |
| `Scheduler` expanded with 10+ new methods | Filtering, sorting, recurring, conflict detection all added |
| `__post_init__` renamed to `validate()` in diagram | Implementation detail replaced with meaningful behavior name |
