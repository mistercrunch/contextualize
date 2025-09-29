#!/usr/bin/env python3
"""
Task Launcher using Claude Code Python SDK
This creates a custom MCP server that provides task management tools
"""

import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import asyncio

# Claude Code SDK imports
from mcp import tool
from claude_code_sdk import ClaudeSDKClient


class TaskFramework:
    """Manages task execution with context isolation and logging"""

    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.context_dir = Path("context/concepts")
        self.dag_file = self.logs_dir / "dag.jsonl"

    def load_concepts(self, concept_names: list[str]) -> str:
        """Load specified concept files"""
        loaded_context = []
        for concept_name in concept_names:
            concept_file = self.context_dir / f"{concept_name}.md"
            if concept_file.exists():
                content = concept_file.read_text()
                loaded_context.append(f"# Concept: {concept_name}\n{content}")
            else:
                loaded_context.append(f"# Warning: Concept {concept_name} not found")

        return "\n\n".join(loaded_context)

    def create_task(
        self,
        description: str,
        parent_id: Optional[str] = None,
        concepts: Optional[list[str]] = None,
    ) -> dict:
        """Create a new task with metadata"""
        task_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        task_dir = self.logs_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "task_id": task_id,
            "session_id": session_id,
            "parent_id": parent_id,
            "description": description,
            "concepts": concepts or [],
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Update DAG
        dag_entry = {
            "task_id": task_id,
            "parent_id": parent_id,
            "timestamp": metadata["started_at"],
            "description": description,
            "status": "running",
        }
        with open(self.dag_file, "a") as f:
            f.write(json.dumps(dag_entry) + "\n")

        return metadata

    def complete_task(self, task_id: str, status: str, report: dict) -> None:
        """Mark task as completed and save report"""
        task_dir = self.logs_dir / task_id

        # Save report
        (task_dir / "report.json").write_text(json.dumps(report, indent=2))

        # Update metadata
        metadata_file = task_dir / "metadata.json"
        metadata = json.loads(metadata_file.read_text())
        metadata["status"] = status
        metadata["completed_at"] = datetime.now().isoformat()
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Update DAG
        dag_entry = {
            "task_id": task_id,
            "parent_id": metadata.get("parent_id"),
            "timestamp": metadata["completed_at"],
            "description": metadata["description"],
            "status": status,
        }
        with open(self.dag_file, "a") as f:
            f.write(json.dumps(dag_entry) + "\n")


# Initialize the framework
framework = TaskFramework()


# Define custom tools using the SDK's @tool decorator


@tool(
    name="launch_task",
    description="Launch a new managed task with context isolation",
    input_schema={
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Task description"},
            "concepts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of concepts to load",
            },
            "parent_id": {"type": "string", "description": "Parent task ID (optional)"},
            "context_from_main": {
                "type": "string",
                "description": "Additional context from main agent",
            },
            "relevant_info": {
                "type": "object",
                "description": "Structured info from main agent (files, errors, etc.)",
            },
        },
        "required": ["description"],
    },
)
async def launch_task(args: dict[str, Any]) -> dict[str, Any]:
    """Launch a new task with isolated context"""
    try:
        # Create task
        metadata = framework.create_task(
            description=args["description"],
            parent_id=args.get("parent_id"),
            concepts=args.get("concepts", []),
        )

        # Capture ALL input from main agent
        task_dir = framework.logs_dir / metadata["task_id"]

        # Save the complete input
        input_data = {
            "description": args["description"],
            "concepts_requested": args.get("concepts", []),
            "parent_task": args.get("parent_id"),
            "context_from_main": args.get("context_from_main", ""),
            "relevant_info": args.get("relevant_info", {}),
            "timestamp": datetime.now().isoformat(),
        }
        (task_dir / "input.json").write_text(json.dumps(input_data, indent=2))

        # If main agent provided context, save it as markdown too
        if args.get("context_from_main"):
            (task_dir / "context_from_main.md").write_text(
                f"# Context from Main Agent\n\n{args['context_from_main']}"
            )

        # Load context
        concept_context = framework.load_concepts(metadata["concepts"])

        # Build the complete prompt with all context
        prompt_parts = [f"# Task: {metadata['description']}", f"## Task ID: {metadata['task_id']}"]

        # Add context from main agent if provided
        if args.get("context_from_main"):
            prompt_parts.append(f"""
## Context from Main Agent:
{args['context_from_main']}
""")

        # Add relevant info if provided
        if args.get("relevant_info"):
            prompt_parts.append(f"""
## Relevant Information:
```json
{json.dumps(args['relevant_info'], indent=2)}
```
""")

        # Add loaded concepts
        prompt_parts.append(f"""
## Loaded Concepts:
{concept_context}

## Instructions:
Execute the task described above using the provided context and loaded concepts.
When complete, use the complete_task tool to save your report.
""")

        prompt = "\n".join(prompt_parts)

        # Launch Claude subprocess with the task
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--output-format",
                "json",
                "--session-id",
                metadata["session_id"],
                prompt,
            ],
            capture_output=True,
            text=True,
        )

        # Save output
        task_dir = framework.logs_dir / metadata["task_id"]
        (task_dir / "output.json").write_text(result.stdout)
        (task_dir / "stderr.txt").write_text(result.stderr)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Task launched: {metadata['task_id']}\nSession: {metadata['session_id']}\nLogging to: logs/{metadata['task_id']}/",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error launching task: {str(e)}"}],
            "is_error": True,
        }


@tool(
    name="complete_task",
    description="Complete a task and save the report",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Task ID to complete"},
            "status": {
                "type": "string",
                "enum": ["completed", "failed"],
                "description": "Task completion status",
            },
            "summary": {"type": "string", "description": "Summary of what was accomplished"},
            "files_modified": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of files modified",
            },
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Issues encountered",
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggested follow-up tasks",
            },
        },
        "required": ["task_id", "status", "summary"],
    },
)
async def complete_task(args: dict[str, Any]) -> dict[str, Any]:
    """Mark a task as complete with a report"""
    try:
        report = {
            "summary": args["summary"],
            "files_modified": args.get("files_modified", []),
            "issues_encountered": args.get("issues", []),
            "next_steps": args.get("next_steps", []),
        }

        framework.complete_task(task_id=args["task_id"], status=args["status"], report=report)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Task {args['task_id']} marked as {args['status']}\nReport saved to: logs/{args['task_id']}/report.json",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error completing task: {str(e)}"}],
            "is_error": True,
        }


@tool(
    name="fork_task",
    description="Fork from an existing task to try a different approach",
    input_schema={
        "type": "object",
        "properties": {
            "parent_task_id": {"type": "string", "description": "Task ID to fork from"},
            "description": {"type": "string", "description": "Description of new approach"},
        },
        "required": ["parent_task_id", "description"],
    },
)
async def fork_task(args: dict[str, Any]) -> dict[str, Any]:
    """Fork from an existing task"""
    try:
        # Load parent metadata
        parent_dir = framework.logs_dir / args["parent_task_id"]
        if not parent_dir.exists():
            raise ValueError(f"Parent task {args['parent_task_id']} not found")

        parent_metadata = json.loads((parent_dir / "metadata.json").read_text())

        # Create forked task with parent's concepts
        metadata = framework.create_task(
            description=args["description"],
            parent_id=args["parent_task_id"],
            concepts=parent_metadata.get("concepts", []),
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Forked task: {metadata['task_id']}\nFrom parent: {args['parent_task_id']}\nInherited concepts: {', '.join(metadata['concepts'])}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error forking task: {str(e)}"}],
            "is_error": True,
        }


@tool(
    name="view_dag",
    description="View the task DAG structure",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of recent tasks to show",
                "default": 10,
            }
        },
    },
)
async def view_dag(args: dict[str, Any]) -> dict[str, Any]:
    """View the current task DAG"""
    try:
        if not framework.dag_file.exists():
            return {"content": [{"type": "text", "text": "No tasks in DAG yet"}]}

        # Read DAG entries
        tasks = []
        with open(framework.dag_file) as f:
            for line in f:
                tasks.append(json.loads(line))

        # Get recent tasks
        limit = args.get("limit", 10)
        recent_tasks = tasks[-limit:] if len(tasks) > limit else tasks

        # Format as tree
        tree_view = []
        for task in recent_tasks:
            indent = "  └─ " if task.get("parent_id") else ""
            status_icon = (
                "✅"
                if task["status"] == "completed"
                else "❌"
                if task["status"] == "failed"
                else "🔄"
            )
            tree_view.append(
                f"{indent}{status_icon} {task['task_id'][:8]}: {task['description'][:50]}"
            )

        dag_text = "\n".join(tree_view)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Task DAG (last {len(recent_tasks)} tasks):\n\n{dag_text}\n\nTotal tasks: {len(tasks)}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error viewing DAG: {str(e)}"}],
            "is_error": True,
        }


# Main entry point for the MCP server
if __name__ == "__main__":
    # This would be run as an MCP server
    # Launch with: claude --mcp-config task-framework-mcp.json
    print("Task Framework MCP Server")
    print("Available tools:")
    print("- launch_task: Start a new managed task")
    print("- complete_task: Mark task as complete")
    print("- fork_task: Fork from existing task")
    print("- view_dag: View task hierarchy")
