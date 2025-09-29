#!/usr/bin/env python3
"""
Report generation for Contextualize tasks
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from importlib import resources
except ImportError:
    # Python < 3.9
    import importlib_resources as resources

from .models import Task, TaskCollection, TaskStatus
from .claude_cli import ClaudeCLI


class ReportGenerator:
    """Generate reports for completed tasks"""

    def __init__(self, reports_dir: Path = Path("context/reports")):
        self.reports_dir = reports_dir

    def generate_report(
        self, task_id: str, template_override: Optional[str] = None, regenerate: bool = False
    ) -> bool:
        """Generate a report for a completed task

        Args:
            task_id: Task to generate report for
            template_override: Override the default template
            regenerate: Force regeneration even if report exists

        Returns:
            True if report was generated successfully
        """
        # Load task
        collection = TaskCollection()
        task = collection.get(task_id, partial=True)

        if not task:
            print(f"Task {task_id} not found")
            return False

        # Check if report already exists
        report_path = self._get_report_path(task)
        if report_path.exists() and not regenerate:
            print(f"Report already exists at {report_path}")
            return True

        # Check task status
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.REPORTED, TaskStatus.REPORTING]:
            print(f"Task is {task.status.value}, reports are only generated for completed tasks")
            return False

        # Update task status
        task.report_status = "generating"
        task.status = TaskStatus.REPORTING
        task.save()

        try:
            # Determine template
            template_path = (
                template_override or task.report_template or "context/reports/default.md"
            )
            template = self.load_template(template_path)

            # Build report prompt
            prompt = self.build_report_prompt(task, template)

            # Generate report using forked session
            print(f"Generating report for task {task_id}...")
            report_session_id, report_content = ClaudeCLI.fork_session(
                original_session_id=task.session_id,
                prompt=prompt,
                output_format="json" if template_path.endswith(".json") else "text",
            )

            # Parse output if JSON
            if template_path.endswith(".json"):
                report_data = ClaudeCLI.parse_json_output(report_content)
                report_content = json.dumps(report_data, indent=2)

            # Save report
            report_path.write_text(report_content)
            print(f"Report saved to {report_path}")

            # Update task
            task.report_status = "completed"
            task.report_generated_at = datetime.now()
            task.report_session_id = report_session_id
            task.status = TaskStatus.REPORTED
            task.save()

            return True

        except Exception as e:
            print(f"Failed to generate report: {e}")
            task.report_status = "failed"
            task.save()
            return False

    def load_template(self, template_path: str) -> str:
        """Load a report template

        Args:
            template_path: Path to template file

        Returns:
            Template content
        """
        # Try user's context first
        user_template = Path(template_path)
        if user_template.exists():
            return user_template.read_text()

        # Try in the configured reports directory
        path = Path(template_path)
        if not path.is_absolute():
            path = self.reports_dir / path.name
            if path.exists():
                return path.read_text()

        # Fall back to package templates
        template_name = Path(template_path).name
        try:
            return (
                resources.files("contextualize.resources.templates.reports")
                .joinpath(template_name)
                .read_text()
            )
        except:
            # Ultimate fallback to default template
            try:
                return (
                    resources.files("contextualize.resources.templates.reports")
                    .joinpath("default.md")
                    .read_text()
                )
            except:
                # If even package resources fail, return minimal template
                return """# Task Report: {{task_id}}
## Summary
{{summary}}
## Details
{{details}}"""

    def build_report_prompt(self, task: Task, template: str) -> str:
        """Build the prompt for report generation

        Args:
            task: Task to report on
            template: Template content

        Returns:
            Complete prompt for Claude
        """
        # Calculate duration
        duration = "N/A"
        if task.started_at and task.completed_at:
            delta = task.completed_at - task.started_at
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                duration = f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                duration = f"{minutes}m {seconds}s"
            else:
                duration = f"{seconds}s"

        prompt = f"""You just completed a task in the Contextualize framework.
Please generate a comprehensive report based on what happened in this session.

TASK DETAILS:
- Task ID: {task.task_id}
- Description: {task.description}
- Status: {task.status.value}
- Started: {task.started_at.isoformat() if task.started_at else 'N/A'}
- Completed: {task.completed_at.isoformat() if task.completed_at else 'N/A'}
- Duration: {duration}
- Concepts Used: {', '.join(task.concepts) if task.concepts else 'None'}

REPORT TEMPLATE:
{template}

INSTRUCTIONS:
1. Review the entire session to understand what was attempted and achieved
2. Fill in ALL template variables (marked with {{{{variable}}}}) based on the session
3. Be concise but comprehensive
4. Focus on concrete outcomes and actionable insights
5. Include specific file paths, commands, or code changes where relevant
6. Return ONLY the filled template, no additional commentary

The report should accurately reflect what happened in this specific task execution."""

        return prompt

    def _get_report_path(self, task: Task) -> Path:
        """Get the path where report should be saved

        Args:
            task: Task to get report path for

        Returns:
            Path to report file
        """
        # Determine extension from template
        template_path = task.report_template or "context/reports/default.md"
        extension = Path(template_path).suffix

        return task.task_dir / f"report{extension}"

    def list_templates(self) -> list:
        """List available report templates

        Returns:
            List of template names
        """
        templates = []
        if self.reports_dir.exists():
            for template_file in self.reports_dir.glob("*.*"):
                if template_file.suffix in [".md", ".json", ".yaml", ".yml"]:
                    templates.append(template_file.name)
        return templates
