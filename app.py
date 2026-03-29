import streamlit as st
from datetime import time
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet.")

scheduler = Scheduler()

# ---------------------------------------------------------------------------
# Session state — persist real class objects across reruns
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120, day_start=time(7, 0))

if "pet" not in st.session_state:
    st.session_state.pet = Pet(name="Mochi", species="dog")
    st.session_state.owner.add_pet(st.session_state.pet)

owner: Owner = st.session_state.owner
pet: Pet = st.session_state.pet

# ---------------------------------------------------------------------------
# Owner & Pet setup
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    new_owner_name = st.text_input("Owner name", value=owner.name)
    new_minutes = st.number_input(
        "Time available today (minutes)", min_value=10, max_value=600,
        value=owner.available_minutes, step=10
    )
    new_start = st.slider("Day start (hour)", min_value=5, max_value=12,
                          value=owner.day_start.hour)

with col2:
    new_pet_name = st.text_input("Pet name", value=pet.name)
    new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"],
                               index=["dog", "cat", "rabbit", "bird", "other"].index(pet.species))
    new_age = st.number_input("Pet age (years)", min_value=0.0, max_value=30.0,
                              value=pet.age_years, step=0.5)
    special_needs_raw = st.text_input(
        "Special needs (comma-separated, optional)",
        value=", ".join(pet.special_needs),
        placeholder="e.g. medication, joint support"
    )

if st.button("Save profile"):
    owner.name = new_owner_name
    owner.available_minutes = int(new_minutes)
    owner.day_start = time(new_start, 0)
    pet.name = new_pet_name
    pet.species = new_species
    pet.age_years = float(new_age)
    pet.special_needs = [s.strip() for s in special_needs_raw.split(",") if s.strip()]
    st.success(f"Profile saved — {owner.name} & {pet.name}.")

st.divider()

# ---------------------------------------------------------------------------
# Task management — tasks live on the Pet object
# ---------------------------------------------------------------------------

st.subheader("Tasks")

with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        description = st.text_input("Description (optional)", placeholder="e.g. slow-paced walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col3:
        category = st.selectbox("Category",
                                ["exercise", "feeding", "medication", "grooming", "enrichment", "general"])
        preferred_time = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

    if st.form_submit_button("Add task"):
        if task_title.strip():
            # Add directly to the Pet object via pet.add_task()
            pet.add_task(Task(
                title=task_title.strip(),
                description=description.strip(),
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                preferred_time=None if preferred_time == "any" else preferred_time,
                frequency=frequency,
            ))
            st.rerun()

if pet.tasks:
    st.write(f"**{len(pet.tasks)} task(s) on {pet.name}:**")
    for i, t in enumerate(pet.tasks):
        col_a, col_b, col_c = st.columns([5, 1, 1])
        with col_a:
            status = "~~" if t.completed else ""
            st.markdown(
                f"{status}**{t.title}** — {t.duration_minutes} min | "
                f"`{t.priority}` | `{t.category}` | `{t.frequency}`{status}"
            )
            if t.description:
                st.caption(t.description)
        with col_b:
            if not t.completed:
                if st.button("Done", key=f"done_{i}"):
                    scheduler.mark_complete(t)
                    st.rerun()
        with col_c:
            if st.button("Remove", key=f"remove_{i}"):
                pet.remove_task(t.title)
                st.rerun()

    col_x, col_y = st.columns(2)
    with col_x:
        if st.button("Reset all (new day)"):
            scheduler.reset_all(owner)
            st.rerun()
    with col_y:
        if st.button("Clear all tasks"):
            pet.tasks = []
            st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Schedule generation — uses pet.pending_tasks() via build_plan()
# ---------------------------------------------------------------------------

st.subheader("Generate Schedule")

pending = pet.pending_tasks()
st.caption(f"{len(pending)} pending task(s) / {len(pet.tasks)} total on {pet.name}.")

if st.button("Generate schedule", type="primary"):
    if not pending:
        st.warning("No pending tasks to schedule — add tasks or reset completed ones.")
    else:
        # build_plan() pulls pending tasks from pet automatically
        plan = scheduler.build_plan(owner, pet)

        st.success(
            f"Schedule for **{owner.name}** & **{pet.name}** — "
            f"{plan.total_minutes} of {owner.available_minutes} min used."
        )

        if plan.scheduled:
            st.markdown("### Scheduled")
            for s in plan.scheduled:
                with st.expander(
                    f"{s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}  |  "
                    f"[{s.task.priority.upper()}]  {s.task.title}  ({s.task.duration_minutes} min)",
                    expanded=True,
                ):
                    if s.task.description:
                        st.markdown(f"_{s.task.description}_")
                    st.markdown(f"**Why:** {s.reason}")
                    if st.button("Mark done", key=f"plan_done_{s.task.title}"):
                        scheduler.mark_complete(s.task)
                        st.rerun()

        if plan.skipped:
            st.markdown("### Skipped")
            for task, reason in plan.skipped:
                st.warning(f"**{task.title}** — {reason}")
