
from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    tasks: list[dict[str, Any]]
    available_hours: float
    feedback: str
    memory: list[dict[str, Any]]
    prioritised_tasks: list[dict[str, Any]]
    deadline_warnings: list[str]
    schedule: list[dict[str, Any]]
    multi_day_schedule: list[dict[str, Any]]
    unscheduled_tasks: list[dict[str, Any]]
    summary: str
