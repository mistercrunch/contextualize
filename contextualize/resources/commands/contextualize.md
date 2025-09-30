---
name: contextualize
description: Execute a task with automatic context management
arguments: Task description and any specific requirements
---

# Contextualize Task Execution

You should use the ContextualizeAgent to execute this task with proper context management and tracking.

## Task to execute:

$ARGUMENTS

## Instructions:

Please use the Task tool with `subagent_type="contextualize"` to execute this request. The ContextualizeAgent will:

1. Automatically detect and load relevant concepts
2. Create a tracked task with unique ID
3. Execute with focused context
4. Generate a report upon completion

Example invocation:

```
Task(
    description="Contextualized task execution",
    subagent_type="contextualize",
    prompt="$ARGUMENTS"
)
```

The ContextualizeAgent is specialized for:

- Smart context loading based on task analysis
- Automatic concept detection and validation
- Task tracking and observability
- Report generation with appropriate templates

Let the agent handle all the details of context management - just pass through the task description and let it work its magic.
