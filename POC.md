# Proof of Concept: Context Window Management System

## The Solution: MCP-Based Task Framework

We've identified a clean approach using Claude Code's MCP (Model Context Protocol) server capabilities to create a fully observable, resumable task execution system.

## Core Innovation

Instead of trying to capture Claude's ephemeral subtasks, we make EVERY operation a managed task that:
1. Runs as its own Claude session with a controlled session ID
2. Loads only the context it needs
3. Logs everything to a persistent filesystem structure
4. Reports completion in a structured format
5. Can be forked, resumed, or inspected at any time

## How It Works: The Complete Flow

### 1. Setup Phase (One-time)

```bash
# Start Claude with our MCP server
$ claude --mcp-config task-framework-mcp.json

# This loads our custom tools:
# - launch_task
# - complete_task
# - fork_task
# - view_dag
```

### 2. Main Agent Workflow

The main Claude session acts as the **orchestrator**. You prompt it normally, but instruct it to use managed tasks for any substantial work:

```
User: "I need to debug the failing authentication tests and then refactor the auth module"

Claude: I'll break this into managed tasks for better tracking and context isolation.
Let me first debug the tests:

[Uses launch_task tool]
> launch_task(description="Debug authentication test failures", concepts=["testing", "auth", "debugging"])
> Task abc-123 launched...

[Task runs in background with only auth/testing context loaded]
[Task completes and reports back]

Now I'll refactor based on what we learned:

[Uses fork_task tool]
> fork_task(parent_task_id="abc-123", description="Refactor auth module based on test findings")
> Task def-456 launched...
```

### 3. Task Execution Flow

Each task launched by the main agent:

1. **Gets a unique session ID** - We control this completely
2. **Loads minimal context** - Only specified concepts, not entire codebase
3. **Runs independently** - Own Claude subprocess with `--print` mode
4. **Logs everything** - Output captured to `logs/{task_id}/`
5. **Reports back** - Uses `complete_task` tool to save structured report
6. **Updates DAG** - Parent-child relationships tracked automatically

### 4. Key Principles for Main Agent

The main agent should be prompted with these guidelines:

```markdown
# Task Management Guidelines

You are operating with the Context Window Management System. Follow these principles:

## When to Create Tasks
- Any operation that requires focused work (debugging, refactoring, analysis)
- When switching between different areas of the codebase
- When you need to try multiple approaches to solve a problem

## How to Use Tasks
1. Break complex requests into discrete tasks
2. Specify only the concepts each task needs
3. Use fork_task when a previous task failed or needs a different approach
4. Check view_dag periodically to show progress

## Context Selection
- testing: For test-related work
- auth: For authentication logic
- database: For DB operations
- api: For API endpoints
- frontend: For UI work
[etc - based on available concepts]

## Task Chaining
- Use parent_id to maintain task relationships
- Fork from failures to try alternatives
- Build a tree of exploration, not a linear sequence
```

---

## CLI Tooling

### The `cw` Command (Context Wrapper)

A simple Python CLI that wraps common operations:

```python
#!/usr/bin/env python3
# cw - Context Wrapper CLI

import click
import json
import subprocess
from pathlib import Path
from datetime import datetime

@click.group()
def cli():
    """Context Window Management System CLI"""
    pass

@cli.command()
@click.option('--mcp-config', default='task-framework-mcp.json')
def start(mcp_config):
    """Start Claude with the task framework MCP server"""
    click.echo("Starting Claude with Context Management Framework...")
    click.echo("Remember to use launch_task for all substantial work!")
    subprocess.run(['claude', '--mcp-config', mcp_config])

@cli.command()
@click.argument('task_id')
def inspect(task_id):
    """Inspect a completed task"""
    task_dir = Path(f'logs/{task_id}')
    if not task_dir.exists():
        click.echo(f"Task {task_id} not found")
        return

    # Show metadata
    metadata = json.loads((task_dir / 'metadata.json').read_text())
    click.echo(f"Task: {metadata['description']}")
    click.echo(f"Status: {metadata['status']}")
    click.echo(f"Concepts: {', '.join(metadata['concepts'])}")

    # Show report if exists
    report_file = task_dir / 'report.json'
    if report_file.exists():
        report = json.loads(report_file.read_text())
        click.echo(f"\nSummary: {report['summary']}")
        if report.get('files_modified'):
            click.echo(f"Files: {', '.join(report['files_modified'])}")

@cli.command()
@click.argument('task_id')
def resume(task_id):
    """Resume a task session (if still in memory)"""
    task_dir = Path(f'logs/{task_id}')
    metadata = json.loads((task_dir / 'metadata.json').read_text())
    session_id = metadata.get('session_id')
    click.echo(f"Attempting to resume session {session_id}...")
    subprocess.run(['claude', '--resume', session_id])

@cli.command()
def dag():
    """View the task DAG in browser"""
    from visualize_dag import generate_dag_html
    generate_dag_html()
    click.echo("DAG visualization opened in browser")

@cli.command()
@click.option('--limit', default=10)
def tasks(limit):
    """List recent tasks"""
    dag_file = Path('logs/dag.jsonl')
    if not dag_file.exists():
        click.echo("No tasks yet")
        return

    tasks = []
    with open(dag_file) as f:
        for line in f:
            tasks.append(json.loads(line))

    for task in tasks[-limit:]:
        status_icon = "✅" if task['status'] == 'completed' else "❌" if task['status'] == 'failed' else "🔄"
        parent = f" (fork of {task['parent_id'][:8]})" if task.get('parent_id') else ""
        click.echo(f"{status_icon} {task['task_id'][:8]}: {task['description'][:50]}{parent}")

if __name__ == '__main__':
    cli()
```

### Usage Examples

```bash
# Start Claude with our framework
$ cw start

# In Claude, work normally but use tasks:
> "Debug the auth tests"
> [Claude uses launch_task automatically]

# From another terminal, monitor progress:
$ cw tasks
🔄 abc123de: Debug authentication test failures
✅ def456gh: Analyze test coverage
❌ ghi789jk: Refactor auth module (fork of abc123de)

# Inspect a specific task
$ cw inspect abc123de
Task: Debug authentication test failures
Status: completed
Concepts: testing, auth, debugging
Summary: Fixed mock initialization issue in auth tests

# View the DAG visualization
$ cw dag
[Opens browser with interactive DAG]

# Resume a session if needed
$ cw resume abc123de
```

---

## Background Execution Options

### Option 1: Async MCP Tools (Recommended)

Modify the `launch_task` tool to run asynchronously:

```python
@tool(name="launch_task_async")
async def launch_task_async(args: dict[str, Any]) -> dict[str, Any]:
    # Create task and return immediately
    metadata = framework.create_task(...)

    # Launch subprocess without waiting
    process = subprocess.Popen([
        "claude", "--print", "--session-id", session_id, prompt
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Save process ID for monitoring
    (task_dir / "pid").write_text(str(process.pid))

    return {
        "content": [{
            "type": "text",
            "text": f"Task {task_id} launched in background. Use check_task to monitor."
        }]
    }
```

### Option 2: Task Queue Pattern

The main agent adds tasks to a queue, and a separate worker processes them:

```python
# Main agent just queues tasks
queue_task(description="Debug auth tests", concepts=["testing", "auth"])

# Separate worker process runs tasks
while True:
    task = get_next_task()
    if task:
        execute_task(task)
```

For the POC, synchronous execution is fine - it keeps things simple and observable.

---

## Project Structure
```yaml
# .claude/commands/task-run.md
---
name: task-run
description: Run task with context management
---

Execute task with proper context isolation:
1. Generate task_id
2. Load only specified concepts
3. Create session folder
4. Stream output to file
5. Generate report on completion

Usage: /task-run --task=debug-test --concepts=testing,debugging
```

### 3. MCP Server Approach
Create an MCP server for context management:

```javascript
// mcp-context-manager/index.js
{
  tools: {
    "context_load": {
      description: "Load specific concepts for this task",
      parameters: {
        concepts: { type: "array", items: { type: "string" } }
      }
    },
    "task_register": {
      description: "Register a new task in the DAG",
      parameters: {
        parent_id: { type: "string" },
        description: { type: "string" }
      }
    },
    "report_write": {
      description: "Write task completion report",
      parameters: {
        task_id: { type: "string" },
        report: { type: "string" }
      }
    }
  }
}
```

Launch with: `claude --mcp-config ./mcp-context-manager.json`

---

## Technical Exploration

### Session State Capture

**Option A: File Watching**
```python
# Watch Claude Code's working directory
import watchdog
watcher = watchdog.observers.Observer()
watcher.schedule(SessionHandler(), path='.', recursive=True)
```

**Option B: Process Monitoring**
```python
# Monitor Claude Code process tree
import psutil
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if 'claude' in proc.info['name']:
        # Track subprocess creation
```

**Option C: Hook via Settings**
```json
// .claude/settings.json
{
  "hooks": {
    "task_start": "context-manager start ${task_id}",
    "task_complete": "context-manager complete ${task_id}"
  }
}
```

### Live Session Tailing

```bash
# Could we tail Claude Code's output?
$ tail -f ~/.claude/logs/current-session.log

# Or intercept via pipe?
$ claude 2>&1 | tee >(context-manager capture)
```

---

## Minimal Weekend POC

### Saturday: Foundation
1. **Morning:** Context mesh with references
   - Create concepts/ structure
   - Build reference resolver
   - Simple CLI to load concept graph

2. **Afternoon:** Session tracking
   - Filesystem watcher for Claude Code
   - Capture task starts/completes
   - Write metadata and logs

### Sunday: Magic Features
1. **Morning:** Session operations
   - List sessions command
   - View session history
   - Basic fork implementation

2. **Afternoon:** Visualization
   - Simple web UI showing DAG
   - Click to view session details
   - Maybe: Mermaid diagram generation

---

## Key Technical Questions

1. **Can we intercept Claude Code task creation?**
   - Check if SDK exposes hooks
   - Look for log files we can tail
   - Investigate process monitoring

2. **Can we inject context into Claude Code?**
   - Via /import command?
   - Through MCP tools?
   - By modifying CLAUDE.md on the fly?

3. **Can we fork/resume sessions?**
   - Export current state
   - Modify context
   - Import as new session

4. **Real-time streaming?**
   - Does Claude Code write logs we can tail?
   - Can we pipe stdout/stderr?
   - WebSocket connection possible?

---

## The Actual Implementation

### Leveraging Claude Code's Native Features

```python
#!/usr/bin/env python3
# context-manager.py

import subprocess
import json
import uuid
from pathlib import Path

class ContextManager:
    def __init__(self):
        self.sessions_dir = Path("./sessions")
        self.sessions_dir.mkdir(exist_ok=True)

    def start_task(self, prompt, concepts=[]):
        """Start a new Claude Code session with specific context"""
        session_id = str(uuid.uuid4())

        # Load only required concepts
        context = self.load_concepts(concepts)

        # Start Claude with streaming JSON output
        process = subprocess.Popen([
            "claude",
            "--session-id", session_id,
            "--output-format", "stream-json",
            "--print",
            f"{context}\n\n{prompt}"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Stream output to session log
        session_path = self.sessions_dir / session_id
        session_path.mkdir(exist_ok=True)

        with open(session_path / "stream.jsonl", "w") as f:
            for line in process.stdout:
                f.write(line.decode())
                # Parse and display in real-time
                self.process_stream_line(line)

        return session_id

    def fork_session(self, parent_id, at_message=None):
        """Fork an existing session"""
        # Use Claude's native fork capability
        result = subprocess.run([
            "claude",
            "--resume", parent_id,
            "--fork-session",
            "--print",
            "Continue from here with a different approach"
        ], capture_output=True, text=True)

        # Extract new session ID from output
        return self.extract_session_id(result.stdout)

    def visualize_dag(self):
        """Generate DAG visualization from session logs"""
        # Read all session metadata
        # Build parent-child relationships
        # Generate Mermaid diagram or web view
        pass
```

### The Magic Command Wrapper

```bash
#!/bin/bash
# cw (context wrapper)

case "$1" in
    start)
        python3 context-manager.py start "$2" "${@:3}"
        ;;
    fork)
        python3 context-manager.py fork "$2"
        ;;
    resume)
        claude --resume "$2"
        ;;
    visualize)
        python3 context-manager.py visualize
        open http://localhost:8080
        ;;
esac
```

## Impact Demonstration

### The "Wow" Demo

```bash
# Start a complex refactor with minimal context
$ cw start "refactor auth system" --concepts=auth,api

> Session abc123 started with 2 concepts loaded (not 50!)
> Streaming output to sessions/abc123/stream.jsonl

# It fails after trying approach A
> ERROR: Type conflicts in auth module

# Fork and try different approach
$ cw fork abc123
> Forked to session def456
> "Let me try a different approach..."

# Resume with stronger model
$ claude --resume abc123 --model opus
> "Looking at the type conflicts..."

# Visualize the exploration tree
$ cw visualize
> DAG rendered at http://localhost:8080
```

**The Money Shot:** A DAG showing multiple solution attempts branching from failure points, with some paths succeeding where others failed. Each node clickable to see what happened.

---

## Tools & Libraries

### Required
- Python/Node for orchestration
- File watcher (watchdog/chokidar)
- Simple web server for UI
- YAML parser

### Nice to Have
- Mermaid for DAG rendering
- SQLite for session index
- WebSocket for live updates

---

## Success Criteria

A POC is successful if it demonstrates:

1. **Context segmentation works** - Loading only needed concepts improves performance
2. **Sessions are recoverable** - Failed work can be resumed/forked
3. **The DAG tells a story** - Visual representation shows how problems were solved
4. **It feels magical** - The demo makes people say "I need this"

---

## Impact & Distribution Strategy

### The Goal
Become part of the conversation shaping AI-assisted development. Get the ideas adopted, not necessarily build everything ourselves.

### Distribution Plan

**Week 1: Build POC**
- Weekend: Core implementation
- Monday-Tuesday: Polish and document
- Wednesday: Record demo video

**Week 2: Launch**
1. **Blog Post:** "How Coding Agents Should Actually Work"
   - Link to manifesto (README)
   - Link to framework (FRAMEWORK.md)
   - Embed demo video
   - Include GitHub repo

2. **Target Audiences:**
   - Post on HN: "Show HN: Context segmentation for AI coding agents"
   - Post on r/LocalLLaMA, r/ArtificialInteligence
   - Tweet thread with video clips
   - LinkedIn post for professional network

3. **Direct Outreach:**
   - Open issue on Gemini CLI: "Proposal: Context mesh and session persistence"
   - Comment on Claude Code feedback forum
   - Reach out to tool creators on Twitter

### The Multiplier Effect

Even a simple POC that shows:
- A task forking after failure
- The same task succeeding with different context
- A DAG visualization of the exploration

...will make the concept tangible. Once people see it, they'll want it.

### Long-term Vision

**Success looks like:**
- Other tools adopt context segmentation
- Session persistence becomes standard
- Someone builds the full framework
- You're cited as introducing these concepts
- Conversations with tool builders about implementation

**The real win:** These ideas become part of how AI coding tools work, whether or not you build the full system.

---

## Claude Code Session Investigation

### Where Sessions Are Stored
Based on investigation, Claude Code stores data in:

1. **~/.claude.json** - Main configuration and project history
   - Contains `projects` object with per-project data
   - Each project has a `history` array
   - History items are minimal (just display text, no full conversation)

2. **~/.claude/todos/** - Task tracking (but files are mostly empty `[]`)
   - UUID-based filenames
   - Format: `{uuid}-agent-{uuid}.json`

3. **Session IDs are ephemeral**
   - Generated at runtime with `--session-id <uuid>`
   - Returned in JSON output: `"session_id": "62adeb86-a758-437a-865e-0dceb81761c2"`
   - Not persisted to disk in accessible format

### Critical Findings

**No accessible subtask data!**
- Subtasks execute in memory only
- No logs or output files created
- No way to "enter" a completed subtask
- Output vanishes after completion

**Session resumption is limited:**
- `--resume [sessionId]` works but requires the session to exist in memory
- `--fork-session` creates a new branch but doesn't preserve task state
- No access to subtask internals

### Implications for POC

**Can't directly access Claude Code subtask data.**

This means we need to:
1. **Intercept at runtime** - Capture streaming output as tasks execute
2. **Build our own persistence layer** - Save what Claude Code doesn't
3. **Use Gemini CLI fork** for true implementation

## The Breakthrough: Controlled Task Execution

### The Solution: Custom Task Launcher Command!

Instead of trying to capture ephemeral subtasks, we create a `.claude/commands/task.md` that:

```python
#!/usr/bin/env python3
# task-launcher.py - Called by our custom command

import subprocess
import uuid
import json
from pathlib import Path
from datetime import datetime

def launch_task(prompt, parent_id=None, concepts=[]):
    task_id = str(uuid.uuid4())
    task_dir = Path(f"logs/{task_id}")
    task_dir.mkdir(parents=True, exist_ok=True)

    # 1. SETUP: Write metadata
    metadata = {
        "task_id": task_id,
        "parent_id": parent_id,
        "started_at": datetime.now().isoformat(),
        "concepts": concepts,
        "prompt": prompt
    }
    (task_dir / "metadata.json").write_text(json.dumps(metadata))

    # 2. Load only required concepts
    context = load_concepts(concepts)

    # 3. Create the prompt with report instruction
    full_prompt = f"""
{context}

TASK: {prompt}

IMPORTANT: When complete, end your response with:

---REPORT---
## Task Report
- What was attempted:
- What was accomplished:
- Files modified:
- Issues encountered:
- Next steps:
---END REPORT---
"""

    # 4. EXECUTE: Run Claude with full output capture
    # Generate our own session ID so we can track it
    session_id = str(uuid.uuid4())

    # Append report instructions to system prompt
    report_instruction = """

    IMPORTANT: End your response with a structured report:
    ---REPORT---
    Task ID: {task_id}
    Status: [success/failed]
    Files Modified: [list files]
    Summary: [what was accomplished]
    ---END REPORT---
    """.format(task_id=task_id)

    result = subprocess.run([
        "claude",
        "--print",
        "--output-format", "json",
        "--session-id", session_id,
        "--append-system-prompt", report_instruction,
        full_prompt  # The actual task prompt
    ], capture_output=True, text=True, cwd=Path.cwd())

    # 5. CAPTURE: Save everything
    (task_dir / "output.json").write_text(result.stdout)
    (task_dir / "stderr.txt").write_text(result.stderr)

    # 6. EXTRACT: Parse report from output
    output_data = json.loads(result.stdout)
    response = output_data.get("result", "")

    if "---REPORT---" in response:
        report = response.split("---REPORT---")[1].split("---END REPORT---")[0]
        (task_dir / "report.md").write_text(report)

    # 7. COMPLETE: Update metadata
    metadata["completed_at"] = datetime.now().isoformat()
    metadata["session_id"] = output_data.get("session_id")
    metadata["success"] = not output_data.get("is_error", False)
    (task_dir / "metadata.json").write_text(json.dumps(metadata))

    print(f"Task {task_id} completed. Logs at: {task_dir}")
    return task_id
```

### The Custom Command

```markdown
# .claude/commands/task.md
---
name: task
description: Run a task with context management and logging
---

You are about to run a managed task. This task will:
1. Be logged to a unique directory
2. Have its output captured
3. Generate a report

Use the following Python script to launch the task:

$ARGUMENTS

```python
import subprocess
subprocess.run(["python3", "task-launcher.py", "$ARGUMENTS"])
```

Remember to end with a structured report as instructed.
```

### Bonus: Custom Agents on the Fly!

We can even create specialized agents dynamically:

```python
def launch_specialized_task(prompt, agent_type="debugger"):
    # Define agent based on type
    agents = {
        "debugger": {
            "description": "Debug test failures",
            "prompt": "You are a test debugging specialist. Focus on root causes."
        },
        "refactorer": {
            "description": "Refactor code",
            "prompt": "You refactor code for clarity and performance."
        }
    }

    result = subprocess.run([
        "claude",
        "--print",
        "--agents", json.dumps({agent_type: agents[agent_type]}),
        "--session-id", session_id,
        prompt
    ], capture_output=True, text=True)
```

### This Enables Everything!

Now we can:
1. **Launch tasks deterministically**: Each task gets its own Claude session with controlled ID
2. **Control context precisely**: Load only needed concepts in the prompt
3. **Capture all output**: Everything saved to `logs/{task_id}/`
4. **Generate reports**: Via `--append-system-prompt`
5. **Build the DAG**: Track parent_id relationships
6. **Resume/Fork**: Use saved session_id with `--resume`
7. **Custom agents**: Create specialized agents with `--agents`

### Usage Example

```bash
# Start a task
$ claude "/task debug the auth test --concepts testing,auth"
> Launching task abc123...
> Task completed. Logs at: logs/abc123/

# Fork from failure
$ python3 task-launcher.py --fork abc123 "try different approach"
> Forked to task def456 from abc123

# View the DAG
$ python3 visualize-dag.py
> DAG served at http://localhost:8080
```

## Next Steps

### Immediate (This Weekend)
1. [ ] Fork Gemini CLI repo
2. [ ] Create basic context mesh
3. [ ] Add session persistence layer
4. [ ] Build simple DAG visualizer
5. [ ] Record compelling demo

### Follow-up (Next Week)
1. [ ] Write blog post
2. [ ] Create video walkthrough
3. [ ] Submit to aggregators
4. [ ] Open discussions with tool maintainers

The goal isn't perfection—it's starting a movement. Show that context can be managed, sessions can be persistent, and AI work can be observable. Let the community take it from there.