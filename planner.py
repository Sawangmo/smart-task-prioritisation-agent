
from datetime import date, datetime, time, timedelta


DEFAULT_START = "17:30"
DEFAULT_END = "21:00"
DEFAULT_BREAK_MINUTES = 10
DEFAULT_SESSION_MINUTES = 50
DEFAULT_MAX_DAYS = 30


def _parse_time(value: str) -> time:
    """Convert HH:MM text into a time object."""
    return datetime.strptime(value, "%H:%M").time()


def _task_deadline(task: dict) -> date:
    """Parse a task deadline; use today when it is invalid."""
    try:
        return date.fromisoformat(str(task.get("deadline", ""))[:10])
    except (ValueError, TypeError):
        return date.today()


def _task_id(task: dict) -> str:
    """Return a stable identifier for timetable progress."""
    if task.get("id") is not None:
        return str(task["id"])
    return str(task.get("title", "Untitled task"))


def build_multi_day_timetable(
    prioritised_tasks: list[dict],
    start_date: date | None = None,
    study_start: str = DEFAULT_START,
    study_end: str = DEFAULT_END,
    break_minutes: int = DEFAULT_BREAK_MINUTES,
    session_minutes: int = DEFAULT_SESSION_MINUTES,
    max_days: int = DEFAULT_MAX_DAYS,
) -> dict:
    """
    Create daily study sessions across multiple days.

    Sessions are scheduled in priority order while respecting task
    deadlines. Overdue tasks may be scheduled today as recovery work,
    but are not silently scheduled on future dates after their deadline.

    Returns:
        {
            "sessions": list[dict],
            "unscheduled_tasks": list[dict],
            "study_start": str,
            "study_end": str,
        }
    """
    today = start_date or date.today()
    start_clock = _parse_time(study_start)
    end_clock = _parse_time(study_end)

    start_minute = start_clock.hour * 60 + start_clock.minute
    end_minute = end_clock.hour * 60 + end_clock.minute

    if end_minute <= start_minute:
        raise ValueError("Study end time must be later than start time.")

    if break_minutes < 0 or session_minutes <= 0 or max_days < 1:
        raise ValueError("Break, session, or planning settings are invalid.")

    # Ignore completed tasks and prepare remaining work in minutes.
    tasks = []
    remaining_minutes = {}

    for original in prioritised_tasks:
        if original.get("completed", False):
            continue

        task = dict(original)
        task_id = _task_id(task)

        try:
            hours = max(0.0, float(task.get("duration", 1)))
        except (ValueError, TypeError):
            hours = 1.0

        remaining = int(round(hours * 60))

        if remaining <= 0:
            continue

        task["_planner_id"] = task_id
        task["_planner_deadline"] = _task_deadline(task)
        tasks.append(task)
        remaining_minutes[task_id] = remaining

    # Earlier deadlines first, then higher priority.
    tasks.sort(
        key=lambda task: (
            task["_planner_deadline"],
            -float(task.get("priority_score", 0)),
        )
    )

    sessions = []
    session_number_by_day = {}

    for day_offset in range(max_days):
        current_date = today + timedelta(days=day_offset)
        cursor = start_minute
        day_session_number = 0

        # A past-deadline task is scheduled today only as recovery work.
        eligible_tasks = [
            task for task in tasks
            if remaining_minutes[task["_planner_id"]] > 0
            and (
                task["_planner_deadline"] >= current_date
                or (
                    day_offset == 0
                    and task["_planner_deadline"] < today
                )
            )
        ]

        for task in eligible_tasks:
            task_id = task["_planner_id"]

            while remaining_minutes[task_id] > 0:
                if cursor >= end_minute:
                    break

                available = end_minute - cursor
                chunk = min(
                    session_minutes,
                    remaining_minutes[task_id],
                    available,
                )

                # If another session would require a break, ensure the
                # remaining window can fit both the break and some work.
                if (
                    day_session_number > 0
                    and cursor + chunk > end_minute
                ):
                    break

                session_start = cursor
                session_end = cursor + chunk

                day_session_number += 1
                session_number_by_day[current_date.isoformat()] = (
                    day_session_number
                )

                session_id = (
                    f"{current_date.isoformat()}-"
                    f"{task_id}-{day_session_number}"
                )

                remaining_minutes[task_id] -= chunk

                sessions.append(
                    {
                        "session_id": session_id,
                        "task_id": task_id,
                        "date": current_date.isoformat(),
                        "start_time": (
                            f"{session_start // 60:02d}:"
                            f"{session_start % 60:02d}"
                        ),
                        "end_time": (
                            f"{session_end // 60:02d}:"
                            f"{session_end % 60:02d}"
                        ),
                        "task": task.get("title", "Untitled task"),
                        "category": task.get("category", "Other"),
                        "duration_minutes": chunk,
                        "allocated_hours": round(chunk / 60, 2),
                        "estimated_hours": round(
                            float(task.get("duration", 1)), 2
                        ),
                        "priority_score": float(
                            task.get("priority_score", 0)
                        ),
                        "priority_level": task.get(
                            "priority_level", "Unspecified"
                        ),
                        "deadline": task.get("deadline", ""),
                        "completed": False,
                    }
                )

                cursor = session_end

                if remaining_minutes[task_id] <= 0:
                    break

                # Add a break only when another study session can fit.
                if cursor + break_minutes < end_minute:
                    cursor += break_minutes
                else:
                    break

            if cursor >= end_minute:
                break

        if all(value <= 0 for value in remaining_minutes.values()):
            break

    unscheduled_tasks = []

    for task in tasks:
        task_id = task["_planner_id"]
        remaining = remaining_minutes[task_id]

        if remaining > 0:
            deadline = task["_planner_deadline"]
            if deadline < today:
                reason = "Overdue; remaining work needs a recovery plan."
            elif deadline >= today + timedelta(days=max_days):
                reason = "Beyond the planning horizon."
            else:
                reason = "Insufficient available time before the deadline."

            unscheduled_tasks.append(
                {
                    "task_id": task_id,
                    "task": task.get("title", "Untitled task"),
                    "deadline": task.get("deadline", ""),
                    "remaining_minutes": remaining,
                    "reason": reason,
                }
            )

    return {
        "sessions": sessions,
        "unscheduled_tasks": unscheduled_tasks,
        "study_start": study_start,
        "study_end": study_end,
    }


def make_plan(
    prioritised_tasks: list[dict],
    available_hours: float,
) -> list[dict]:
    """
    Backward-compatible daily plan for the existing dashboard.

    available_hours limits study work; the timetable also respects
    the configured 17:30–21:00 study window and includes breaks.
    """
    result = build_multi_day_timetable(
        prioritised_tasks,
        max_days=1,
    )

    sessions = result["sessions"]
    budget_minutes = max(0, int(float(available_hours) * 60))
    selected = []
    used_minutes = 0

    for session in sessions:
        minutes = int(session["duration_minutes"])

        if used_minutes + minutes > budget_minutes:
            remaining = budget_minutes - used_minutes

            if remaining <= 0:
                break

            session = dict(session)
            session["duration_minutes"] = remaining
            session["allocated_hours"] = round(remaining / 60, 2)
            session["end_time"] = (
                f"{int(session['start_time'][:2]):02d}:"
                f"{int(session['start_time'][3:]):02d}"
            )
            start = (
                int(session["start_time"][:2]) * 60
                + int(session["start_time"][3:])
            )
            end = start + remaining
            session["end_time"] = f"{end // 60:02d}:{end % 60:02d}"

            selected.append(session)
            used_minutes += remaining
            break

        selected.append(session)
        used_minutes += minutes

    # Keep the keys expected by the existing Agent Plan table.
    return [
        {
            "task": item["task"],
            "allocated_hours": item["allocated_hours"],
            "estimated_hours": item["estimated_hours"],
            "status": "Scheduled in timetable",
            "start_time": item["start_time"],
            "end_time": item["end_time"],
            "date": item["date"],
            "session_id": item["session_id"],
        }
        for item in selected
    ]
