#!/usr/bin/env python3
"""
Monitor background tasks
"""

import json
import os
import time
from pathlib import Path
from typing import Any


def check_task_status(task_id: str) -> dict[str, Any]:
    """Check if a background task is still running"""
    task_dir = Path(f"logs/{task_id}")

    if not task_dir.exists():
        return {"error": "Task not found"}

    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        return {"error": "No metadata"}

    metadata = json.loads(metadata_file.read_text())

    # Check if task has a PID (background task)
    if "pid" in metadata:
        pid = metadata["pid"]

        # Check if process is still running
        try:
            os.kill(pid, 0)  # Signal 0 = check if alive
            metadata["running"] = True
        except ProcessLookupError:
            # Process finished
            metadata["running"] = False

            # Update status if needed
            if metadata.get("status") == "running":
                metadata["status"] = "completed"
                metadata_file.write_text(json.dumps(metadata, indent=2))
    else:
        metadata["running"] = False

    # Check for output
    output_file = task_dir / "output.txt"
    if output_file.exists():
        output = output_file.read_text()
        metadata["has_output"] = bool(output.strip())
        metadata["output_size"] = len(output)

    return metadata


def wait_for_task(task_id: str, timeout: int = 300) -> dict[str, Any]:
    """Wait for a background task to complete"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = check_task_status(task_id)

        if status.get("error"):
            return status

        if not status.get("running", False):
            return status

        time.sleep(1)

    return {"error": "Timeout waiting for task"}


def monitor_all_tasks() -> list:
    """Check status of all recent tasks"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return []

    results = []
    for task_dir in sorted(logs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        if task_dir.is_dir():
            task_id = task_dir.name
            status = check_task_status(task_id)
            results.append(
                {
                    "task_id": task_id,
                    "description": status.get("description", ""),
                    "status": status.get("status", "unknown"),
                    "running": status.get("running", False),
                    "has_output": status.get("has_output", False),
                }
            )

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        status = check_task_status(task_id)
        print(json.dumps(status, indent=2))
    else:
        print("Recent tasks:")
        for task in monitor_all_tasks():
            icon = "🔄" if task["running"] else ("✅" if task["has_output"] else "❓")
            print(f"{icon} {task['task_id']}: {task['status']}")
