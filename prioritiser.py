
from datetime import date


def days_until(deadline_text: str) -> int:
    if not deadline_text:
        return 30

    try:
        deadline = date.fromisoformat(str(deadline_text))
        return (deadline - date.today()).days
    except (ValueError, TypeError):
        return 30


def score_task(task: dict) -> dict:
    item = dict(task)

    days = days_until(item.get("deadline", ""))
    importance = max(1, min(5, int(item.get("importance", 3))))
    duration = max(0.25, float(item.get("duration", 1)))

    if days < 0:
        urgency = 100
    elif days == 0:
        urgency = 95
    elif days == 1:
        urgency = 85
    elif days <= 3:
        urgency = 70
    elif days <= 7:
        urgency = 50
    elif days <= 14:
        urgency = 30
    else:
        urgency = 15

    importance_score = importance * 20
    quick_win = max(0, 15 - min(duration, 15))

    score = round(
        0.55 * urgency
        + 0.40 * importance_score
        + 0.05 * quick_win,
        1
    )

    item["days_until_deadline"] = days
    item["priority_score"] = score

    item["priority_level"] = (
        "High" if score >= 70
        else "Medium" if score >= 45
        else "Low"
    )

    item["explanation"] = (
        f"Urgency={urgency}/100; "
        f"importance={importance}/5; "
        f"duration={duration:g} hour(s); "
        f"deadline in {days} day(s)."
    )

    return item


def prioritise_tasks(tasks: list[dict]) -> list[dict]:
    active_tasks = [
        task for task in tasks
        if not task.get("completed", False)
    ]

    scored_tasks = [
        score_task(task) for task in active_tasks
    ]

    return sorted(
        scored_tasks,
        key=lambda task: task["priority_score"],
        reverse=True
    )
