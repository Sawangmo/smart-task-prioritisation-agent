
from datetime import date, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from prioritiser import prioritise_tasks
from tools import check_deadlines, build_study_schedule

today = date.today()

test_cases = [
    {
        "name": "Urgent task ranks first",
        "tasks": [
            {
                "title": "Long-term reading",
                "deadline": (today + timedelta(days=20)).isoformat(),
                "importance": 2,
                "duration": 2
            },
            {
                "title": "Assignment due tomorrow",
                "deadline": (today + timedelta(days=1)).isoformat(),
                "importance": 5,
                "duration": 3
            }
        ],
        "expected_top": "Assignment due tomorrow"
    },
    {
        "name": "Importance affects ranking",
        "tasks": [
            {
                "title": "Optional reading",
                "deadline": (today + timedelta(days=5)).isoformat(),
                "importance": 1,
                "duration": 1
            },
            {
                "title": "Major project",
                "deadline": (today + timedelta(days=5)).isoformat(),
                "importance": 5,
                "duration": 2
            }
        ],
        "expected_top": "Major project"
    },
    {
        "name": "Overdue task triggers an alert",
        "tasks": [
            {
                "title": "Missed quiz",
                "deadline": (today - timedelta(days=1)).isoformat(),
                "importance": 4,
                "duration": 1
            }
        ],
        "expected_top": "Missed quiz",
        "expect_overdue": True
    }
]

results = []

for case in test_cases:
    ranked = prioritise_tasks(case["tasks"])
    actual_top = ranked[0]["title"] if ranked else None

    passed = actual_top == case["expected_top"]

    if case.get("expect_overdue"):
        passed = passed and any(
            "OVERDUE" in alert
            for alert in check_deadlines(case["tasks"])
        )

    results.append({
        "test": case["name"],
        "passed": bool(passed)
    })

    print(
        f"{'PASS' if passed else 'FAIL'}: {case['name']}"
    )

# Test schedule time constraint
sample_tasks = prioritise_tasks([
    {
        "title": "Task A",
        "deadline": (today + timedelta(days=1)).isoformat(),
        "importance": 4,
        "duration": 2
    },
    {
        "title": "Task B",
        "deadline": (today + timedelta(days=2)).isoformat(),
        "importance": 3,
        "duration": 2
    }
])

budget = 1.5
schedule = build_study_schedule(sample_tasks, budget)

allocated = sum(
    item["allocated_hours"] for item in schedule
)

feasible = allocated <= budget

results.append({
    "test": "Schedule respects available hours",
    "passed": feasible
})

print(
    f"{'PASS' if feasible else 'FAIL'}: "
    "Schedule respects available hours"
)

df = pd.DataFrame(results)
pass_rate = 100 * df["passed"].mean()

print(
    f"\nPass rate: {df['passed'].sum()}/"
    f"{len(df)} ({pass_rate:.1f}%)"
)

df.to_csv("evaluation_results.csv", index=False)

fig, ax = plt.subplots()
counts = (
    df["passed"]
    .map({True: "PASS", False: "FAIL"})
    .value_counts()
)

ax.bar(counts.index, counts.values)
ax.set_title(f"Evaluation outcomes ({pass_rate:.1f}% pass rate)")
ax.set_ylabel("Number of tests")

fig.tight_layout()
fig.savefig("evaluation_chart.png", dpi=150)
plt.show()
