
from tools import build_study_schedule


def make_plan(
    prioritised_tasks: list[dict],
    available_hours: float
) -> list[dict]:
    return build_study_schedule(
        prioritised_tasks,
        available_hours
    )
