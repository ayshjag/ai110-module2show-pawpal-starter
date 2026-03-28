import streamlit as st
from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet.")

# ---------------------------------------------------------------------------
# Owner + Pet info
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=10, max_value=600, value=120, step=10
    )
    day_start_hour = st.slider("Day start (hour)", min_value=5, max_value=12, value=7)

with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    pet_age = st.number_input("Pet age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
    special_needs_raw = st.text_input(
        "Special needs (comma-separated, optional)", placeholder="e.g. medication, joint support"
    )

special_needs = [s.strip() for s in special_needs_raw.split(",") if s.strip()] if special_needs_raw else []

st.divider()

# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------

st.subheader("Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col4:
        category = st.selectbox("Category", ["exercise", "feeding", "medication", "grooming", "enrichment", "general"])
    with col5:
        preferred_time = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])

    submitted = st.form_submit_button("Add task")
    if submitted and task_title.strip():
        st.session_state.tasks.append(
            {
                "title": task_title.strip(),
                "duration_minutes": int(duration),
                "priority": priority,
                "category": category,
                "preferred_time": None if preferred_time == "any" else preferred_time,
            }
        )

if st.session_state.tasks:
    st.write(f"**{len(st.session_state.tasks)} task(s) queued:**")
    for i, t in enumerate(st.session_state.tasks):
        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.markdown(
                f"- **{t['title']}** — {t['duration_minutes']} min | "
                f"priority: `{t['priority']}` | category: `{t['category']}`"
            )
        with col_b:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.tasks.pop(i)
                st.rerun()

    if st.button("Clear all tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------

st.subheader("Generate Schedule")

if st.button("Generate schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            day_start=time(day_start_hour, 0),
        )
        pet = Pet(
            name=pet_name,
            species=species,
            age_years=float(pet_age),
            special_needs=special_needs,
        )
        task_objects = [
            Task(
                title=t["title"],
                duration_minutes=t["duration_minutes"],
                priority=t["priority"],
                category=t["category"],
                preferred_time=t["preferred_time"],
            )
            for t in st.session_state.tasks
        ]

        plan = Scheduler().build_plan(owner, pet, task_objects)

        st.success(
            f"Schedule built for **{owner.name}** and **{pet.name}** — "
            f"{plan.total_minutes} of {owner.available_minutes} minutes used."
        )

        if plan.scheduled:
            st.markdown("### Scheduled tasks")
            for s in plan.scheduled:
                with st.expander(
                    f"{_fmt(s.start_time)} – {_fmt(s.end_time)}  |  "
                    f"[{s.task.priority.upper()}] {s.task.title}  ({s.task.duration_minutes} min)",
                    expanded=True,
                ):
                    st.markdown(f"**Reasoning:** {s.reason}")

        if plan.skipped:
            st.markdown("### Skipped tasks")
            for task, reason in plan.skipped:
                st.warning(f"**{task.title}** — {reason}")


def _fmt(t) -> str:
    suffix = "AM" if t.hour < 12 else "PM"
    hour = t.hour % 12 or 12
    return f"{hour}:{t.minute:02d} {suffix}"
