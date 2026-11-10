
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent

FILES = {
    "Fixed Workers (50)": "fixed_workers_benchmark_50.csv",
    "KEDA (50)": "keda_benchmark_50.csv",
    "KEDA Dashboard (50)": "keda_dashboard_test_50.csv",
    "KEDA (100)": "keda_benchmark_100.csv"
}


def percentile(values, p):
    values = sorted(values)
    if not values:
        return 0.0

    index = max(0, math.ceil(p / 100 * len(values)) - 1)
    return values[index]


results = {}

for label, filename in FILES.items():
    with open(BASE_DIR / filename, newline="") as file:
        rows = list(csv.DictReader(file))

    completed = [
        row for row in rows
        if row["status"] == "COMPLETED"
    ]

    completion = [
        float(row["completion_latency_seconds"])
        for row in completed
    ]

    submission = [
        float(row["submission_latency_seconds"])
        for row in rows
        if row["request_id"]
    ]

    results[label] = {
        "avg_completion": (
            sum(completion) / len(completion) if completion else 0
        ),
        "p95_completion": percentile(completion, 95),
        "avg_submission": (
            sum(submission) / len(submission) if submission else 0
        )
    }


def create_graph(metric, title, ylabel, filename):
    labels = list(results.keys())
    values = [results[label][metric] for label in labels]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values)

    plt.title(title, fontsize=14)
    plt.xlabel("Benchmark Configuration")
    plt.ylabel(ylabel)
    plt.xticks(rotation=15, ha="right")
    plt.grid(axis="y", alpha=0.3)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(BASE_DIR / filename, dpi=300)
    plt.close()

    print("Generated:", filename)


create_graph(
    "avg_completion",
    "Average Registration Completion Latency",
    "Time (seconds)",
    "average_completion_latency.png"
)

create_graph(
    "p95_completion",
    "P95 Registration Completion Latency",
    "Time (seconds)",
    "p95_completion_latency.png"
)

create_graph(
    "avg_submission",
    "Average API Submission Latency",
    "Time (seconds)",
    "average_submission_latency.png"
)

print("\nAll performance graphs generated successfully.")