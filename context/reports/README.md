# Report Templates

This directory contains YOUR project's report templates for generating structured task reports.

This is part of your project's context and should be committed to git.

## How Reports Work

1. Every task generates a report upon completion
2. Reports are saved to `logs/{task_id}/report.md` (or `.json`, `.yaml`)
3. Templates use `{{variable}}` placeholders that are filled by the report generator
4. Default template (`default.md`) is used if no specific template is specified

## Available Templates

- `default.md` - Generic task report (fallback for all tasks)
- `command.md` - Command execution report
- `research.md` - Research/investigation report
- `bug-fix.md` - Bug resolution report

## Creating Custom Templates

You can add your own templates to this directory:

1. Create a new `.md`, `.json`, or `.yaml` file
2. Use `{{variable}}` syntax for placeholders
3. Reference it when starting a task: `ctx task start --report-template my-template`

## Template Variables

Common variables available in all templates:

- `{{task_id}}` - Unique task identifier
- `{{description}}` - Task description
- `{{started_at}}` - Start timestamp
- `{{completed_at}}` - Completion timestamp
- `{{duration}}` - Execution duration
- `{{status}}` - Final task status
- `{{concepts}}` - Concepts used

The report generator will prompt Claude to fill in context-specific variables based on the actual task execution.

## JSON Templates

For structured data, use `.json` templates:

```json
{
  "task_id": "{{task_id}}",
  "summary": "{{summary}}",
  "metrics": {
    "duration": "{{duration}}",
    "status": "{{status}}"
  }
}
```

The report generator will ensure valid JSON output when using JSON templates.
