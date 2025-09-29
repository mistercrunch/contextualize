#!/usr/bin/env python3
"""
Contextualize CLI - Clean, focused version with working commands only
"""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    name="ctx",
    help="Contextualize - Active Context Engineering for Claude Code",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


# ==================== CORE COMMANDS ====================


@app.command()
def init():
    """Initialize Contextualize in current directory"""
    console.print("[bold]Initializing Contextualize...[/bold]")

    # Create directory structure
    dirs = [
        Path("context/concepts"),
        Path("logs"),
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Created {dir_path}")

    # Create core concept if it doesn't exist
    core_file = Path("context/concepts/core.md")
    if not core_file.exists():
        core_file.write_text("""---
name: core
references: []
---

# Core Concepts

This is your project's core concept file.
Add key information that many tasks will need.

## Project Overview
[Add your project description]

## Key Architecture
[Add architecture notes]

## Common Patterns
[Add patterns used across the project]
""")
        console.print("✅ Created core concept")

    console.print("[bold green]Contextualize initialized![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Add your concepts to context/concepts/")
    console.print("2. Run `ctx launch --desc 'your task' --concepts 'core'`")


@app.command()
def launch(
    description: str = typer.Argument(..., help="Task description"),
    concepts: str = typer.Option("", "--concepts", "-c", help="Comma-separated concepts to load"),
    background: bool = typer.Option(False, "--bg", "-b", help="Run in background"),
    context: str = typer.Option("", "--context", help="Additional context"),
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
def tasks(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tasks to show"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
):
    """List recent tasks"""
    dag_file = Path("logs/dag.jsonl")

    if not dag_file.exists():
        console.print("[yellow]No tasks found. Run `ctx init` first.[/yellow]")
        return

    tasks_list = []
    with open(dag_file) as f:
        for line in f:
            tasks_list.append(json.loads(line))

    tasks_list = tasks_list[-limit:]

    if verbose:
        # Detailed view
        for task in tasks_list:
            status_color = {
                "completed": "green",
                "failed": "red",
                "running": "yellow",
                "created": "blue",
            }.get(task.get("status", "unknown"), "white")

            console.print(f"\n[bold]Task {task['task_id']}[/bold]")
            console.print(f"  Description: {task['description']}")
            console.print(
                f"  Status: [{status_color}]{task.get('status', 'unknown')}[/{status_color}]"
            )
            console.print(f"  Time: {task.get('timestamp', 'N/A')[:19]}")
            if task.get("parent_id"):
                console.print(f"  Parent: {task['parent_id']}")
    else:
        # Table view
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
                task["description"][:40] + ("..." if len(task["description"]) > 40 else ""),
                f"[{status_color}]{task.get('status', 'unknown')}[/{status_color}]",
                task.get("timestamp", "")[:16],
            )

        console.print(table)


@app.command()
def inspect(task_id: str):
    """Inspect a task's details"""
    task_dir = Path(f"logs/{task_id}")

    if not task_dir.exists():
        # Try partial match
        possible = list(Path("logs").glob(f"{task_id}*"))
        if possible:
            task_dir = possible[0]
            task_id = task_dir.name
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
        console.print(f"Started: {metadata.get('started_at', 'N/A')[:19]}")

        if metadata.get("concepts"):
            console.print(f"Concepts: {', '.join(metadata['concepts'])}")

        if metadata.get("session_id"):
            console.print(f"Session ID: {metadata['session_id']}")

    # Check for output
    output_file = task_dir / "output.txt"
    if output_file.exists():
        output = output_file.read_text()
        if output.strip():
            console.print(f"\n[bold]Output:[/bold]")
            console.print(output[:500] + ("..." if len(output) > 500 else ""))

    # Show commands
    console.print(f"\n[dim]Resume: ctx resume {task_id}[/dim]")
    console.print(f"[dim]Fork: ctx fork {task_id} 'new description'[/dim]")


@app.command()
def resume(task_id: str):
    """Resume a task session"""
    task_dir = Path(f"logs/{task_id}")

    if not task_dir.exists():
        # Try partial match
        possible = list(Path("logs").glob(f"{task_id}*"))
        if possible:
            task_dir = possible[0]
        else:
            console.print(f"[red]Task {task_id} not found[/red]")
            return

    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        console.print("[red]No metadata found[/red]")
        return

    metadata = json.loads(metadata_file.read_text())
    session_id = metadata.get("session_id")

    if not session_id:
        console.print("[red]No session ID found[/red]")
        return

    console.print(f"[green]Resuming session {session_id}...[/green]")
    subprocess.run(["claude", "--session-id", session_id])


@app.command()
def fork(
    parent_id: str,
    description: str = typer.Argument(..., help="Description for the fork"),
):
    """Fork from an existing task"""
    from .launcher import launch_task

    parent_dir = Path(f"logs/{parent_id}")

    if not parent_dir.exists():
        # Try partial match
        possible = list(Path("logs").glob(f"{parent_id}*"))
        if possible:
            parent_dir = possible[0]
            parent_id = parent_dir.name
        else:
            console.print(f"[red]Parent task {parent_id} not found[/red]")
            return

    # Load parent metadata
    metadata_file = parent_dir / "metadata.json"
    if not metadata_file.exists():
        console.print("[red]Parent task has no metadata[/red]")
        return

    parent_metadata = json.loads(metadata_file.read_text())

    # Load parent input if exists
    input_file = parent_dir / "input.json"
    parent_context = ""
    if input_file.exists():
        input_data = json.loads(input_file.read_text())
        parent_context = input_data.get("context_from_main", "")

    # Launch new task with parent's concepts
    task_id = launch_task(
        description=f"[Fork of {parent_id[:8]}] {description}",
        concepts=parent_metadata.get("concepts", []),
        context_from_main=f"Forked from: {parent_metadata.get('description', 'Unknown')}\n{parent_context}",
        parent_id=parent_id,
        background=False,
    )

    return task_id


# ==================== CONCEPT MANAGEMENT ====================


@app.command()
def concepts(
    show: Optional[str] = typer.Argument(None, help="Concept name to display"),
):
    """List or display concepts"""
    concepts_dir = Path("context/concepts")

    if not concepts_dir.exists():
        console.print("[red]No concepts directory. Run `ctx init` first.[/red]")
        return

    if show:
        # Display specific concept
        concept_file = concepts_dir / f"{show}.md"
        if not concept_file.exists():
            console.print(f"[red]Concept '{show}' not found[/red]")
            return

        content = concept_file.read_text()
        console.print(content)
    else:
        # List all concepts
        concepts_list = []
        for concept_file in sorted(concepts_dir.glob("*.md")):
            # Simple parse for references
            content = concept_file.read_text()
            lines = content.split("\n")
            refs = []
            if len(lines) > 2 and "references:" in lines[2]:
                refs_str = lines[2].replace("references:", "").strip()
                if refs_str and refs_str != "[]":
                    refs = [r.strip() for r in refs_str.strip("[]").split(",")]

            concepts_list.append(
                {"name": concept_file.stem, "size": len(content), "refs": len(refs)}
            )

        if not concepts_list:
            console.print(
                "[yellow]No concepts found. Create .md files in context/concepts/[/yellow]"
            )
            return

        table = Table(title="Available Concepts")
        table.add_column("Concept", style="cyan")
        table.add_column("Size", style="dim")
        table.add_column("Refs", style="dim")

        for concept in concepts_list:
            table.add_row(concept["name"], f"{concept['size']:,} chars", str(concept["refs"]))

        console.print(table)


# ==================== MONITORING ====================


@app.command()
def status():
    """Check status of recent tasks"""
    from .monitor import monitor_all_tasks

    tasks = monitor_all_tasks()

    if not tasks:
        console.print("[yellow]No tasks found[/yellow]")
        return

    table = Table(title="Task Status")
    table.add_column("Status", style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("State", style="dim")
    table.add_column("Output", style="dim")

    for task in tasks:
        icon = "🔄" if task["running"] else ("✅" if task["has_output"] else "❓")
        state = "Running" if task["running"] else "Complete"
        output = "Yes" if task["has_output"] else "No"

        table.add_row(icon, task["task_id"][:8], state, output)

    console.print(table)


# ==================== HELP & INFO ====================


@app.command()
def version():
    """Show version and info"""
    from . import __version__

    console.print(f"[bold]Contextualize v{__version__}[/bold]")
    console.print("Active Context Engineering for Claude Code")
    console.print("\n[dim]Docs: https://github.com/yourusername/contextualize[/dim]")


if __name__ == "__main__":
    app()
