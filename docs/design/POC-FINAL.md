# Context Window Management System - POC

## The Solution

We use Claude Code's MCP (Model Context Protocol) server to create a fully observable, persistent task execution system where every operation is tracked, logged, and resumable.

## Architecture

```
Main Claude Session (Orchestrator)
    ├── launch_task() → Creates isolated Claude subprocess
    ├── fork_task() → Branches from existing task
    ├── view_dag() → Shows task relationships
    └── complete_task() → Records structured output

Each Task:
    ├── Own session ID (controlled)
    ├── Minimal context (only what's needed)
    ├── Full logging (logs/{task_id}/)
    └── Structured report (on completion)
```

## Implementation

### 1. MCP Server (`task-launcher-sdk.py`)

Provides deterministic Python tools via `@tool` decorator:

- `launch_task`: Creates new task with isolated context
- `fork_task`: Branches from existing task
- `complete_task`: Saves structured reports
- `view_dag`: Shows task hierarchy

### 2. Context Organization

```
context/
└── concepts/
    ├── testing.md      # Test strategies
    ├── auth.md         # Authentication logic
    ├── database.md     # DB patterns
    ├── api.md          # API conventions
    └── debugging.md    # Debug approaches
```

Each concept is atomic, self-contained knowledge that can reference other concepts.

### 3. Task Persistence

```
logs/
├── dag.jsonl           # Task relationships
└── {task_id}/
    ├── metadata.json   # Task configuration + session_id
    ├── input.json      # Complete input from main agent
    ├── context_from_main.md  # Additional context passed
    ├── output.json     # Claude's response
    ├── report.json     # Structured summary
    └── stderr.txt      # Error output
```

### Session ID Powers

Each task gets its own session ID which enables:

- **Resume**: `claude --resume {session_id}` to re-enter any task
- **Inspection**: `/status` within a session shows its ID
- **Fork**: `claude --resume {session_id} --fork-session` creates a branch
- **Persistence**: Session IDs are saved in metadata.json for later use

## Usage Flow

### Starting the System

```bash
# Launch Claude with our MCP server
$ cw start
# Or directly:
$ claude --mcp-config task-framework-mcp.json
```

### Main Agent Workflow

The main Claude session should be prompted with:

```markdown
You are operating with the Context Window Management System.

IMPORTANT: Use managed tasks for all substantial work:
- Use launch_task() for new operations
- Use fork_task() when retrying or exploring alternatives
- Use view_dag() to show progress
- Each task should load only the concepts it needs

Available concepts:
- testing: Test strategies and patterns
- auth: Authentication implementation
- database: DB operations
- api: API endpoints
- debugging: Debug techniques

Break complex requests into discrete, focused tasks.
```

### Example Interaction

```
User: Debug the failing auth tests and fix them

Claude: I'll handle this using managed tasks for better tracking.

First, let me check what's failing:
[Runs test command to gather context]

Now I'll analyze the failures with a focused task:

[Calls launch_task]
> launch_task(
    description="Analyze auth test failures",
    concepts=["testing", "auth", "debugging"],
    context_from_main="Test output shows: 'TokenValidationError at line 45'",
    relevant_info={
        "failing_tests": ["test_token_validation", "test_refresh_token"],
        "error_type": "TokenValidationError",
        "last_working_commit": "abc123"
    }
  )
> Task abc-123 launched with context from main session...
> Task completed. Found issue with token expiry check.

Now I'll implement the fix based on the analysis:

[Calls fork_task]
> fork_task(
    parent_task_id="abc-123",
    description="Fix token expiry validation logic"
  )
> Task def-456 launched...
> Task completed. Tests now passing.

[Calls view_dag]
> view_dag()
✅ abc-123: Analyze auth test failures
  └─ ✅ def-456: Fix token validation in auth tests
```

## CLI Tools

### The `cw` Command

```bash
# Start Claude with framework
$ cw start

# Monitor tasks
$ cw tasks
✅ abc123: Analyze auth test failures
✅ def456: Fix token validation (fork of abc123)
🔄 ghi789: Refactor auth module

# Inspect specific task
$ cw inspect abc123
Task: Analyze auth test failures
Status: completed
Concepts: testing, auth, debugging
Summary: Found token validation issue

# View DAG visualization
$ cw dag
# Opens browser with interactive DAG

# Resume a session (if still in memory)
$ cw resume abc123
```

## Key Benefits Demonstrated

1. **Context Isolation**: Tasks load only needed concepts (faster, cheaper)
2. **Full Observability**: Every task logged to `logs/{task_id}/`
3. **Fork & Resume**: Failed tasks can be retried with different approaches
4. **DAG Visualization**: See the exploration tree of solutions
5. **Structured Reports**: Each task produces parseable output

## Weekend Implementation Plan

### Saturday Morning: Core Infrastructure

- [ ] Set up context/concepts/ folder with 5-10 concepts
- [ ] Create task-launcher-sdk.py with MCP tools
- [ ] Test basic task launch and logging

### Saturday Afternoon: Task Management

- [ ] Implement fork_task for branching
- [ ] Add complete_task for reports
- [ ] Build DAG tracking

### Sunday Morning: CLI & Visualization

- [ ] Create `cw` CLI tool
- [ ] Build DAG HTML visualizer
- [ ] Add task inspection commands

### Sunday Afternoon: Demo & Documentation

- [ ] Record demo video showing task forking
- [ ] Show context isolation benefits
- [ ] Document setup instructions

## Success Metrics

The POC succeeds if it demonstrates:

1. **A task failing, then succeeding with different context/approach**
2. **Multiple parallel explorations visible in DAG**
3. **10x less context per task** (measure tokens)
4. **Complete task history preservation**

## The Pitch

"Current AI coding tools treat subtasks as black boxes that vanish. This framework makes every operation observable, resumable, and learnable. It's Git for AI sessions - every decision point preserved, every failure debuggable, every success reproducible."
