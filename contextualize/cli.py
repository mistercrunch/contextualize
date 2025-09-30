#!/usr/bin/env python3
"""
Contextualize CLI v2 - Using subcommand pattern
"""

import subprocess
from pathlib import Path

try:
    from importlib import resources
except ImportError:
    # Python < 3.9
    import importlib_resources as resources

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="ctx",
    help="Contextualize - Active Context Engineering for Claude Code",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# ==================== TASK SUBCOMMANDS ====================

task_app = typer.Typer(
    help="Manage tasks",
    invoke_without_command=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(task_app, name="task", rich_help_panel="Core Commands")


@task_app.command("start")
def task_start(
    description: str = typer.Argument(..., help="Task description"),
    concepts: str = typer.Option("", "--concepts", "-c", help="Comma-separated concepts"),
    background: bool = typer.Option(False, "--bg", "-b", help="Run in background"),
    context: str = typer.Option("", "--context", help="Additional context"),
    report: bool = typer.Option(False, "--report", "-r", help="Generate report after completion"),
    report_template: str = typer.Option(None, "--report-template", help="Report template to use"),
):
    """Start a new task with focused context"""
    from .launcher import launch_task

    concepts_list = [c.strip() for c in concepts.split(",") if c.strip()]

    task_id = launch_task(
        description=description,
        concepts=concepts_list,
        context_from_main=context,
        background=background,
        generate_report=report,
        report_template=report_template,
    )

    return task_id


@task_app.command("list")
def task_list(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tasks to show"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all tasks"),
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    monitor: bool = typer.Option(False, "--monitor", "-m", help="Show monitoring view"),
):
    """List tasks with optional monitoring"""
    from .models import TaskCollection, TaskStatus

    collection = TaskCollection()

    # If monitor mode, show monitoring view
    if monitor:
        from .monitor import monitor_all_tasks

        tasks = monitor_all_tasks()

        if not tasks:
            console.print("[yellow]No tasks found[/yellow]")
            return

        table = Table(title="Task Monitor")
        table.add_column("", style="bold")  # Icon
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="dim")
        table.add_column("Output", style="dim")

        for task in tasks:
            icon = "🔄" if task["running"] else ("✅" if task["has_output"] else "❓")
            status = task["status"]
            output = "Yes" if task["has_output"] else "No"
            desc = task.get("description", "")[:30] + (
                "..." if len(task.get("description", "")) > 30 else ""
            )

            table.add_row(icon, task["task_id"][:8], desc, status, output)

        console.print(table)
        return

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status.lower())
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            return

    # Get tasks
    tasks = collection.list(limit=None if all else limit, status=status_filter)

    if not tasks:
        console.print("[yellow]No tasks found. Run `ctx init` first.[/yellow]")
        return

    table = Table(title=f"Tasks ({len(tasks)} shown)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Parent", style="dim")
    table.add_column("Time", style="dim")

    for task in tasks:
        status_color = {
            TaskStatus.COMPLETED: "green",
            TaskStatus.FAILED: "red",
            TaskStatus.RUNNING: "yellow",
            TaskStatus.CREATED: "blue",
        }.get(task.status, "white")

        parent_str = task.parent_id[:8] if task.parent_id else "-"
        time_str = task.started_at.strftime("%Y-%m-%dT%H:%M") if task.started_at else "-"

        table.add_row(
            task.task_id[:8],
            task.description[:35] + ("..." if len(task.description) > 35 else ""),
            f"[{status_color}]{task.status.value}[/{status_color}]",
            parent_str,
            time_str,
        )

    console.print(table)


@task_app.command("show")
def task_show(
    task_id: str = typer.Argument(..., help="Task ID (can be partial)"),
    output: bool = typer.Option(False, "--output", "-o", help="Show full output"),
):
    """Show task details"""
    from .models import TaskCollection

    collection = TaskCollection()
    task = collection.get(task_id, partial=True)

    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    # Display task info
    console.print(f"\n[bold]Task {task.task_id}[/bold]")
    console.print(f"├─ Description: {task.description}")
    console.print(f"├─ Status: {task.status.value}")

    if task.started_at:
        console.print(f"├─ Started: {task.started_at.isoformat()[:19]}")
    if task.completed_at:
        console.print(f"├─ Completed: {task.completed_at.isoformat()[:19]}")

    if task.concepts:
        console.print(f"├─ Concepts: {', '.join(task.concepts)}")

    if task.session_id:
        console.print(f"├─ Session: {task.session_id}")

    if task.parent_id:
        console.print(f"└─ Parent: {task.parent_id[:8]}")

    # Show output
    task_output = task.get_output()
    if task_output and task_output.strip():
        if output or len(task_output) < 1000:
            console.print("\n[bold]Output:[/bold]")
            console.print(task_output)
        else:
            console.print(f"\n[bold]Output:[/bold] ({len(task_output)} chars)")
            console.print(task_output[:500] + "...")
            console.print("\n[dim]Use --output to see full output[/dim]")

    # Show error if exists
    error = task.get_error()
    if error and error.strip():
        console.print("\n[bold red]Error:[/bold red]")
        console.print(error[:500] + ("..." if len(error) > 500 else ""))

    # Show available actions
    console.print("\n[dim]Actions:[/dim]")
    console.print(f"  ctx task resume {task.task_id[:8]}")
    console.print(f"  ctx task fork {task.task_id[:8]} 'new description'")
    console.print(f"  ctx task rm {task.task_id[:8]}")


@task_app.command("resume")
def task_resume(
    task_id: str = typer.Argument(..., help="Task ID to resume"),
):
    """Resume a task session"""
    from .models import TaskCollection

    collection = TaskCollection()
    task = collection.get(task_id, partial=True)

    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    if not task.session_id:
        console.print("[red]No session ID found[/red]")
        return

    console.print(f"[green]Resuming task {task.task_id[:8]}: {task.description}[/green]")
    console.print(f"[dim]Session: {task.session_id}[/dim]")
    subprocess.run(["claude", "--session-id", task.session_id])


@task_app.command("fork")
def task_fork(
    parent_id: str = typer.Argument(..., help="Parent task ID"),
    description: str = typer.Argument(..., help="Description for the fork"),
):
    """Fork a new task from existing one"""
    from .launcher import launch_task
    from .models import TaskCollection

    collection = TaskCollection()
    parent_task = collection.get(parent_id, partial=True)

    if not parent_task:
        console.print(f"[red]Parent task {parent_id} not found[/red]")
        return

    # Get parent context
    parent_input = parent_task.get_input()
    parent_context = parent_input.get("context_from_main", "") if parent_input else ""

    # Launch new task with parent's concepts
    task_id = launch_task(
        description=f"[Fork of {parent_task.task_id[:8]}] {description}",
        concepts=parent_task.concepts,
        context_from_main=f"Forked from: {parent_task.description}\n{parent_context}",
        parent_id=parent_task.task_id,
        background=False,
    )

    return task_id


@task_app.command("rm")
def task_remove(
    task_id: str = typer.Argument(..., help="Task ID to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
):
    """Remove a task and its logs"""
    from .models import TaskCollection

    collection = TaskCollection()
    task = collection.get(task_id, partial=True)

    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    if not force:
        confirm = typer.confirm(f"Remove task {task.task_id[:8]}: {task.description}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    if collection.remove(task.task_id):
        console.print(f"[green]Removed task {task.task_id}[/green]")
    else:
        console.print("[red]Failed to remove task[/red]")


@task_app.command("report")
def task_report(
    task_id: str = typer.Argument(..., help="Task ID to generate report for"),
    template: str = typer.Option(None, "--template", "-t", help="Report template to use"),
    regenerate: bool = typer.Option(False, "--regenerate", help="Regenerate existing report"),
    show: bool = typer.Option(False, "--show", "-s", help="Display report after generation"),
):
    """Generate or view a task report"""
    from .models import TaskCollection
    from .report_generator import ReportGenerator

    # Get task
    collection = TaskCollection()
    task = collection.get(task_id, partial=True)

    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    # Check if just showing existing report
    report_path = task.task_dir / "report.md"  # TODO: Handle other extensions
    if report_path.exists() and show and not regenerate:
        console.print(report_path.read_text())
        return

    # Generate report
    generator = ReportGenerator()
    console.print(f"[yellow]Generating report for task {task.task_id}...[/yellow]")

    if generator.generate_report(task.task_id, template_override=template, regenerate=regenerate):
        console.print(f"[green]✅ Report generated: {report_path}[/green]")

        if show:
            console.print("\n" + "=" * 60 + "\n")
            console.print(report_path.read_text())
    else:
        console.print("[red]Failed to generate report[/red]")


@task_app.command("clear")
def task_clear(
    force: bool = typer.Option(False, "--force", "-f", help="Force clear without confirmation"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Clear all tasks and logs"""
    from .models import TaskCollection

    collection = TaskCollection()
    stats = collection.stats()

    if stats["total"] == 0:
        console.print("[yellow]No tasks to clear[/yellow]")
        return

    # Show what will be cleared
    console.print("[bold]Tasks to clear:[/bold]")
    console.print(f"  Total: {stats['total']}")
    console.print(f"  Running: {stats['running']}")
    console.print(f"  Completed: {stats['completed']}")
    console.print(f"  Failed: {stats['failed']}")

    # Confirm unless forced or yes flag
    if not force and not yes:
        confirm = typer.confirm(f"Clear {stats['total']} tasks?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Clear
    try:
        count = collection.clear(force=True)
        console.print(f"[green]✅ Cleared {count} tasks[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ==================== CONCEPT SUBCOMMANDS ====================

concept_app = typer.Typer(
    help="Manage concepts",
    invoke_without_command=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(concept_app, name="concept", rich_help_panel="Core Commands")


@concept_app.command("list")
def concept_list():
    """List all concepts"""
    from .concept_models import ConceptCollection

    collection = ConceptCollection()
    concepts = collection.list()

    if not concepts:
        console.print("[yellow]No concepts found. Run `ctx init` first.[/yellow]")
        return

    table = Table(title="Available Concepts")
    table.add_column("Concept", style="cyan")
    table.add_column("Size", style="dim")
    table.add_column("References", style="dim")

    for concept in concepts:
        refs_str = ", ".join(concept.references) if concept.references else "-"
        table.add_row(concept.name, f"{concept.get_size():,} chars", refs_str)

    console.print(table)


@concept_app.command("show")
def concept_show(
    name: str = typer.Argument(..., help="Concept name"),
    deps: bool = typer.Option(False, "--deps", "-d", help="Show with dependencies"),
):
    """Show concept content"""
    from .concept_models import ConceptCollection

    collection = ConceptCollection()
    concept = collection.get(name)

    if not concept:
        console.print(f"[red]Concept '{name}' not found[/red]")
        return

    if deps:
        # Load with dependencies
        content = collection.load_with_dependencies([name])
        console.print(content)
    else:
        # Show just this concept
        console.print(f"[bold]Concept: {concept.name}[/bold]")
        if concept.references:
            console.print(f"[dim]References: {', '.join(concept.references)}[/dim]")
        console.print()
        console.print(concept.content)


@concept_app.command("new")
def concept_new(
    name: str = typer.Argument(..., help="Concept name"),
    references: str = typer.Option("", "--refs", "-r", help="Comma-separated references"),
):
    """Create a new concept"""
    from .concept_models import ConceptCollection

    collection = ConceptCollection()

    # Check if already exists
    if collection.get(name):
        console.print(f"[yellow]Concept '{name}' already exists[/yellow]")
        return

    refs_list = [r.strip() for r in references.split(",") if r.strip()]

    # Create concept
    concept = collection.create(name, refs_list)
    console.print(f"[green]Created concept: {name}[/green]")
    console.print(f"Edit: {concept.file_path}")


@concept_app.command("validate")
def concept_validate():
    """Validate all concept references"""
    from .concept_models import ConceptCollection

    collection = ConceptCollection()
    issues = collection.validate_all_references()

    if not issues:
        console.print("[green]✅ All concept references are valid[/green]")
        return

    console.print("[yellow]⚠️  Found reference issues:[/yellow]")
    for concept_name, missing_refs in issues.items():
        console.print(f"\n[bold]{concept_name}[/bold] references missing concepts:")
        for ref in missing_refs:
            console.print(f"  ❌ {ref}")

    console.print("\n[dim]Fix by creating missing concepts or updating references[/dim]")


@concept_app.command("rm")
def concept_remove(
    name: str = typer.Argument(..., help="Concept name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal"),
):
    """Remove a concept"""
    from .concept_models import ConceptCollection

    collection = ConceptCollection()
    concept = collection.get(name)

    if not concept:
        console.print(f"[red]Concept '{name}' not found[/red]")
        return

    # Check for references
    referenced_by = collection.get_referenced_by(name)
    if referenced_by and not force:
        console.print(f"[yellow]Warning: Concept '{name}' is referenced by:[/yellow]")
        for ref in referenced_by:
            console.print(f"  - {ref}")
        confirm = typer.confirm("Remove anyway?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return
    elif not force:
        confirm = typer.confirm(f"Remove concept '{name}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    if collection.remove(name):
        console.print(f"[green]Removed concept: {name}[/green]")
    else:
        console.print("[red]Failed to remove concept[/red]")


# ==================== TOP-LEVEL COMMANDS ====================


@app.command(rich_help_panel="Setup Commands")
def init():
    """Initialize Contextualize in current directory"""
    console.print("[bold]Initializing Contextualize...[/bold]")

    # Create directory structure
    # User-land directories under context/
    dirs = [
        Path("context/concepts"),  # Knowledge modules
        Path("context/reports"),  # Report templates
        Path("logs"),  # Task execution logs (separate from context)
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Created {dir_path}")

    # Copy default templates from package resources
    try:
        # Copy report templates
        report_templates = resources.files("contextualize.resources.templates.reports")
        for template in report_templates.iterdir():
            if template.name.endswith(".md"):
                target = Path(f"context/reports/{template.name}")
                if not target.exists():
                    target.write_text(template.read_text())
                    console.print(f"✅ Created report template: {template.name}")

        # Copy concept templates
        concept_templates = resources.files("contextualize.resources.templates.concepts")
        for template in concept_templates.iterdir():
            if template.name.endswith(".md"):
                target = Path(f"context/concepts/{template.name}")
                if not target.exists():
                    target.write_text(template.read_text())
                    console.print(f"✅ Created concept: {template.name}")

    except Exception as e:
        # Fallback for development or if resources not found
        console.print(f"[yellow]Note: Using fallback templates (resources not found: {e})[/yellow]")

        # Create minimal default report template
        default_report = Path("context/reports/default.md")
        if not default_report.exists():
            default_report.write_text("""# Task Report: {{task_id}}

## Summary
{{summary}}

## Context
- **Task ID**: {{task_id}}
- **Description**: {{description}}
- **Started**: {{started_at}}
- **Completed**: {{completed_at}}
- **Duration**: {{duration}}
- **Status**: {{status}}
- **Concepts Used**: {{concepts}}

## Execution

### What was attempted
{{actions_taken}}

### What was achieved
{{outcomes}}

### Issues encountered
{{issues_and_resolutions}}

## Artifacts
{{artifacts_created}}

## Recommendations
{{next_steps}}""")
            console.print("✅ Created default report template")

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

    # Create .gitignore for logs and .claude if it doesn't exist
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        lines_to_add = []

        if "logs/" not in content:
            lines_to_add.append("logs/")
        if ".claude/" not in content:
            lines_to_add.append(".claude/")

        if lines_to_add:
            gitignore.write_text(content + "\n# Contextualize\n" + "\n".join(lines_to_add) + "\n")
            console.print(f"✅ Added {', '.join(lines_to_add)} to .gitignore")
    else:
        gitignore.write_text("# Contextualize\nlogs/\n\n# Claude Code\n.claude/\n")
        console.print("✅ Created .gitignore")

    console.print("[bold green]Contextualize initialized![/bold green]")
    console.print("\nDirectory structure:")
    console.print("  context/          # Your project context (add to git)")
    console.print("    concepts/       # Knowledge modules")
    console.print("    reports/        # Report templates")
    console.print("  logs/            # Task execution logs (gitignored)")
    console.print("\nNext steps:")
    console.print("1. Add concepts: `ctx concept new <name>`")
    console.print("2. Start a task: `ctx task start 'description' -c core`")
    console.print("3. Generate reports: `ctx task start 'description' --report`")


@app.command(rich_help_panel="Info Commands")
def status():
    """Show overall status"""
    # Count tasks
    dag_file = Path("logs/dag.jsonl")
    task_count = 0
    if dag_file.exists():
        with open(dag_file) as f:
            task_count = sum(1 for _ in f)

    # Count concepts
    concepts_dir = Path("context/concepts")
    concept_count = len(list(concepts_dir.glob("*.md"))) if concepts_dir.exists() else 0

    # Show summary
    console.print("[bold]Contextualize Status[/bold]")
    console.print(f"├─ Tasks: {task_count}")
    console.print(f"├─ Concepts: {concept_count}")
    console.print(f"└─ Working dir: {Path.cwd()}")

    if task_count == 0 and concept_count == 0:
        console.print("\n[yellow]No tasks or concepts yet. Run `ctx init` to get started.[/yellow]")


@app.command(rich_help_panel="Info Commands")
def version():
    """Show version info"""
    from . import __version__

    console.print(f"[bold]Contextualize v{__version__}[/bold]")
    console.print("Active Context Engineering for Claude Code")
    console.print("\n[dim]https://github.com/yourusername/contextualize[/dim]")


if __name__ == "__main__":
    app()
