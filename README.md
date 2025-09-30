# Contextualize

**A framework for structured, active context engineering built on Claude Code**

## What is Contextualize?

Contextualize extends Claude Code with three core capabilities:

1. **Structured Context Organization** - Organize your project knowledge as a collection of interconnected concept files, not monolithic documentation
2. **Subtask-Oriented Execution** - Each spawned task gets precisely the context it needs, nothing more, nothing less
3. **Active Session Management** - Wraps Claude's subtasks in a framework that enables task isolation, introspection, persistence, and multi-session orchestration

## The Problem

Claude Code is powerful, but operates with significant limitations:

### The Context Segmentation Dilemma

Power users have discovered that **context segmentation is key** to getting great results from Claude. Using the `Task` tool or subagents to manage context more actively can be powerful—giving focused context to specific problems. But this approach comes with significant drawbacks:

- **No persistence** - subtasks vanish when complete
- **No observability** - can't inspect what happened
- **No resumability** - can't pick up where you left off
- **No relationships** - can't track task dependencies or failures

You're forced to choose: either dump everything into context (and get confused responses), or use ephemeral subtasks (and lose all your work history).

### One-Size-Fits-All Context

Without proper segmentation tools, projects rely on monolithic `CLAUDE.md` files that dump everything into context. Every task—whether fixing a typo or refactoring architecture—gets the same overwhelming context. This leads to:

- Token waste on irrelevant information
- Confused responses mixing unrelated concerns
- Hallucinated imports from parts of the codebase not actually needed

### Limited Context Management

While Claude Code's `.claude/commands/` and `.claude/agents/` directories offer some ways to manage certain types of context, they're:

- Limited to specific use cases (commands and agent personalities)
- Not composable or reusable across tasks
- Still require dumping everything into the main session

### Context Fragmentation

Every AI tool wants its own format:

- `CLAUDE.md` for Claude
- `CURSOR.md` for Cursor
- `.aider.conf.yml` for Aider
- `.claude/` directories aren't universal
- No reusability across tools or sessions

## How It Works

Contextualize solves these problems through `ctx`, a **companion CLI for Claude Code** that intercepts and enhances the task workflow.

### High-Level Flow

1. **Organize Knowledge** - Break your project context into focused concept files instead of one massive document
2. **Launch Targeted Tasks** - Use `ctx` to spawn Claude sessions with only the concepts each task needs
3. **Track Everything** - Every task gets logged with full input/output, creating a persistent knowledge graph
4. **Resume & Fork** - Jump back into any session or branch from failure points

### Architecture Comparison

```
Traditional Claude:                    With Contextualize:
┌─────────────┐                        ┌─────────────┐
│   Main      │                        │   Main      │
│  Session    │                        │  Session    │
│             │                        │             │
│ Everything  │                        │ Orchestrator│
│ in context  │                        │    only     │
└─────┬───────┘                        └─────┬───────┘
      │                                      │
      ▼                                      ▼
┌─────────────┐                        ┌─────────────┐
│  Subtask    │                        │  Task 1     │
│             │                        │ ┌─────────┐ │
│ (ephemeral) │                        │ │Concepts:│ │
│             │                        │ │auth,api │ │
└─────────────┘                        │ └─────────┘ │
                                       │  Logged     │
                                       │  Persistent │
                                       └─────────────┘
```

### What Contextualize Provides

Instead of ephemeral subtasks with full context, Contextualize creates:

- **Isolated sessions** with targeted context via `claude --session-id`
- **Persistent task records** with full I/O logging in `logs/`
- **Concept loading** from your `context/concepts/` knowledge base
- **Task relationships** tracked in a visual DAG

## Key Features

### 🎯 **Surgical Context Loading**

- Load only relevant "concepts" per task
- Self-referencing knowledge network
- Reusable, composable context modules

### 🔀 **Multi-Session Orchestration**

- Each task runs in its own Claude session
- Parallel task execution without context pollution
- Session IDs enable persistence and resumability

### 🔍 **Full Observability**

- Track all tasks in a visual DAG
- Complete input/output logging
- Inspect any task's context and results

### ⏮️ **Time Travel & Forking**

- Resume any session exactly where it left off
- Fork from any task when issues arise
- Build on previous work without starting over

### 🦘 **Session Hopping**

- Jump between related tasks
- Carry forward learned context
- Build a living knowledge graph as you work

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/contextualize.git
cd contextualize

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Setup

The `ctx` CLI works alongside `claude` as a companion tool:

```bash
# Step 1: Install Claude Code integration (optional but recommended)
ctx install
# Choose 'project' for local .claude/ or 'global' for ~/.claude/

# Step 2: Initialize Contextualize in your project
ctx init

# This creates:
# - context/concepts/ - Your reusable knowledge modules
# - logs/ - Task history and outputs
# - .claude/commands/ - Custom Claude commands (if project install)
```

### Basic Usage

```bash
# Initialize project
ctx init

# Manage concepts
ctx concept list                    # List all concepts
ctx concept new auth                # Create new concept
ctx concept show auth                # View concept content

# Manage tasks
ctx task start "Fix OAuth bug" -c auth,debugging
ctx task list                       # View recent tasks
ctx task show <id>                  # Inspect task details
ctx task resume <id>                # Resume session
ctx task fork <id> "Try new approach"  # Fork from task

# Check status
ctx status                          # Overall project status
ctx task status                     # All task statuses
```

## Core Concepts

### Concepts

Reusable knowledge modules in `context/concepts/`. Each concept is a markdown file with frontmatter:

```markdown
---
name: auth
references: [core, oauth]
---

# Authentication Concepts

## OAuth Flow
- Token refresh mechanism
- Error handling patterns
- Security considerations
```

### Tasks

Every substantial piece of work becomes a tracked task with:

- Unique ID and session
- Isolated context (only needed concepts)
- Full input/output logging
- Parent relationships (for forks)

### DAG (Directed Acyclic Graph)

Visual representation of task relationships showing:

- Task dependencies
- Fork points
- Success/failure status
- Execution timeline

## Philosophy

> "Context is everything, but everything is not context."

Traditional AI coding assistants fail because they try to understand everything at once. Contextualize embraces the opposite: give AI agents **exactly what they need** for each specific task.

This isn't just about managing files - it's about structuring knowledge for optimal AI consumption. By treating context as a carefully curated network rather than a document dump, we enable AI to work with precision instead of confusion.

## Example Workflow

```bash
# 1. Initialize your project
ctx init

# 2. Create a concept for your authentication system
ctx concept new auth
# Edit context/concepts/auth.md with your auth docs

# 3. Start a focused task
ctx task start "Implement token refresh rotation" -c auth,testing

# 4. Task runs in isolated Claude session
# Output: Task 8f3d2a created

# 5. Check progress
ctx task show 8f3d

# 6. If it fails, fork and retry
ctx task fork 8f3d "Fix import error and retry"

# 7. Resume later
ctx task resume 8f3d
```

## Advanced Features

### Async Task Execution

Run tasks in background while continuing work:

```bash
ctx launch-async --desc "Generate test suite" --concepts "testing"
```

### Web-based DAG Visualization

```bash
python -m contextualize.dag_visualizer serve
# Opens browser with interactive DAG viewer
```

### Dogfooding Mode

Let Contextualize build itself:

```bash
ctx dogfood
# Launches Claude with context about the framework
```

## Project Status

**⚠️ Proof of Concept**

This is an early POC demonstrating active context engineering. Expect rough edges and breaking changes.

### Working Features ✅

- Basic task launching and tracking
- Concept organization and loading
- DAG visualization
- Session fork and resume
- CLI interface

### In Development 🚧

- Full MCP server integration
- Better async execution
- Concept auto-discovery
- Cloud persistence
- Multi-agent coordination

## Project Goals

### Immediate: Empower Claude Code Users

Enable Claude Code power users to take context engineering to the next level through:

- **Better context management** - Move beyond monolithic CLAUDE.md files
- **Active session orchestration** - Control multiple focused sessions instead of one bloated context
- **Full observability** - See what your AI agents are actually doing
- **Knowledge persistence** - Build on previous work instead of starting fresh

### Long-term: Inspire Native Implementation

This project serves as a **proof of concept** for enhanced workflows that could inspire the Claude Code team to implement these concepts natively:

- Demonstrate the value of context segmentation
- Prove that session persistence improves productivity
- Show how task relationships enable better debugging
- Validate that targeted context leads to better AI performance

If these patterns gain traction and prove valuable to the community, they could influence the future direction of Claude Code itself.

## Contributing

We're exploring the future of AI-assisted development. If you're a Claude Code power user who's felt the pain of context management, we'd love your input:

- Share your workflows and pain points
- Contribute concepts and patterns
- Help test and refine the framework
- Spread the word if it helps your productivity

## License

MIT

## Links

- [Blog: Context is Everything](./BLOG.md) - Philosophical foundations
- [Framework Design](./FRAMEWORK.md) - Technical architecture
- [Core Concepts](./context/concepts/core.md) - Framework principles

---

*Built with Claude, for Claude, using Claude* 🤖
