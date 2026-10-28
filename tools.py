
from prioritiser import days_until


def check_deadlines(tasks: list[dict]) -> list[str]:
    alerts = []

    for task in tasks:
        if task.get("completed", False):
            continue

        days = days_until(task.get("deadline", ""))
        title = task.get("title", "Untitled task")

        if days < 0:
            alerts.append(
                f"OVERDUE: '{title}' was due "
                f"{abs(days)} day(s) ago."
            )
        elif days == 0:
            alerts.append(
                f"DUE TODAY: '{title}' should be addressed today."
            )
        elif days <= 2:
            alerts.append(
                f"COMING SOON: '{title}' is due in {days} day(s)."
            )

    return alerts


def mark_task_completed(
    tasks: list[dict],
    title: str
) -> list[dict]:
    updated_tasks = []

    for task in tasks:
        item = dict(task)

        if item.get("title", "").casefold() == title.casefold():
            item["completed"] = True

        updated_tasks.append(item)

    return updated_tasks


def build_study_schedule(
    prioritised_tasks: list[dict],
    available_hours: float
) -> list[dict]:
    remaining = max(0.0, float(available_hours))
    schedule = []

    for task in prioritised_tasks:
        if remaining <= 0:
            break

        estimated = max(
            0.25,
            float(task.get("duration", 1))
        )

        allocated = min(estimated, remaining)

        schedule.append({
            "task": task["title"],
            "allocated_hours": round(allocated, 2),
            "estimated_hours": round(estimated, 2),
            "status": (
                "Full estimate covered"
                if allocated >= estimated
                else "Partial session; continue later"
            ),
            "priority_score": task.get("priority_score", 0)
        })

        remaining = round(remaining - allocated, 6)

    return schedule
