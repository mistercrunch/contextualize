#!/usr/bin/env python3
"""
Simple synchronous task launcher for Contextualize
"""

import json
import subprocess
import uuid
from datetime import datetime

from .concept_models import ConceptCollection
from .models import Task, TaskCollection, TaskStatus


def launch_task(
    description: str,
    concepts: list[str] = None,
    context_from_main: str = "",
    parent_id: str | None = None,
    background: bool = False,
    generate_report: bool = False,
    report_template: str | None = None,
) -> str:
    """Launch a task with Claude"""

    # Generate IDs
    task_id = str(uuid.uuid4())[:8]
    session_id = str(uuid.uuid4())

    # Create Task object
    task = Task(
        task_id=task_id,
        description=description,
        status=TaskStatus.CREATED,
        concepts=concepts or [],
        context_from_main=context_from_main,
        parent_id=parent_id,
        session_id=session_id,
        started_at=datetime.now(),
        report_template=report_template,
    )

    # Add to collection (creates directory and saves metadata)
    collection = TaskCollection()
    collection.add(task)

    # Load concepts using ConceptCollection
    concept_content = ""
    if concepts:
        concept_collection = ConceptCollection()
        concept_content = concept_collection.load_with_dependencies(concepts)

    # Save input data for reference
    input_data = {
        "concepts": concepts or [],
        "concept_content": concept_content,
        "context_from_main": context_from_main,
        "parent_id": parent_id,
    }
    input_file = task.task_dir / "input.json"
    input_file.write_text(json.dumps(input_data, indent=2))

    # Build prompt
    prompt = f"""You are executing a Contextualize managed task.

TASK: {description}

LOADED CONCEPTS:
{concept_content}

ADDITIONAL CONTEXT:
{context_from_main}

Please complete this task. Your work will be logged and can be resumed later."""

    print(f"✅ Task {task_id} created")
    print(f"📝 Description: {description}")
    print(f"🔗 Session: {session_id}")
    print(f"📚 Concepts: {', '.join(concepts) if concepts else 'none'}")
    print("\n" + "=" * 60 + "\n")

    # Launch Claude
    # Use --print for one-shot execution (exits after response)
    cmd = ["claude", "--session-id", session_id, "--print"]

    # Update task status to running
    task.status = TaskStatus.RUNNING
    task.save()

    if background:
        # Launch in background
        with (
            open(task.task_dir / "output.txt", "w") as out_f,
            open(task.task_dir / "error.txt", "w") as err_f,
        ):
            process = subprocess.Popen(cmd + [prompt], stdout=out_f, stderr=err_f)
            print(f"🚀 Task running in background (PID: {process.pid})")
            print(f"Check status: ctx task show {task_id}")

            # Store PID for monitoring
            task.pid = process.pid
            task.save()
    else:
        # Run interactively - pipe to stdout
        print("🚀 Launching Claude session...")
        print("=" * 60 + "\n")

        # Save prompt for reference
        (task.task_dir / "prompt.txt").write_text(prompt)

        # Run and stream output
        result = subprocess.run(
            cmd + [prompt],
            capture_output=False,  # Let output go to terminal
            text=True,
        )

        # Update task status
        if result.returncode == 0:
            task.update_status(TaskStatus.COMPLETED)
        else:
            task.update_status(TaskStatus.FAILED)

        print("\n" + "=" * 60)
        print(f"✅ Task {task_id} {task.status.value}")
        print(f"Resume later: ctx task resume {task_id}")

        # Generate report if requested
        if generate_report and task.status == TaskStatus.COMPLETED:
            from .report_generator import ReportGenerator

            print("\n🔄 Generating report...")
            generator = ReportGenerator()
            if generator.generate_report(task_id):
                print(f"📄 Report generated: logs/{task_id}/report.md")
            else:
                print("⚠️  Report generation failed")

    return task_id


if __name__ == "__main__":
    # Test
    import sys

    if len(sys.argv) > 1:
        task_id = launch_task(
            description=" ".join(sys.argv[1:]), concepts=["core"], background=False
        )
        print(f"\nTask ID: {task_id}")
    else:
        print("Usage: python launcher.py <task description>")
