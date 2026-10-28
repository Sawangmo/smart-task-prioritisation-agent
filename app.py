
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

from agent import run_agent
from memory import get_recent_sessions


# DeadlineIQ - Light Blue + White Theme
import streamlit as st

st.markdown("""
<style>
/* Main page background */
.stApp {
    background-color: #EFF6FF;
    color: #1E293B;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #DBEAFE;
}

/* Main content text */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp p,
.stApp label {
    color: #1E293B;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #DBEAFE;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.06);
}

/* Buttons */
.stButton > button {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

/* Button hover effect */
.stButton > button:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
    border: none;
}

/* Input fields */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea {
    background-color: #FFFFFF;
    color: #1E293B;
    border-radius: 8px;
}

/* Select boxes */
[data-testid="stSelectbox"] {
    background-color: #FFFFFF;
    border-radius: 8px;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: #1E40AF;
}

.stTabs [aria-selected="true"] {
    color: #2563EB;
}

/* Data tables */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 10px;
}

/* Divider */
hr {
    border-color: #DBEAFE;
}
</style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Smart Task Prioritisation Agent",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🗓️ Smart Task Prioritisation Agent")
st.markdown(
    "Organise your tasks, track deadlines, and create a realistic "
    "daily plan with your intelligent task prioritisation agent."
)

# ---------------- SESSION STATE ----------------

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0


# ---------------- DEADLINE COUNTDOWN ----------------

def deadline_info(task):
    """Calculate days remaining until the task deadline."""

    if task.get("completed", False):
        return None, "Completed", "✅"

    try:
        deadline = date.fromisoformat(
            str(task.get("deadline", ""))[:10]
        )
    except (ValueError, TypeError):
        return None, "No valid deadline", "❔"

    days_left = (deadline - date.today()).days

    if days_left < 0:
        return days_left, f"Overdue by {abs(days_left)} day(s)", "🚨"

    if days_left == 0:
        return 0, "Due today", "🔴"

    if days_left == 1:
        return 1, "1 day left", "🟠"

    if days_left <= 3:
        return days_left, f"{days_left} days left", "🟠"

    return days_left, f"{days_left} days left", "🟢"


def invalidate_plan():
    st.session_state.last_result = None


# ---------------- SIDEBAR: ADD TASK ----------------

with st.sidebar:
    st.header("Add a New Task")

    with st.form("add_task_form", clear_on_submit=True):
        task_title = st.text_input(
            "Task title",
        
        )

        task_deadline = st.date_input(
            "Deadline",
            value=date.today() + timedelta(days=3)
        )

        task_importance = st.slider(
            "Importance",
            min_value=1,
            max_value=5,
            value=4,
            help="1 = low importance, 5 = very important"
        )

        task_duration = st.number_input(
            "Estimated work (hours)",
            min_value=0.25,
            max_value=100.0,
            value=2.0,
            step=0.25
        )

        task_category = st.selectbox(
            "Category",
            [
                "Assignment",
                "Exam preparation",
                "Project",
                "Personal",
                "Other"
            ]
        )

        add_task = st.form_submit_button(
            "➕ Add Task",
            type="primary",
            use_container_width=True
        )

    if add_task:
        if task_title.strip():
            st.session_state.task_counter += 1

            st.session_state.tasks.append({
                "id": st.session_state.task_counter,
                "title": task_title.strip(),
                "deadline": task_deadline.isoformat(),
                "importance": int(task_importance),
                "duration": float(task_duration),
                "category": task_category,
                "completed": False,
            })

            invalidate_plan()
            st.success(f"Added: {task_title.strip()}")
        else:
            st.error("Please enter a task title.")

    st.divider()
    st.header("⚙️ Daily Planning")

    available_hours = st.slider(
        "Time available today (hours)",
        min_value=0.5,
        max_value=12.0,
        value=3.0,
        step=0.5
    )

    feedback = st.text_area(
        "Feedback for the agent (optional)",
        placeholder="Example: Give more time to coding tasks.",
        height=100
    )

    if st.button(
        "🧠 Prioritise My Tasks",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.tasks
    ):
        with st.spinner("Analysing tasks and deadlines..."):
            st.session_state.last_result = run_agent(
                st.session_state.tasks,
                available_hours,
                feedback
            )

        st.success("Your daily plan is ready!")


# ---------------- DASHBOARD METRICS ----------------

tasks = st.session_state.tasks

active_tasks = [
    task for task in tasks
    if not task.get("completed", False)
]

completed_tasks = [
    task for task in tasks
    if task.get("completed", False)
]

overdue_tasks = [
    task for task in active_tasks
    if deadline_info(task)[0] is not None
    and deadline_info(task)[0] < 0
]

due_today = [
    task for task in active_tasks
    if deadline_info(task)[0] == 0
]

completion_percentage = (
    len(completed_tasks) / len(tasks) * 100
    if tasks else 0
)

st.subheader("DeadlineIQ")

col1, col2, col3, col4 = st.columns(4)

col1.metric("📋 Total Tasks", len(tasks))
col2.metric("⏳ In Progress", len(active_tasks))
col3.metric("🚨 Overdue", len(overdue_tasks))
col4.metric(
    "✅ Completed",
    f"{len(completed_tasks)} / {len(tasks)}"
)

st.progress(
    int(completion_percentage),
    text=f"Overall completion: {completion_percentage:.0f}%"
)

if overdue_tasks:
    st.error(
        f"You have {len(overdue_tasks)} overdue task(s). "
        "Review these tasks as soon as possible."
    )
elif due_today:
    st.warning(
        f"You have {len(due_today)} task(s) due today!"
    )
elif not tasks:
    st.info("Add your first task using the sidebar.")
else:
    st.success("No overdue tasks. Keep up the good work!")


# ---------------- INTERACTIVE TABS ----------------

tab_tasks, tab_plan, tab_history = st.tabs([
    "📋 My Tasks & Deadlines",
    "🧠 Agent Plan",
    "🗃️ Session History"
])


# ---------------- TASK MANAGEMENT ----------------

with tab_tasks:
    st.subheader("📅 Task Deadline Countdown")

    st.caption(
        "The countdown uses your computer's current date. "
        "A negative number means the deadline has passed."
    )

    if not tasks:
        st.info("Your task list is empty. Add a task from the sidebar.")

    else:
        col_filter, col_sort = st.columns(2)

        with col_filter:
            status_filter = st.selectbox(
                "Filter tasks",
                [
                    "All Tasks",
                    "In Progress",
                    "Completed",
                    "Overdue",
                    "Due in Next 3 Days"
                ]
            )

        with col_sort:
            sort_option = st.selectbox(
                "Sort tasks",
                [
                    "Soonest Deadline",
                    "Highest Importance",
                    "Longest Task First",
                    "Task Name"
                ]
            )

        shown_tasks = list(tasks)

        if status_filter == "In Progress":
            shown_tasks = [
                t for t in shown_tasks
                if not t.get("completed", False)
            ]

        elif status_filter == "Completed":
            shown_tasks = [
                t for t in shown_tasks
                if t.get("completed", False)
            ]

        elif status_filter == "Overdue":
            shown_tasks = [
                t for t in shown_tasks
                if not t.get("completed", False)
                and deadline_info(t)[0] is not None
                and deadline_info(t)[0] < 0
            ]

        elif status_filter == "Due in Next 3 Days":
            shown_tasks = [
                t for t in shown_tasks
                if not t.get("completed", False)
                and deadline_info(t)[0] is not None
                and 0 <= deadline_info(t)[0] <= 3
            ]

        if sort_option == "Soonest Deadline":
            shown_tasks.sort(
                key=lambda t: (
                    t.get("completed", False),
                    t.get("deadline", "9999-12-31")
                )
            )

        elif sort_option == "Highest Importance":
            shown_tasks.sort(
                key=lambda t: (
                    t.get("completed", False),
                    -int(t.get("importance", 1))
                )
            )

        elif sort_option == "Longest Task First":
            shown_tasks.sort(
                key=lambda t: (
                    t.get("completed", False),
                    -float(t.get("duration", 0))
                )
            )

        elif sort_option == "Task Name":
            shown_tasks.sort(
                key=lambda t: t.get("title", "").lower()
            )

        for task in shown_tasks:
            days_left, status, emoji = deadline_info(task)

            with st.container(border=True):
                title_col, countdown_col = st.columns([3, 1])

                with title_col:
                    st.markdown(f"### {task['title']}")

                    st.caption(
                        f"Category: {task.get('category', 'Other')} | "
                        f"Importance: {task.get('importance', 1)}/5 | "
                        f"Estimated work: {task.get('duration', 1)} hour(s)"
                    )

                with countdown_col:
                    if task.get("completed", False):
                        st.success("✅ Completed")

                    elif days_left is not None and days_left < 0:
                        st.error(f"{emoji} {status}")

                    elif days_left == 0:
                        st.error(f"{emoji} {status}")

                    elif days_left is not None and days_left <= 3:
                        st.warning(f"{emoji} {status}")

                    else:
                        st.info(f"{emoji} {status}")

                st.write(f"**Deadline:** {task.get('deadline', 'Not set')}")

                button1, button2, _ = st.columns([1, 1, 3])

                task_id = task.get("id", task["title"])

                if not task.get("completed", False):
                    if button1.button(
                        "✓ Complete",
                        key=f"complete_{task_id}"
                    ):
                        task["completed"] = True
                        invalidate_plan()
                        st.rerun()

                else:
                    if button1.button(
                        "↩ Reopen",
                        key=f"reopen_{task_id}"
                    ):
                        task["completed"] = False
                        invalidate_plan()
                        st.rerun()

                if button2.button(
                    "🗑 Remove",
                    key=f"remove_{task_id}"
                ):
                    st.session_state.tasks.remove(task)
                    invalidate_plan()
                    st.rerun()

        # CSV export
        st.divider()

        if tasks:
            export_data = []

            for task in tasks:
                days_left, status, _ = deadline_info(task)

                export_data.append({
                    "Task": task.get("title", ""),
                    "Category": task.get("category", ""),
                    "Deadline": task.get("deadline", ""),
                    "Days Remaining": days_left,
                    "Status": status,
                    "Importance": task.get("importance", 1),
                    "Estimated Hours": task.get("duration", 1),
                    "Completed": task.get("completed", False)
                })

            export_df = pd.DataFrame(export_data)

            st.download_button(
                "⬇️ Download Tasks as CSV",
                data=export_df.to_csv(index=False).encode("utf-8"),
                file_name="my_tasks.csv",
                mime="text/csv"
            )


# ---------------- AGENT PLAN ----------------

with tab_plan:
    st.subheader("🧠 Agent Recommendations")

    result = st.session_state.last_result

    if not result:
        st.info(
            "Use the sidebar to add tasks, choose today's available "
            "hours, and click 'Prioritise My Tasks'."
        )

    else:
        st.write(result.get("summary", ""))

        ranked_tasks = result.get("prioritised_tasks", [])

        if ranked_tasks:
            ranking_rows = []

            for rank, task in enumerate(ranked_tasks, start=1):
                days_left, status, _ = deadline_info(task)

                ranking_rows.append({
                    "Rank": rank,
                    "Task": task.get("title", ""),
                    "Priority Score": round(
                        float(task.get("priority_score", 0)), 1
                    ),
                    "Priority": task.get("priority_level", ""),
                    "Deadline": task.get("deadline", ""),
                    "Days Left": (
                        days_left if days_left is not None else status
                    ),
                    "Estimated Hours": task.get("duration", 1)
                })

            ranking_df = pd.DataFrame(ranking_rows)

            st.markdown("#### 📈 Priority Ranking")
            st.dataframe(
                ranking_df,
                use_container_width=True,
                hide_index=True
            )

            chart_df = ranking_df.sort_values("Priority Score")

            fig, ax = plt.subplots(
                figsize=(8, max(3, len(chart_df) * 0.45))
            )

            ax.barh(
                chart_df["Task"],
                chart_df["Priority Score"]
            )

            ax.set_xlabel("Priority Score")
            ax.set_title("Task Priority Comparison")
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

        st.markdown("#### ⏰ Deadline Alerts")

        warnings = result.get("deadline_warnings", [])

        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("No deadline warnings returned by the agent.")

        st.markdown("#### 🗓️ Suggested Schedule for Today")

        schedule = result.get("schedule", [])

        if schedule:
            st.dataframe(
                pd.DataFrame(schedule),
                use_container_width=True,
                hide_index=True
            )

            allocated_hours = sum(
                float(row.get("allocated_hours", 0))
                for row in schedule
            )

            st.caption(
                f"Scheduled {allocated_hours:.2f} of "
                f"{available_hours:.2f} available hours."
            )

        else:
            st.info(
                "No tasks fitted into the available time. "
                "Try increasing today's available hours."
            )


# ---------------- SESSION HISTORY ----------------

with tab_history:
    st.subheader("🗃️ Recent Agent Sessions")

    try:
        sessions = get_recent_sessions(limit=10)
    except Exception as error:
        sessions = []
        st.warning(f"Could not load session history: {error}")

    if sessions:
        history_rows = []

        for session in sessions:
            session_tasks = session.get("tasks", [])

            history_rows.append({
                "Saved At": session.get("created_at", ""),
                "Tasks": len(session_tasks),
                "Available Hours": session.get("available_hours", 0),
                "Feedback": session.get("feedback", "")
            })

        st.dataframe(
            pd.DataFrame(history_rows),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "No saved sessions yet. Run the agent to save your first session."
        )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "Smart Task Prioritisation Agent | Prototype decision-support tool. "
    "Review suggested priorities and schedules before following them."
)
