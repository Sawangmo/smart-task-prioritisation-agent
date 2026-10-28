
from datetime import date

from langgraph.graph import StateGraph, START, END

from state import AgentState
from prioritiser import prioritise_tasks
from tools import check_deadlines
from planner import make_plan, build_multi_day_timetable
from memory import get_recent_sessions, save_session


def load_memory_node(state: AgentState) -> dict:
    return {"memory": get_recent_sessions(limit=5)}


def prioritise_node(state: AgentState) -> dict:
    return {
        "prioritised_tasks": prioritise_tasks(
            state.get("tasks", [])
        )
    }


def deadline_node(state: AgentState) -> dict:
    return {
        "deadline_warnings": check_deadlines(
            state.get("tasks", [])
        )
    }


def planning_node(state: AgentState) -> dict:
    ranked = state.get("prioritised_tasks", [])
    available_hours = float(state.get("available_hours", 3.5))

    multi_day = build_multi_day_timetable(
        ranked,
        start_date=date.today(),
        study_start="17:30",
        study_end="21:00",
        break_minutes=10,
        session_minutes=50,
        max_days=30,
    )

    return {
        "schedule": make_plan(ranked, available_hours),
        "multi_day_schedule": multi_day["sessions"],
        "unscheduled_tasks": multi_day["unscheduled_tasks"],
    }


def reflect_and_save_node(state: AgentState) -> dict:
    ranked = state.get("prioritised_tasks", [])
    warnings = state.get("deadline_warnings", [])
    schedule = state.get("schedule", [])
    multi_day = state.get("multi_day_schedule", [])
    unscheduled = state.get("unscheduled_tasks", [])
    feedback = (state.get("feedback") or "").strip()

    if not ranked:
        summary = (
            "There are no unfinished tasks. Add a task before planning."
        )
    else:
        summary = (
            f"Ranked {len(ranked)} unfinished task(s). "
            f"Recommended first: '{ranked[0]['title']}'. "
            f"Today's plan has {len(schedule)} session(s); "
            f"the multi-day timetable has {len(multi_day)} session(s). "
            f"{len(warnings)} deadline alert(s); "
            f"{len(unscheduled)} task(s) need more time or review."
        )

    if feedback:
        summary += f" Feedback recorded: {feedback}"
    else:
        summary += " You can provide feedback after using the plan."

    save_session(
        state.get("tasks", []),
        state.get("available_hours", 3.5),
        feedback,
    )

    return {"summary": summary}


def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("load_memory", load_memory_node)
    graph.add_node("prioritise", prioritise_node)
    graph.add_node("check_deadlines", deadline_node)
    graph.add_node("plan", planning_node)
    graph.add_node("reflect_and_save", reflect_and_save_node)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "prioritise")
    graph.add_edge("prioritise", "check_deadlines")
    graph.add_edge("check_deadlines", "plan")
    graph.add_edge("plan", "reflect_and_save")
    graph.add_edge("reflect_and_save", END)

    return graph.compile()


agent = build_agent()


def run_agent(
    tasks: list[dict],
    available_hours: float,
    feedback: str = "",
) -> dict:
    return agent.invoke(
        {
            "tasks": tasks,
            "available_hours": float(available_hours),
            "feedback": feedback,
        }
    )
