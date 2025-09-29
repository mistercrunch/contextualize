#!/usr/bin/env python3
"""
Full MCP server implementation for Context Window Management System
This server enables task management with Claude Code integration
"""

import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class TaskLauncherServer:
    """MCP server for managing context-isolated tasks"""

    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.context_dir = Path("context/concepts")
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.current_task_id: Optional[str] = None
        self.server = Server("task-launcher")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools for Claude"""
            return [
                Tool(
                    name="launch_task",
                    description="Launch a new managed task with isolated context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Clear description of the task",
                            },
                            "concepts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Concepts to load for this task",
                            },
                            "context_from_main": {
                                "type": "string",
                                "description": "Additional context from main session",
                            },
                            "parent_id": {
                                "type": "string",
                                "description": "Parent task ID if forking",
                            },
                        },
                        "required": ["description"],
                    },
                ),
                Tool(
                    name="fork_task",
                    description="Fork from existing task with its context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parent_id": {"type": "string", "description": "Task ID to fork from"},
                            "description": {
                                "type": "string",
                                "description": "Description for the new fork",
                            },
                            "additional_concepts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Additional concepts to add",
                            },
                        },
                        "required": ["parent_id", "description"],
                    },
                ),
                Tool(
                    name="complete_task",
                    description="Mark current task as complete with report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Summary of what was accomplished",
                            },
                            "context_learned": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "New context discovered during task",
                            },
                            "artifacts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files or artifacts created",
                            },
                        },
                        "required": ["summary"],
                    },
                ),
                Tool(
                    name="view_dag",
                    description="View task DAG and relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of recent tasks to show",
                                "default": 10,
                            }
                        },
                    },
                ),
                Tool(
                    name="list_concepts",
                    description="List available concepts",
                    inputSchema={"type": "object"},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls from Claude"""

            if name == "launch_task":
                return await self._launch_task(arguments)
            elif name == "fork_task":
                return await self._fork_task(arguments)
            elif name == "complete_task":
                return await self._complete_task(arguments)
            elif name == "view_dag":
                return await self._view_dag(arguments)
            elif name == "list_concepts":
                return await self._list_concepts()
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _launch_task(self, args: Dict[str, Any]) -> List[TextContent]:
        """Launch a new managed task"""
        task_id = str(uuid.uuid4())[:8]
        task_dir = self.logs_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Load concept content
        concepts = args.get("concepts", [])
        concept_content = self._load_concepts(concepts)

        # Prepare metadata
        metadata = {
            "task_id": task_id,
            "description": args.get("description", ""),
            "concepts": concepts,
            "parent_id": args.get("parent_id"),
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        # Save metadata
        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Save input context
        input_data = {
            "concepts": concepts,
            "concept_content": concept_content,
            "context_from_main": args.get("context_from_main", ""),
            "parent_id": args.get("parent_id"),
        }
        (task_dir / "input.json").write_text(json.dumps(input_data, indent=2))

        # Log to DAG
        self._log_to_dag(
            {
                "task_id": task_id,
                "timestamp": metadata["started_at"],
                "description": metadata["description"],
                "parent_id": metadata.get("parent_id"),
                "status": "running",
            }
        )

        # Generate session ID for resumability
        session_id = f"task-{task_id}-{uuid.uuid4().hex[:8]}"
        metadata["session_id"] = session_id
        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Build the prompt for the task
        prompt = self._build_task_prompt(
            args["description"], concept_content, args.get("context_from_main", "")
        )

        # Launch Claude with isolated context
        launch_cmd = ["claude", "--session-id", session_id, "--print", prompt]

        # Execute in background (async)
        result = subprocess.run(launch_cmd, capture_output=True, text=True)

        # Save output
        (task_dir / "output.txt").write_text(result.stdout)
        if result.stderr:
            (task_dir / "error.txt").write_text(result.stderr)

        self.current_task_id = task_id

        return [
            TextContent(
                type="text",
                text=f"✅ Task {task_id} launched\n"
                f"Description: {metadata['description']}\n"
                f"Concepts: {', '.join(concepts)}\n"
                f"Session: {session_id}\n\n"
                f"Output:\n{result.stdout[:500]}...",
            )
        ]

    async def _fork_task(self, args: Dict[str, Any]) -> List[TextContent]:
        """Fork from existing task"""
        parent_id = args["parent_id"]
        parent_dir = self.logs_dir / parent_id

        if not parent_dir.exists():
            # Try partial match
            possible = list(self.logs_dir.glob(f"{parent_id}*"))
            if possible:
                parent_dir = possible[0]
                parent_id = parent_dir.name
            else:
                return [TextContent(type="text", text=f"Parent task {parent_id} not found")]

        # Load parent context
        parent_input = json.loads((parent_dir / "input.json").read_text())

        # Merge concepts
        concepts = list(set(parent_input.get("concepts", []) + args.get("additional_concepts", [])))

        # Launch new task with parent context
        return await self._launch_task(
            {
                "description": args["description"],
                "concepts": concepts,
                "context_from_main": parent_input.get("context_from_main", ""),
                "parent_id": parent_id,
            }
        )

    async def _complete_task(self, args: Dict[str, Any]) -> List[TextContent]:
        """Mark current task as complete"""
        if not self.current_task_id:
            return [TextContent(type="text", text="No active task to complete")]

        task_dir = self.logs_dir / self.current_task_id

        # Create report
        report = {
            "summary": args["summary"],
            "context_learned": args.get("context_learned", []),
            "artifacts": args.get("artifacts", []),
            "completed_at": datetime.now().isoformat(),
        }

        (task_dir / "report.json").write_text(json.dumps(report, indent=2))

        # Update metadata
        metadata = json.loads((task_dir / "metadata.json").read_text())
        metadata["status"] = "completed"
        metadata["completed_at"] = report["completed_at"]
        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Update DAG
        self._log_to_dag(
            {
                "task_id": self.current_task_id,
                "timestamp": report["completed_at"],
                "description": metadata["description"],
                "status": "completed",
            }
        )

        result = f"✅ Task {self.current_task_id} completed\n"
        result += f"Summary: {report['summary']}\n"

        if report["context_learned"]:
            result += f"Learned: {', '.join(report['context_learned'])}\n"

        self.current_task_id = None
        return [TextContent(type="text", text=result)]

    async def _view_dag(self, args: Dict[str, Any]) -> List[TextContent]:
        """View task DAG"""
        dag_file = self.logs_dir / "dag.jsonl"
        if not dag_file.exists():
            return [TextContent(type="text", text="No tasks in DAG yet")]

        tasks = []
        with open(dag_file) as f:
            for line in f:
                tasks.append(json.loads(line))

        limit = args.get("limit", 10)
        recent_tasks = tasks[-limit:]

        output = f"Task DAG (last {limit}):\n\n"

        # Build tree structure
        by_parent = {}
        roots = []

        for task in recent_tasks:
            parent = task.get("parent_id")
            if parent:
                if parent not in by_parent:
                    by_parent[parent] = []
                by_parent[parent].append(task)
            else:
                roots.append(task)

        def format_task(task, indent=0):
            status_icon = {"completed": "✅", "failed": "❌", "running": "🔄", "created": "📝"}.get(
                task.get("status", "unknown"), "❓"
            )

            prefix = "  " * indent + ("└─ " if indent > 0 else "")
            line = f"{prefix}{status_icon} {task['task_id'][:8]}: {task['description'][:40]}"

            children_output = ""
            if task["task_id"] in by_parent:
                for child in by_parent[task["task_id"]]:
                    children_output += "\n" + format_task(child, indent + 1)

            return line + children_output

        for root in roots:
            output += format_task(root) + "\n"

        return [TextContent(type="text", text=output)]

    async def _list_concepts(self) -> List[TextContent]:
        """List available concepts"""
        concepts = []
        for concept_file in self.context_dir.glob("*.md"):
            concepts.append(concept_file.stem)

        output = "Available concepts:\n"
        for concept in sorted(concepts):
            output += f"  - {concept}\n"

        return [TextContent(type="text", text=output)]

    def _load_concepts(self, concepts: List[str]) -> str:
        """Load concept content from files"""
        content = ""
        for concept in concepts:
            concept_file = self.context_dir / f"{concept}.md"
            if concept_file.exists():
                content += f"\n## Concept: {concept}\n"
                content += concept_file.read_text()
                content += "\n"
        return content

    def _build_task_prompt(self, description: str, concepts: str, context: str) -> str:
        """Build prompt for task execution"""
        prompt = f"""You are executing a managed task with isolated context.

TASK: {description}

{concepts}

CONTEXT FROM MAIN SESSION:
{context}

Focus only on this specific task. When complete, use the complete_task tool to report results.
"""
        return prompt

    def _log_to_dag(self, entry: Dict[str, Any]):
        """Append entry to DAG log"""
        dag_file = self.logs_dir / "dag.jsonl"
        with open(dag_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


def main():
    """Main entry point"""
    import asyncio

    server = TaskLauncherServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
