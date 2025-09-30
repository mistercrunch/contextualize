#!/usr/bin/env python3
"""
Contextualize CLI - Active Context Engineering for AI Coding Agents
"""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    name="ctx",
    help="Contextualize - Active Context Engineering for AI Coding Agents",
    add_completion=False,
)
console = Console()


@app.command()
def start(
    mcp_config: Path | None = typer.Option(
        Path("task-framework-mcp.json"),
        "--config",
        "-c",
        help="Path to MCP configuration",
    ),
):
    """Start Claude with Contextualize Framework"""
    console.print("[bold green]Starting Claude with Contextualize...[/bold green]")
    console.print("[yellow]Remember to use launch_task for all substantial work![/yellow]")

    if not mcp_config.exists():
        console.print(f"[red]Config file not found: {mcp_config}[/red]")
        raise typer.Exit(1)

    subprocess.run(["claude", "--mcp-config", str(mcp_config)])


@app.command()
def install():
    """Install Contextualize integration with Claude Code"""
    console.print("[bold]Installing Contextualize integration...[/bold]\n")

    # Ask where to install
    location = typer.prompt(
        "Install location", type=typer.Choice(["global", "project"]), default="project"
    )

    if location == "global":
        claude_dir = Path.home() / ".claude"
    else:
        claude_dir = Path.cwd() / ".claude"

    # Create directories
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    # Create custom command for launching tasks
    launch_task_cmd = commands_dir / "ctx-launch.md"
    launch_task_cmd.write_text("""---
name: ctx-launch
description: Launch a Contextualize task with focused context
---

# Launch Contextualize Task

To launch a task with targeted context:

```bash
ctx launch-async --desc "Your task description" --concepts "concept1,concept2"
```

This will:
1. Create an isolated Claude session
2. Load only the specified concepts
3. Track the task in the DAG
4. Allow resume/fork later
""")

    console.print("✅ Installed command: ctx-launch")

    # Create MCP config if needed
    mcp_config = claude_dir / "mcp-servers.json"
    if mcp_config.exists():
        console.print("[yellow]MCP config already exists, skipping[/yellow]")
    else:
        mcp_data = {
            "mcpServers": {
                "contextualize": {
                    "command": "python",
                    "args": ["-m", "contextualize.mcp_server"],
                    "cwd": str(Path.cwd()),
                    "env": {"PYTHONPATH": str(Path.cwd())},
                }
            }
        }
        mcp_config.write_text(json.dumps(mcp_data, indent=2))
        console.print(f"✅ Created MCP config: {mcp_config}")

    console.print(f"\n[green]Contextualize installed in {claude_dir}[/green]")
    console.print("\nNext steps:")
    console.print("1. Run `ctx init` to set up your project")
    console.print("2. Restart Claude Code to load the integration")


@app.command()
def init():
    """Initialize Contextualize in current directory"""
    console.print("[bold]Initializing Contextualize...[/bold]")

    # Create directory structure
    dirs = [
        Path("context/concepts"),
        Path("logs"),
        Path(".claude/commands"),
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Created {dir_path}")

    # Create initial concepts
    initial_concepts = {
        "framework": """---
name: framework
references: []
---

# Framework Concepts

## Purpose
This is Contextualize, the active context engineering framework that enables:
- Task isolation with minimal context
- Full observability and logging
- Fork and resume capabilities
- DAG visualization

## Key Commands
- launch_task: Create new managed task
- fork_task: Branch from existing task
- view_dag: Show task relationships
""",
        "setup": """---
name: setup
references: []
---

# Setup Concepts

## Prerequisites
- Python 3.10+
- Claude Code CLI
- uv package manager

## Installation
1. Install dependencies: `uv pip install -e .`
2. Install pre-commit: `pre-commit install`
3. Initialize Contextualize: `ctx init`
""",
    }

    for name, content in initial_concepts.items():
        concept_file = Path(f"context/concepts/{name}.md")
        concept_file.write_text(content)
        console.print(f"✅ Created concept: {name}")

    console.print("[bold green]Contextualize initialized successfully![/bold green]")


@app.command()
def tasks(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tasks to show"),
    all_tasks: bool = typer.Option(False, "--all", "-a", help="Show all tasks"),
):
    """List recent tasks with status"""
    dag_file = Path("logs/dag.jsonl")

    if not dag_file.exists():
        console.print("[yellow]No tasks found yet[/yellow]")
        return

    tasks_list = []
    with open(dag_file) as f:
        for line in f:
            tasks_list.append(json.loads(line))

    if not all_tasks:
        tasks_list = tasks_list[-limit:]

    table = Table(title=f"Recent Tasks ({len(tasks_list)} shown)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Time", style="dim")

    for task in tasks_list:
        status_color = {
            "completed": "green",
            "failed": "red",
            "running": "yellow",
            "created": "blue",
        }.get(task.get("status", "unknown"), "white")

        table.add_row(
            task["task_id"][:8],
            task["description"][:50],
            f"[{status_color}]{task.get('status', 'unknown')}[/{status_color}]",
            task.get("timestamp", "")[:19],
        )

    console.print(table)


@app.command()
def inspect(task_id: str):
    """Inspect a specific task's details"""
    task_dir = Path(f"logs/{task_id}")

    if not task_dir.exists():
        # Try with partial ID
        possible_dirs = list(Path("logs").glob(f"{task_id}*"))
        if possible_dirs:
            task_dir = possible_dirs[0]
        else:
            console.print(f"[red]Task {task_id} not found[/red]")
            return

    # Load metadata
    metadata_file = task_dir / "metadata.json"
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())

        console.print(f"[bold]Task: {metadata.get('task_id', 'unknown')}[/bold]")
        console.print(f"Description: {metadata.get('description', 'N/A')}")
        console.print(f"Status: {metadata.get('status', 'unknown')}")
        console.print(f"Started: {metadata.get('started_at', 'N/A')}")

        if metadata.get("concepts"):
            console.print(f"Concepts: {', '.join(metadata['concepts'])}")

    # Show input if exists
    input_file = task_dir / "input.json"
    if input_file.exists():
        input_data = json.loads(input_file.read_text())
        if input_data.get("context_from_main"):
            console.print("\n[bold]Context from Main:[/bold]")
            console.print(input_data["context_from_main"][:500])

    # Show report if exists
    report_file = task_dir / "report.json"
    if report_file.exists():
        report = json.loads(report_file.read_text())
        console.print("\n[bold]Report:[/bold]")
        console.print(f"Summary: {report.get('summary', 'N/A')}")


@app.command()
def dag():
    """Visualize task DAG as a tree"""
    dag_file = Path("logs/dag.jsonl")

    if not dag_file.exists():
        console.print("[yellow]No tasks in DAG yet[/yellow]")
        return

    tasks = []
    with open(dag_file) as f:
        for line in f:
            tasks.append(json.loads(line))

    # Build tree structure
    tree = Tree("Task DAG")
    task_nodes = {}

    for task in tasks:
        task_id = task["task_id"][:8]
        status_icon = {
            "completed": "✅",
            "failed": "❌",
            "running": "🔄",
            "created": "📝",
        }.get(task.get("status", "unknown"), "❓")

        label = f"{status_icon} {task_id}: {task['description'][:40]}"

        if task.get("parent_id"):
            parent_id = task["parent_id"][:8]
            if parent_id in task_nodes:
                node = task_nodes[parent_id].add(label)
            else:
                node = tree.add(label)
        else:
            node = tree.add(label)

        task_nodes[task_id] = node

    console.print(tree)


@app.command()
def concepts(show: str | None = typer.Argument(None, help="Concept name to display")):
    """List or display concepts"""
    concepts_dir = Path("context/concepts")

    if not concepts_dir.exists():
        console.print("[red]No concepts directory found[/red]")
        return

    if show:
        # Display specific concept
        concept_file = concepts_dir / f"{show}.md"
        if not concept_file.exists():
            console.print(f"[red]Concept '{show}' not found[/red]")
            return

        content = concept_file.read_text()
        console.print(f"[bold]Concept: {show}[/bold]\n")
        console.print(content)
    else:
        # List all concepts
        concepts_list = []
        for concept_file in concepts_dir.glob("*.md"):
            # Parse frontmatter to get references
            content = concept_file.read_text()
            lines = content.split("\n")
            refs = []
            if len(lines) > 2 and lines[2].startswith("references:"):
                refs_str = lines[2].replace("references:", "").strip()
                if refs_str and refs_str != "[]":
                    refs = [r.strip() for r in refs_str.strip("[]").split(",")]

            concepts_list.append({"name": concept_file.stem, "references": refs})

        table = Table(title="Available Concepts")
        table.add_column("Concept", style="cyan")
        table.add_column("References", style="dim")

        for concept in sorted(concepts_list, key=lambda x: x["name"]):
            refs_str = ", ".join(concept["references"]) if concept["references"] else "-"
            table.add_row(concept["name"], refs_str)

        console.print(table)


@app.command()
def fork(
    parent_id: str,
    description: str = typer.Option(..., "--desc", "-d", help="Description for the fork"),
):
    """Fork a new task from an existing one"""
    parent_dir = Path(f"logs/{parent_id}")

    if not parent_dir.exists():
        # Try with partial ID
        possible_dirs = list(Path("logs").glob(f"{parent_id}*"))
        if possible_dirs:
            parent_dir = possible_dirs[0]
            parent_id = parent_dir.name
        else:
            console.print(f"[red]Parent task {parent_id} not found[/red]")
            return

    # Load parent metadata and input
    metadata_file = parent_dir / "metadata.json"
    input_file = parent_dir / "input.json"

    if not metadata_file.exists():
        console.print("[red]No metadata found for parent task[/red]")
        return

    parent_metadata = json.loads(metadata_file.read_text())
    parent_input = {}
    if input_file.exists():
        parent_input = json.loads(input_file.read_text())

    # Create new task ID
    task_id = str(uuid.uuid4())[:8]
    task_dir = Path(f"logs/{task_id}")
    task_dir.mkdir(parents=True, exist_ok=True)

    # Generate session ID for resumability (must be valid UUID)
    session_id = str(uuid.uuid4())

    # Create fork metadata
    metadata = {
        "task_id": task_id,
        "description": description,
        "parent_id": parent_id,
        "concepts": parent_metadata.get("concepts", []),
        "started_at": datetime.now().isoformat(),
        "session_id": session_id,
        "status": "created",
    }

    (task_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # Copy parent input
    input_data = {
        "concepts": parent_metadata.get("concepts", []),
        "context_from_main": parent_input.get("context_from_main", ""),
        "parent_id": parent_id,
        "fork_reason": description,
    }
    (task_dir / "input.json").write_text(json.dumps(input_data, indent=2))

    # Log to DAG
    dag_file = Path("logs/dag.jsonl")
    with open(dag_file, "a") as f:
        f.write(
            json.dumps(
                {
                    "task_id": task_id,
                    "timestamp": metadata["started_at"],
                    "description": description,
                    "parent_id": parent_id,
                    "status": "created",
                }
            )
            + "\n"
        )

    console.print(f"[green]✅ Forked task {task_id} from {parent_id}[/green]")
    console.print(f"Description: {description}")
    console.print(f"Session ID: {session_id}")
    console.print(f"Concepts: {', '.join(metadata['concepts'])}")

    # Launch Claude with fork context
    prompt = f"""You are resuming work from a forked task.

PARENT TASK: {parent_metadata.get('description', 'Unknown')}
FORK REASON: {description}

CONCEPTS LOADED:
{', '.join(metadata['concepts'])}

CONTEXT FROM PARENT:
{parent_input.get('context_from_main', '')}

Continue the work, addressing the fork reason."""

    console.print("\n[yellow]Launching Claude with fork context...[/yellow]")
    subprocess.run(["claude", "--session-id", session_id, prompt])


@app.command()
def resume(task_id: str):
    """Resume a task session (if still in memory)"""
    task_dir = Path(f"logs/{task_id}")

    if not task_dir.exists():
        # Try with partial ID
        possible_dirs = list(Path("logs").glob(f"{task_id}*"))
        if possible_dirs:
            task_dir = possible_dirs[0]
        else:
            console.print(f"[red]Task {task_id} not found[/red]")
            return

    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        console.print("[red]No metadata found for task[/red]")
        return

    metadata = json.loads(metadata_file.read_text())
    session_id = metadata.get("session_id")

    if not session_id:
        console.print("[red]No session ID found for task[/red]")
        return

    console.print(f"[green]Attempting to resume session {session_id}...[/green]")
    subprocess.run(["claude", "--resume", session_id])


@app.command()
def launch(
    description: str = typer.Option(..., "--desc", "-d", help="Task description"),
    concepts: str = typer.Option("", "--concepts", "-c", help="Comma-separated concepts"),
    context: str = typer.Option("", "--context", help="Additional context"),
    background: bool = typer.Option(False, "--bg", help="Run in background"),
):
    """Launch a task with focused context"""
    from .launcher import launch_task

    concepts_list = [c.strip() for c in concepts.split(",") if c.strip()]

    task_id = launch_task(
        description=description,
        concepts=concepts_list,
        context_from_main=context,
        background=background,
    )

    return task_id


@app.command()
def launch_async(
    description: str = typer.Option(..., "--desc", "-d", help="Task description"),
    concepts: str = typer.Option("", "--concepts", "-c", help="Comma-separated concepts"),
    context: str = typer.Option("", "--context", help="Additional context"),
):
    """Launch a task in background (alias for launch --bg)"""
    from .launcher import launch_task

    concepts_list = [c.strip() for c in concepts.split(",") if c.strip()]

    task_id = launch_task(
        description=description, concepts=concepts_list, context_from_main=context, background=True
    )

    return task_id


@app.command()
def dogfood():
    """Start dogfooding - use the framework to build itself!"""
    console.print("[bold cyan]🐕 Starting Dogfood Mode![/bold cyan]")
    console.print("\nThis will launch Claude with instructions to:")
    console.print("1. Use the framework to manage its own development")
    console.print("2. Create tasks for each feature to implement")
    console.print("3. Build the remaining framework components\n")

    # Load available concepts
    concepts_dir = Path("context/concepts")
    available_concepts = []
    if concepts_dir.exists():
        for concept_file in concepts_dir.glob("*.md"):
            available_concepts.append(concept_file.stem)

    concepts_list = "\n".join(f"- {c}" for c in sorted(available_concepts))

    prompt = f"""You are now in DOGFOOD MODE for Contextualize.

Your mission: Use Contextualize to build itself!

Available concepts:
{concepts_list}

For every feature you implement, create a managed task:
1. Use launch_task() for new features
2. Use fork_task() if something fails
3. Keep tasks focused with minimal concepts

Start by reviewing what's been built and create tasks for:
- Completing the MCP server implementation
- Adding async task support
- Creating the DAG visualizer
- Adding more concepts

Remember: EVERY piece of work should be a tracked task!"""

    console.print("[yellow]Launching Claude with dogfood instructions...[/yellow]")
    subprocess.run(["claude", prompt])


if __name__ == "__main__":
    app()
