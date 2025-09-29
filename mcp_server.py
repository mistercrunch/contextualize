#!/usr/bin/env python3
"""
Minimal MCP server for task management POC
This is a simplified version we can actually run and test
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime


# Simple mock for the MCP protocol
class SimpleMCPServer:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.context_dir = Path("context/concepts")

    def handle_request(self, request):
        """Handle incoming MCP request"""
        if request["method"] == "tools/list":
            return self.list_tools()
        elif request["method"] == "tools/call":
            return self.call_tool(request["params"])

    def list_tools(self):
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "launch_task",
                    "description": "Launch a new managed task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "concepts": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                {"name": "view_dag", "description": "View task DAG", "inputSchema": {}},
            ]
        }

    def call_tool(self, params):
        """Call a specific tool"""
        tool_name = params["name"]
        args = params.get("arguments", {})

        if tool_name == "launch_task":
            return self.launch_task(args)
        elif tool_name == "view_dag":
            return self.view_dag(args)

    def launch_task(self, args):
        """Launch a new task"""
        task_id = str(uuid.uuid4())[:8]
        task_dir = self.logs_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            "task_id": task_id,
            "description": args.get("description", ""),
            "concepts": args.get("concepts", []),
            "started_at": datetime.now().isoformat(),
            "status": "created",
        }

        (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Log to DAG
        dag_file = self.logs_dir / "dag.jsonl"
        with open(dag_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "task_id": task_id,
                        "timestamp": metadata["started_at"],
                        "description": metadata["description"],
                        "status": "created",
                    }
                )
                + "\n"
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Task {task_id} created\nDescription: {metadata['description']}\nConcepts: {', '.join(metadata['concepts'])}",
                }
            ]
        }

    def view_dag(self, args):
        """View the task DAG"""
        dag_file = self.logs_dir / "dag.jsonl"
        if not dag_file.exists():
            return {"content": [{"type": "text", "text": "No tasks yet"}]}

        tasks = []
        with open(dag_file) as f:
            for line in f:
                tasks.append(json.loads(line))

        output = "Task DAG:\n"
        for task in tasks[-10:]:  # Last 10 tasks
            output += f"- {task['task_id']}: {task['description']} ({task['status']})\n"

        return {"content": [{"type": "text", "text": output}]}


if __name__ == "__main__":
    # For testing purposes, we'll create a simple test harness
    server = SimpleMCPServer()

    # Test launch_task
    result = server.launch_task({"description": "Test task", "concepts": ["testing", "debugging"]})
    print("Launch result:", result)

    # Test view_dag
    result = server.view_dag({})
    print("\nDAG view:", result)
