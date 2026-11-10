import argparse
import csv
import json
import math
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((p / 100) * len(ordered)) - 1)
    return ordered[index]


def api_request(url, method="GET", data=None, timeout=10):
    body = json.dumps(data).encode("utf-8") if data is not None else None

    request = Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"}
    )

    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def process_registration(number, base_url, poll_interval, request_timeout):
    started = time.perf_counter()
    result = {
        "number": number,
        "request_id": "",
        "status": "FAILED",
        "submission_latency_seconds": 0.0,
        "completion_latency_seconds": 0.0,
        "error": ""
    }

    try:
        payload = {
            "student_name": f"Benchmark User {number}",
            "email": f"benchmark_{uuid.uuid4().hex[:12]}@example.com",
            "event_name": "QueueScale Performance Benchmark"
        }

        submit_started = time.perf_counter()

        response = api_request(
            f"{base_url}/registrations",
            method="POST",
            data=payload,
            timeout=request_timeout
        )

        result["submission_latency_seconds"] = (
            time.perf_counter() - submit_started
        )

        request_id = response["request_id"]
        result["request_id"] = request_id

        deadline = time.perf_counter() + request_timeout

        while time.perf_counter() < deadline:
            registration = api_request(
                f"{base_url}/registrations/{request_id}",
                timeout=request_timeout
            )

            status = registration["status"]

            if status == "COMPLETED":
                result["status"] = "COMPLETED"
                break

            if status == "FAILED":
                result["status"] = "FAILED"
                result["error"] = "Registration processing failed"
                break

            time.sleep(poll_interval)

        if result["status"] != "COMPLETED" and not result["error"]:
            result["error"] = "Timed out waiting for completion"

    except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as error:
        result["error"] = str(error)

    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"

    result["completion_latency_seconds"] = time.perf_counter() - started

    return result


def main():
    parser = argparse.ArgumentParser(
        description="QueueScale performance benchmark"
    )

    parser.add_argument("--url", default="http://localhost:8001")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", default="")

    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("Requests and concurrency must both be positive.")

    base_url = args.url.rstrip("/")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"benchmark_{timestamp}.csv"

    print("\nQueueScale Performance Benchmark")
    print("--------------------------------")
    print(f"API URL:       {base_url}")
    print(f"Total requests: {args.requests}")
    print(f"Concurrency:    {args.concurrency}")
    print("Starting benchmark...\n")

    benchmark_started = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                process_registration,
                number,
                base_url,
                args.poll_interval,
                args.timeout
            )
            for number in range(1, args.requests + 1)
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            print(
                f"Request {result['number']:>3}: "
                f"{result['status']}"
            )

    total_duration = time.perf_counter() - benchmark_started

    completed = [
        item for item in results if item["status"] == "COMPLETED"
    ]

    failed = len(results) - len(completed)

    submission_latencies = [
        item["submission_latency_seconds"] for item in results
        if item["request_id"]
    ]

    completion_latencies = [
        item["completion_latency_seconds"] for item in completed
    ]

    throughput = (
        len(completed) / total_duration if total_duration > 0 else 0
    )

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "number",
                "request_id",
                "status",
                "submission_latency_seconds",
                "completion_latency_seconds",
                "error"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n========== BENCHMARK RESULTS ==========")
    print(f"Total requests:              {len(results)}")
    print(f"Successful registrations:    {len(completed)}")
    print(f"Failed registrations:        {failed}")
    print(f"Total duration:              {total_duration:.2f} seconds")
    print(f"Throughput:                  {throughput:.2f} registrations/sec")

    if submission_latencies:
        print(
            "Average submission latency:  "
            f"{sum(submission_latencies) / len(submission_latencies):.3f} sec"
        )
        print(
            "P95 submission latency:      "
            f"{percentile(submission_latencies, 95):.3f} sec"
        )

    if completion_latencies:
        print(
            "Average completion latency:  "
            f"{sum(completion_latencies) / len(completion_latencies):.3f} sec"
        )
        print(
            "P95 completion latency:      "
            f"{percentile(completion_latencies, 95):.3f} sec"
        )

    print(f"\nDetailed results saved to: {Path(output_file).resolve()}")


if __name__ == "__main__":
    main()
