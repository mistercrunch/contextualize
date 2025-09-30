# Task Framework POC Implementation

## The Architecture

We use Claude Code's custom command + agent system to create a deterministic task execution framework.

## 1. The Custom Command

```markdown
# .claude/commands/task.md
---
name: task
description: Execute a managed task with context isolation and logging
arguments: "<action> <task_description> --concepts <concept_list> --parent <parent_id>"
---

# Context-Managed Task Execution

You are executing a managed task within the Probabilistic Computing Framework.

**Arguments provided:** $ARGUMENTS

## Step 1: Parse Arguments

Parse the arguments to extract:
- Action: "run", "fork", or "resume"
- Task description
- Concepts to load (comma-separated)
- Parent task ID (if forking or chaining)

## Step 2: Initialize Task

Run this Python script to set up the task:

```python
import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime

# Parse arguments from "$ARGUMENTS"
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['run', 'fork', 'resume'])
parser.add_argument('description', nargs='+')
parser.add_argument('--concepts', default='')
parser.add_argument('--parent', default=None)

# Manual parsing since we get a string
args_str = "$ARGUMENTS"
# ... parse logic here ...

# Generate task ID
task_id = str(uuid.uuid4())
session_id = str(uuid.uuid4())

# Create task directory
task_dir = Path(f"logs/{task_id}")
task_dir.mkdir(parents=True, exist_ok=True)

# Write initial metadata
metadata = {
    "task_id": task_id,
    "session_id": session_id,
    "parent_id": args.parent,
    "description": " ".join(args.description),
    "concepts": args.concepts.split(',') if args.concepts else [],
    "started_at": datetime.now().isoformat(),
    "status": "running"
}

(task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

print(f"Task initialized: {task_id}")
print(f"Session ID: {session_id}")
print(f"Logging to: {task_dir}")
```

## Step 3: Load Context

Load only the specified concepts:

```python
# Load concept files
concepts_loaded = []
for concept_name in metadata['concepts']:
    concept_file = Path(f"context/concepts/{concept_name}.md")
    if concept_file.exists():
        content = concept_file.read_text()
        print(f"\n--- CONCEPT: {concept_name} ---")
        print(content)
        concepts_loaded.append(concept_name)
    else:
        print(f"Warning: Concept {concept_name} not found")

print(f"\nLoaded {len(concepts_loaded)} concepts: {', '.join(concepts_loaded)}")
```

## Step 4: Execute Task

Now execute the actual task with the loaded context:

**TASK DESCRIPTION:** [Extracted from arguments]

[The task will be executed here with only the loaded concepts as context]

## Step 5: Generate Report

When the task is complete, create a structured report:

```python
import json
from datetime import datetime
from pathlib import Path

# Update this based on what you accomplished
report = {
    "task_id": task_id,
    "status": "completed",  # or "failed"
    "completed_at": datetime.now().isoformat(),
    "summary": "[Describe what was accomplished]",
    "files_modified": [
        # List files you changed
    ],
    "issues_encountered": [
        # List any problems
    ],
    "next_steps": [
        # Suggest follow-up tasks
    ],
    "outputs": {
        # Any generated outputs
    }
}

# Save report
task_dir = Path(f"logs/{task_id}")
(task_dir / "report.json").write_text(json.dumps(report, indent=2))

# Update metadata
metadata = json.loads((task_dir / "metadata.json").read_text())
metadata["status"] = report["status"]
metadata["completed_at"] = report["completed_at"]
(task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

print(f"\nTask {task_id} completed!")
print(f"Report saved to: {task_dir}/report.json")
```

## Step 6: Create DAG Entry

Register this task in the DAG:

```python
# Update the global DAG
dag_file = Path("logs/dag.jsonl")
dag_entry = {
    "task_id": task_id,
    "parent_id": metadata.get("parent_id"),
    "timestamp": datetime.now().isoformat(),
    "description": metadata["description"],
    "status": report["status"]
}

with open(dag_file, "a") as f:
    f.write(json.dumps(dag_entry) + "\n")

print(f"DAG updated: {dag_file}")
```

Remember: You are operating within a managed task context. Keep operations focused and report results clearly.

```

## 2. The Custom Agent

```json
// .claude/agents/framework-operator.json
{
  "framework-operator": {
    "description": "Operates within the Probabilistic Computing Framework",
    "prompt": "You are a task operator within the Probabilistic Computing Framework. You execute tasks with precise context isolation, generate structured reports, and maintain the task DAG. Always:\n1. Load only required concepts\n2. Log operations to the task directory\n3. Generate structured reports\n4. Update the DAG\n5. Suggest follow-up tasks when appropriate",
    "tools": ["Read", "Write", "Edit", "Bash", "Grep"],
    "temperature": 0.5
  }
}
```

## 3. Helper Scripts

### visualize-dag.py

```python
#!/usr/bin/env python3
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

def generate_dag_html():
    """Generate an HTML visualization of the task DAG"""
    dag_file = Path("logs/dag.jsonl")

    if not dag_file.exists():
        return "<h1>No DAG data found</h1>"

    # Read all DAG entries
    tasks = []
    with open(dag_file) as f:
        for line in f:
            tasks.append(json.loads(line))

    # Generate Mermaid diagram
    mermaid = ["graph TD"]
    for task in tasks:
        task_id = task['task_id'][:8]  # Shorten for display
        desc = task['description'][:30]
        status = task['status']

        # Node style based on status
        style = "fill:#9f9" if status == "completed" else "fill:#f99"
        label = f"{task_id}<br/>{desc}"

        mermaid.append(f'    {task_id}["{label}"]')
        mermaid.append(f'    style {task_id} {style}')

        # Add edge from parent
        if task.get('parent_id'):
            parent_id = task['parent_id'][:8]
            mermaid.append(f'    {parent_id} --> {task_id}')

    mermaid_str = "\n".join(mermaid)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true }});</script>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #333; }}
            .mermaid {{ text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Task DAG Visualization</h1>
        <div class="mermaid">
        {mermaid_str}
        </div>
        <h2>Task List</h2>
        <ul>
        {"".join(f'<li><b>{t["task_id"][:8]}</b>: {t["description"]} ({t["status"]})</li>' for t in tasks)}
        </ul>
    </body>
    </html>
    """

    Path("logs/dag.html").write_text(html)
    return html

if __name__ == "__main__":
    generate_dag_html()
    print("DAG visualization generated: logs/dag.html")
    webbrowser.open("file://" + str(Path("logs/dag.html").absolute()))
```

### fork-task.py

```python
#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path

def fork_task(parent_task_id, new_description):
    """Fork from an existing task"""

    # Load parent metadata
    parent_dir = Path(f"logs/{parent_task_id}")
    if not parent_dir.exists():
        print(f"Parent task {parent_task_id} not found")
        return

    parent_metadata = json.loads((parent_dir / "metadata.json").read_text())

    # Get parent's session ID to potentially resume
    parent_session = parent_metadata.get("session_id")

    # Launch new task with parent's context
    concepts = ",".join(parent_metadata.get("concepts", []))

    print(f"Forking from {parent_task_id}")
    print(f"Inheriting concepts: {concepts}")

    # Launch Claude with the task command
    subprocess.run([
        "claude",
        f"/task fork '{new_description}' --concepts {concepts} --parent {parent_task_id}"
    ])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fork-task.py <parent_task_id> <new_description>")
        sys.exit(1)

    fork_task(sys.argv[1], sys.argv[2])
```

## 4. Usage Examples

```bash
# Run a new task with specific concepts
$ claude "/task run 'Debug authentication test' --concepts testing,auth"

# Fork from a failed task
$ python3 fork-task.py abc123def4 "Try mock-based approach"

# Visualize the DAG
$ python3 visualize-dag.py

# Resume a specific session (if still in memory)
$ claude --resume <session_id>
```

## 5. The Magic

This approach gives us:

1. **Controlled Execution**: Every task runs in isolation with specific context
2. **Full Logging**: Everything captured to `logs/{task_id}/`
3. **DAG Tracking**: Parent-child relationships preserved
4. **Fork Capability**: Retry failed tasks with different approaches
5. **Visualization**: See the exploration tree
6. **Reports**: Structured output from every task

The key insight: We're not trying to capture Claude's internal subtasks. Instead, we're making EVERY operation a tracked, logged, managed task that we control completely.
