#!/usr/bin/env python3
"""
Async task launcher for background execution
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class AsyncTaskLauncher:
    """Manages async task execution in background"""

    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.running_tasks: dict[str, asyncio.Task] = {}

    async def launch_task(
        self,
        description: str,
        concepts: list[str],
        context_from_main: str = "",
        parent_id: str | None = None,
    ) -> str:
        """Launch an async task in background"""
        task_id = str(uuid.uuid4())[:8]
        task_dir = self.logs_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            "task_id": task_id,
            "description": description,
            "concepts": concepts,
            "parent_id": parent_id,
            "started_at": datetime.now().isoformat(),
            "status": "running",
            "async": True,
        }

        # Generate session ID (must be valid UUID for Claude)
        session_id = str(uuid.uuid4())
        metadata["session_id"] = session_id

        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Save input
        input_data = {
            "concepts": concepts,
            "context_from_main": context_from_main,
            "parent_id": parent_id,
        }
        (task_dir / "input.json").write_text(json.dumps(input_data, indent=2))

        # Log to DAG
        self._log_to_dag(
            {
                "task_id": task_id,
                "timestamp": metadata["started_at"],
                "description": description,
                "parent_id": parent_id,
                "status": "running",
                "async": True,
            }
        )

        # Build prompt
        prompt = self._build_prompt(description, concepts, context_from_main)

        # Launch async task
        task = asyncio.create_task(self._execute_task(task_id, session_id, prompt))
        self.running_tasks[task_id] = task

        return task_id

    async def _execute_task(self, task_id: str, session_id: str, prompt: str):
        """Execute task in background"""
        task_dir = self.logs_dir / task_id

        try:
            # Run Claude subprocess
            process = await asyncio.create_subprocess_exec(
                "claude",
                "--session-id",
                session_id,
                "--print",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Stream output to file
            output_file = task_dir / "output.txt"
            error_file = task_dir / "error.txt"

            with open(output_file, "w") as out_f:
                async for line in process.stdout:
                    out_f.write(line.decode())
                    out_f.flush()

            stdout, stderr = await process.communicate()

            if stderr:
                error_file.write_text(stderr.decode())

            # Update status
            metadata_file = task_dir / "metadata.json"
            metadata = json.loads(metadata_file.read_text())
            metadata["status"] = "completed" if process.returncode == 0 else "failed"
            metadata["completed_at"] = datetime.now().isoformat()
            metadata_file.write_text(json.dumps(metadata, indent=2))

            # Update DAG
            self._log_to_dag(
                {
                    "task_id": task_id,
                    "timestamp": metadata["completed_at"],
                    "description": metadata["description"],
                    "status": metadata["status"],
                    "async": True,
                }
            )

        except Exception as e:
            # Log error
            error_file = task_dir / "error.txt"
            error_file.write_text(f"Exception: {str(e)}")

            # Update status
            metadata_file = task_dir / "metadata.json"
            metadata = json.loads(metadata_file.read_text())
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            metadata_file.write_text(json.dumps(metadata, indent=2))

        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def _build_prompt(self, description: str, concepts: list[str], context: str) -> str:
        """Build task prompt"""
        concepts_content = self._load_concepts(concepts)

        return f"""You are executing an async managed task.

TASK: {description}

CONCEPTS:
{concepts_content}

CONTEXT:
{context}

Complete this task independently. The session will be saved for later review."""

    def _load_concepts(self, concepts: list[str]) -> str:
        """Load concept content"""
        content = ""
        concepts_dir = Path("context/concepts")

        for concept in concepts:
            concept_file = concepts_dir / f"{concept}.md"
            if concept_file.exists():
                content += f"\n## {concept}\n"
                content += concept_file.read_text()
                content += "\n"

        return content

    def _log_to_dag(self, entry: dict[str, Any]):
        """Append to DAG log"""
        dag_file = self.logs_dir / "dag.jsonl"
        with open(dag_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def get_status(self, task_id: str) -> dict[str, Any]:
        """Get task status"""
        task_dir = self.logs_dir / task_id
        metadata_file = task_dir / "metadata.json"

        if not metadata_file.exists():
            return {"error": "Task not found"}

        metadata = json.loads(metadata_file.read_text())

        # Check if still running
        if task_id in self.running_tasks:
            metadata["running"] = True
        else:
            metadata["running"] = False

        # Get output preview if exists
        output_file = task_dir / "output.txt"
        if output_file.exists():
            output = output_file.read_text()
            metadata["output_preview"] = output[:500]

        return metadata

    async def wait_for_task(self, task_id: str) -> dict[str, Any]:
        """Wait for task completion"""
        if task_id in self.running_tasks:
            await self.running_tasks[task_id]

        return await self.get_status(task_id)

    def list_running_tasks(self) -> list[str]:
        """List currently running task IDs"""
        return list(self.running_tasks.keys())


async def main():
    """Test async launcher"""
    launcher = AsyncTaskLauncher()

    # Launch test task
    task_id = await launcher.launch_task(
        description="Test async task",
        concepts=["python", "testing"],
        context_from_main="This is a test of async execution",
    )

    print(f"Launched async task: {task_id}")

    # Wait a bit
    await asyncio.sleep(2)

    # Check status
    status = await launcher.get_status(task_id)
    print(f"Status: {status}")

    # Wait for completion
    print("Waiting for completion...")
    final_status = await launcher.wait_for_task(task_id)
    print(f"Final status: {final_status}")


if __name__ == "__main__":
    asyncio.run(main())
