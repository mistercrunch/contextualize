# How Coding Agents Should Actually Work

## A Proposal for Context-First Development

### Draft v0.1

---

## The Current State of Coding Agents

Today's AI coding assistants—Claude Code, Cursor, Aider—have revolutionized development speed. Yet they share fundamental limitations in how they manage context and execution.

**The fragmentation problem:**

- Every tool demands its own context format: `CLAUDE.md`, `CURSOR.md`, `.aider.conf`
- The same knowledge gets duplicated across multiple files
- No universal standard for structuring project context
- Teams maintain parallel documentation for humans and each AI tool

**The context window crisis:**

- Context windows are precious and expensive computational resources
- Most tasks perform better with focused, relevant context
- Yet current tools force an all-or-nothing approach
- Loading unnecessary context degrades performance and increases costs
- The optimal solution—precise context per task—remains manual and error-prone

**The operational pain points:**

- Main sessions accumulate context from dozens of unrelated tasks
- Subtasks execute in black boxes—no logs, no debugging, no learning
- Developers hesitate to spawn subtasks they cannot observe
- Long-running tasks fail mysteriously without recovery options
- The choice becomes: overload with context (slow, expensive) or underload (failures)

**The tools have evolved rapidly, but the paradigm hasn't.**

## A Different Paradigm: Context-First Development

The current generation of coding agents treats context as monolithic and sessions as ephemeral. A context-first approach inverts these assumptions:

### Core Principle: Universal Context Standards

Context becomes tool-agnostic and modular:

- One source of truth for all agents and humans
- Structured knowledge that any tool can consume
- No more `CLAUDE.md` vs `CURSOR.md` duplication
- Context modules that compose based on task needs

### Core Principle: Precise Context Loading

Every subtask receives exactly the context required for its specific purpose:

- Test debugging loads testing patterns and error handling concepts
- API refactoring loads backend architecture and API conventions
- Database migrations load schemas and data models
- **Result:** Faster execution, lower costs, better outcomes

### Core Principle: Full Observability

All agent activity becomes inspectable and persistent:

- Any session can be entered, even after completion
- Streaming logs capture agent reasoning in real-time
- Structured reports document outcomes
- Failed tasks preserve full diagnostic information

### Core Principle: Non-Linear Workflows

Context segmentation enables exploration and recovery:

- Failed tasks can be forked to explore alternatives
- Dead sessions can be resumed with different models
- Previous contexts can be recycled into new sessions
- Multiple approaches can execute in parallel

## The Framework: Structure and Execution

### Persistent Session Architecture

```
logs/session_123/task_456/
├── metadata.yml    # Task configuration and context loaded
├── session.txt     # Real-time agent thoughts and actions
└── report.md       # Structured output of accomplishments
```

Every task becomes a permanent artifact—inspectable, resumable, learnable.

### Hierarchical Context Organization

```
context/
├── concepts/       # Atomic knowledge units
│   ├── testing.md  # Testing strategies and patterns
│   ├── auth.md     # Authentication architecture
│   └── api.md      # API conventions
├── agents/         # Specialized actors
│   ├── debugger.yml
│   └── refactorer.yml
└── commands/       # Reusable operations
    └── fix-test.yml
```

Knowledge becomes modular, reusable, and precisely loadable.

### Recovery and Exploration Patterns

```bash
# When a task fails
> Task 456 failed: Cannot resolve module

# Enter the failed session for inspection
> context restore session_123/task_456

# Fork to explore alternative solutions
> context fork session_123/task_456 --approach=alternative

# Escalate to a more capable model
> context resume session_123/task_456 --model=opus
```

Failure becomes a starting point, not an ending.

## The Paradigm Shift

**Current generation:** Each tool requires its own context format
**Context-first approach:** Universal standards work across all tools

**Current generation:** Context windows filled with irrelevant information
**Context-first approach:** Precise context injection per task

**Current generation:** Optimizes for single-session productivity
**Context-first approach:** Optimizes for systematic knowledge accumulation

**Current generation:** Treats context as monolithic blocks
**Context-first approach:** Treats context as composable, atomic units

**Current generation:** Makes subtasks ephemeral and opaque
**Context-first approach:** Makes every decision persistent and observable

## Implications

### For Development Practice

- Subtasks become the default, not the exception
- Context pollution becomes manageable through segmentation
- Failed tasks become recoverable assets
- Multiple solution paths can be explored simultaneously
- Past work becomes reusable knowledge

### For Team Collaboration

- Context libraries become shared resources
- AI workflows become observable and reviewable
- Problem-solving patterns become reproducible
- Collective learning emerges from individual sessions

### For Tool Evolution

- DAG visualization of AI work becomes possible
- Context modules become shareable packages
- Different approaches become benchmarkable
- The entire ecosystem can learn from usage patterns

## The End State

Picture a development environment where AI sessions render as explorable DAGs—tasks branching, merging, failing, succeeding. Every node is clickable, revealing exactly what transpired. Failed paths can be resumed. Successful paths can be forked for variation.

The transformation goes beyond incremental tool improvement. It represents a fundamental shift in how context is structured, how AI work is observed, and how knowledge accumulates in software development.

**The need is clear. The benefits are compelling.**
**The path forward requires collective design and implementation.**

---

## Part I: Context Engineering

### The Entity Model

Context organizes hierarchically from atomic concepts to complete transformations:

```
CONCEPTS (Atomic knowledge units)
    ↓ loaded by
AGENTS (Actors with capabilities)
    ↓ execute
COMMANDS (Parameterized operations)
    ↓ instantiate into
TASKS (Running instances)
    ↓ compose into
WORKFLOWS (Task DAGs)
    ↓ orchestrate into
PROJECTS (Transformations)
```

### 1. Concepts

Atomic, self-contained knowledge units that can reference other concepts.

```markdown
---
name: testing
type: concept
references:
  - assertions
  - mocking
---

# Testing Strategy

## Philosophy
Test behavior, not implementation.

## Commands
- Run all: `npm test`
- Single: `npm test {file}`
```

**Location:** `context/concepts/`
**Format:** Markdown with YAML frontmatter
**References:** Via `references` field or inline `@concepts/name`

### 2. Agents

Actors equipped with specific concepts and capabilities.

```yaml
---
name: test-debugger
type: agent
inherits: debugger
concepts:
  - testing
  - error-handling
  - debugging
capabilities:
  - analyze test failures
  - identify root causes
  - suggest fixes
---

# Test Debugger Agent

Specialized in diagnosing and fixing test failures.
```

**Location:** `context/agents/`
**Inheritance:** Agents can inherit from other agents
**Context Loading:** Union of inherited + declared concepts

### 3. Commands

Parameterized operations that agents can execute.

```yaml
---
name: debug-failing-test
type: command
agent: test-debugger
inputs:
  test_file:
    type: path
    required: true
  verbose:
    type: boolean
    default: false
additional_concepts:
  - ci-environment
outputs:
  report:
    schema: test-debug-report
    path: artifacts/reports/
---

# Debug Failing Test

Analyzes test failure and proposes fix.

## Execution Steps
1. Load test file and error output
2. Analyze failure pattern
3. Search for root cause in codebase
4. Propose and optionally apply fix
5. Generate detailed report
```

**Location:** `context/commands/`
**Context:** Agent concepts + additional_concepts
**Outputs:** Structured reports with schemas

### 4. Workflows

Compositions of commands with dependencies.

```yaml
---
name: test-and-fix
type: workflow
---

# Test and Fix Workflow

## DAG Definition
```yaml
steps:
  - id: run-tests
    command: run-all-tests

  - id: analyze-failures
    command: analyze-test-results
    depends_on: [run-tests]

  - id: debug-failures
    command: debug-failing-test
    depends_on: [analyze-failures]
    parallel: true  # One task per failure

  - id: verify-fixes
    command: run-all-tests
    depends_on: [debug-failures]
```

### 5. Projects

High-level transformations that orchestrate multiple workflows.

```yaml
---
name: migrate-to-typescript
type: project
status: active
---

# TypeScript Migration Project

## Transformation
From: JavaScript codebase
To: Fully typed TypeScript

## Workflows
1. analyze-codebase
2. convert-modules (parallel per module)
3. add-type-definitions
4. fix-type-errors
5. update-build-system

## Scope
- src/**/*.js → .ts
- tests/**/*.js → .ts
```

### Reference System

Deterministic loading through structured references:

```markdown
@concepts/testing        # Absolute from context root
./testing               # Same directory
../shared/auth          # Relative path
```

**Context Loading Rules:**

1. Load referenced concept recursively
2. Stop at already-loaded concepts (no cycles)
3. Union all concepts for task execution

---

## Part II: Execution & Observability Framework

### Session Management

Every AI interaction happens within a persistent session:

```
logs/
└── {session_id}/
    ├── metadata.yml           # Session metadata
    ├── context.yml           # Loaded context
    └── {task_id}/
        ├── metadata.yml      # Task metadata
        ├── session.txt       # Streaming output
        └── report.md         # Final report
```

### Task Metadata

```yaml
# logs/session_abc/task_123/metadata.yml
task_id: task_123
parent_ids: [root]            # Multiple parents = DAG
command: debug-failing-test
agent: test-debugger
model: claude-3-5-sonnet
status: completed
started_at: 2024-01-15T10:00:00Z
completed_at: 2024-01-15T10:05:00Z
context_loaded:
  - concepts/testing
  - concepts/debugging
inputs:
  test_file: tests/auth.test.js
outputs:
  report: ./report.md
  fixes_applied:
    - tests/auth.test.js
```

### DAG Tracking

Tasks can have multiple parents, enabling complex workflows:

```yaml
task_456:
  parent_ids: [task_123, task_124]  # Joins two branches

task_789:
  parent_ids: [task_456]
  spawn_parallel: true              # Creates multiple children
```

### Streaming Output

`session.txt` captures real-time progress:

```
[2024-01-15T10:00:00Z] Task started: debug-failing-test
[2024-01-15T10:00:01Z] Loading test file: tests/auth.test.js
[2024-01-15T10:00:02Z] Error identified: Missing mock for auth service
[2024-01-15T10:00:03Z] Searching for auth service implementation...
[2024-01-15T10:00:05Z] Applying fix to line 45
[2024-01-15T10:00:06Z] Running verification test...
[2024-01-15T10:00:08Z] Test passed! Generating report...
```

### Recovery & Resumption

Failed or interrupted tasks can be resumed:

```bash
# Original task fails
logs/session_123/task_456/
  metadata.yml: {status: failed, error: "Module not found"}

# Resume with same model
context resume session_123/task_456

# Escalate to stronger model
context resume session_123/task_456 --model=claude-3-opus

# Fork for parallel exploration
context fork session_123/task_456 --approach=alternative
```

### Model Escalation

```yaml
# Automatic escalation on failure
escalation:
  enabled: true
  chain:
    - claude-3-haiku      # Fast, cheap first attempt
    - claude-3-5-sonnet   # Standard model
    - claude-3-opus       # Complex problems
    - human              # Manual intervention
```

---

## Part III: Implementation Guidelines

### Minimal Requirements (MUST)

1. **Reference System**: Deterministic concept loading
2. **Frontmatter Support**: YAML metadata in markdown files
3. **Session Persistence**: logs/{session_id}/{task_id}/ structure
4. **Task Metadata**: Parent tracking for DAG construction

### Recommended Conventions (SHOULD)

```
context/
├── concepts/           # Atomic knowledge
│   ├── architecture.md
│   ├── testing.md
│   └── domain/
│       └── users.md
├── agents/            # Actor definitions
│   ├── debugger.yml
│   └── reviewer.yml
├── commands/          # Operations
│   └── test-commands.yml
├── workflows/         # Compositions
│   └── ci-workflow.yml
└── projects/         # Transformations
    └── current/
        └── refactor.md
```

### File Naming Standards

Use these canonical names when applicable:

**Universal Concepts:**

- `structure.md` - Codebase organization
- `architecture.md` - System design
- `testing.md` - Test strategy
- `conventions.md` - Coding standards
- `environment.md` - Dev/prod setup

**Not:**

- ~~`folder-map.md`~~
- ~~`test-guide.md`~~
- ~~`code-style.md`~~

### Progressive Adoption

#### Stage 1: Basic Context (Manual)

```
context/
├── README.md
├── setup.md
└── architecture.md
```

#### Stage 2: Structured Context (Semi-automated)

```
context/
├── concepts/
│   └── *.md
├── agents/
│   └── *.yml
└── commands/
    └── *.yml
```

#### Stage 3: Full Framework (Automated)

```
context/
├── [full structure]
logs/
├── [session tracking]
.context/
└── config.yml
```

### Tool Integration

Tools can build on this framework:

```yaml
# .context/config.yml
version: "1.0"
execution:
  track_sessions: true
  persist_artifacts: true
  enable_recovery: true

observability:
  ui: true
  port: 8080

models:
  available:
    - claude-3-5-sonnet
    - gpt-4
    - llama-70b
```

---

## Appendix A: Schemas

### Concept Schema

```yaml
name: string (required)
type: concept
references: [string]
deprecated: boolean
```

### Agent Schema

```yaml
name: string (required)
type: agent
inherits: string
concepts: [string]
capabilities: [string]
tools: [string]
```

### Command Schema

```yaml
name: string (required)
type: command
agent: string (required)
inputs: map
additional_concepts: [string]
outputs: map
timeout: duration
```

### Task Metadata Schema

```yaml
task_id: string
parent_ids: [string]
command: string
agent: string
model: string
status: enum[pending, running, completed, failed]
started_at: timestamp
completed_at: timestamp
context_loaded: [string]
inputs: map
outputs: map
error: string
```

---

## Appendix B: Example Implementation

### Simple Test Debugging Session

```bash
# Initialize context
$ context init
Created context/ structure

# Start session
$ context session start --project=fix-tests
Session started: session_2024_01_15_001

# Execute command
$ context run debug-failing-test --test=auth.test.js
Task started: task_001
Loading concepts: [testing, debugging, auth]
Debugging test...
✓ Fixed: Missing mock in auth.test.js
Report saved: logs/session_2024_01_15_001/task_001/report.md

# View DAG
$ context dag show
session_2024_01_15_001
└── task_001 [completed] debug-failing-test
```

### Parallel Refactoring

```bash
# Start parallel refactor
$ context run refactor-to-typescript --parallel=src/**/*.js
Created 47 parallel tasks...

# Monitor progress
$ context dag watch
session_xyz
├── task_001 [completed] analyze-dependencies
└── parallel-group-001
    ├── task_002 [completed] convert-src/index.js
    ├── task_003 [running] convert-src/auth/login.js
    ├── task_004 [failed] convert-src/api/client.js
    └── ... 43 more

# Resume failed task with stronger model
$ context resume task_004 --model=claude-3-opus
Resuming with enhanced model...
✓ Fixed: Complex type inference resolved
```

---

## Conclusion

This framework provides the foundation for a new paradigm in software development where:

1. **Context is structured** for optimal AI consumption
2. **Execution is observable** and debuggable
3. **Failures are recoverable** through session persistence
4. **Workflows are composable** through DAG orchestration
5. **Knowledge accumulates** rather than resets

It's not just about making AI coding better—it's about making AI coding **systematically improvable** through observation, iteration, and reuse.

---

*Status: RFC v1.0*
*Created: January 2024*
*Author: Framework Contributors*
