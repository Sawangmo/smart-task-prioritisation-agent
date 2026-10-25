
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

from agent import run_agent
from memory import get_recent_sessions

st.set_page_config(
    page_title="Smart Task Prioritisation Agent",
    page_icon="🗓️",
    layout="wide"
)

st.title("🗓️ Smart Task Prioritisation Agent")
st.write(
    "Rank your tasks, check deadlines, and create "
    "a realistic study plan."
)

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar: add tasks
with st.sidebar:
    st.header("Add a task")

    title = st.text_input(
        "Task title",
        placeholder="Finish NLP assignment"
    )

    deadline = st.date_input(
        "Deadline",
        value=date.today() + timedelta(days=3)
    )

    importance = st.slider(
        "Importance (1 = low, 5 = very high)",
        1, 5, 4
    )

    duration = st.number_input(
        "Estimated work (hours)",
        min_value=0.25,
        max_value=40.0,
        value=2.0,
        step=0.25
    )

    if st.button("Add task", type="primary"):
        if title.strip():
            st.session_state.tasks.append({
                "title": title.strip(),
                "deadline": deadline.isoformat(),
                "importance": importance,
                "duration": duration,
                "completed": False
            })
            st.session_state.last_result = None
            st.success("Task added successfully.")
        else:
            st.warning("Please enter a task title.")

# Display existing tasks
st.subheader("Your tasks")

if not st.session_state.tasks:
    st.info("Add tasks using the sidebar to get started.")
else:
    for i, task in enumerate(st.session_state.tasks):
        left, middle, right = st.columns([6, 1, 1])

        status = (
            "Completed"
            if task.get("completed", False)
            else "Incomplete"
        )

        left.write(
            f"**{task['title']}** — "
            f"Deadline: {task['deadline']} · "
            f"Importance: {task['importance']}/5 · "
            f"{task['duration']} hours · {status}"
        )

        if not task.get("completed", False):
            if middle.button("Complete", key=f"done_{i}"):
                st.session_state.tasks[i]["completed"] = True
                st.session_state.last_result = None
                st.rerun()

        if right.button("Remove", key=f"remove_{i}"):
            st.session_state.tasks.pop(i)
            st.session_state.last_result = None
            st.rerun()

st.divider()

available_hours = st.slider(
    "Available study time today (hours)",
    min_value=0.5,
    max_value=12.0,
    value=3.0,
    step=0.5
)

feedback = st.text_input(
    "Feedback (optional)",
    placeholder="For example, this task took longer than expected."
)

if st.button(
    "Prioritise tasks and create plan",
    type="primary",
    disabled=not st.session_state.tasks
):
    with st.spinner("Agent is preparing your plan..."):
        st.session_state.last_result = run_agent(
            st.session_state.tasks,
            available_hours,
            feedback
        )

# Display agent results
result = st.session_state.last_result

if result:
    st.divider()
    st.subheader("Agent recommendation")
    st.write(result.get("summary", ""))

    ranked = result.get("prioritised_tasks", [])

    if ranked:
        df = pd.DataFrame([
            {
                "Rank": i + 1,
                "Task": task["title"],
                "Score": task["priority_score"],
                "Priority": task["priority_level"],
                "Deadline": task["deadline"],
                "Hours": task["duration"],
                "Explanation": task["explanation"]
            }
            for i, task in enumerate(ranked)
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # Visualise task priorities
        chart_df = df.sort_values("Score")

        fig, ax = plt.subplots()
        ax.barh(chart_df["Task"], chart_df["Score"])
        ax.set_xlabel("Priority score (0–100)")
        ax.set_title("Task Priority Ranking")
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    # Deadline alerts
    st.subheader("Deadline alerts")
    warnings = result.get("deadline_warnings", [])

    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No overdue or near-term deadline alerts.")

    # Study schedule
    st.subheader("Suggested study schedule")
    schedule = result.get("schedule", [])

    if schedule:
        st.dataframe(
            pd.DataFrame(schedule),
            use_container_width=True,
            hide_index=True
        )

        allocated = sum(
            row["allocated_hours"] for row in schedule
        )

        st.caption(
            f"Allocated {allocated:.2f} of "
            f"{available_hours:.2f} available hours."
        )
    else:
        st.info("No unfinished tasks could be scheduled.")

# Persistent memory
with st.expander("Recent session memory"):
    sessions = get_recent_sessions(limit=10)

    if sessions:
        history = pd.DataFrame([
            {
                "Saved at": session["created_at"],
                "Number of tasks": len(session["tasks"]),
                "Available hours": session["available_hours"],
                "Feedback": session["feedback"]
            }
            for session in sessions
        ])

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No saved sessions yet.")

st.caption(
    "Priority scores are estimates to support your decisions. "
    "Check deadlines and review recommendations before following them."
)
