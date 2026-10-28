
from langgraph.graph import StateGraph, START, END

from state import AgentState
from prioritiser import prioritise_tasks
from tools import check_deadlines
from planner import make_plan
from memory import get_recent_sessions, save_session


def load_memory_node(state: AgentState) -> dict:
    return {
        "memory": get_recent_sessions(limit=5)
    }


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
    return {
        "schedule": make_plan(
            state.get("prioritised_tasks", []),
            state.get("available_hours", 2.0)
        )
    }


def reflect_and_save_node(state: AgentState) -> dict:
    ranked = state.get("prioritised_tasks", [])
    warnings = state.get("deadline_warnings", [])
    schedule = state.get("schedule", [])
    feedback = (state.get("feedback") or "").strip()

    if not ranked:
        summary = (
            "There are no unfinished tasks. "
            "Add a task before planning."
        )
    else:
        summary = (
            f"Ranked {len(ranked)} unfinished task(s). "
            f"Recommended first: '{ranked[0]['title']}'. "
            f"The schedule contains {len(schedule)} item(s) "
            f"and {len(warnings)} deadline alert(s)."
        )

    if feedback:
        summary += f" Feedback recorded: {feedback}"
    else:
        summary += " You can provide feedback after using the plan."

    save_session(
        state.get("tasks", []),
        state.get("available_hours", 2.0),
        feedback
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
    feedback: str = ""
) -> dict:
    return agent.invoke({
        "tasks": tasks,
        "available_hours": float(available_hours),
        "feedback": feedback
    })
