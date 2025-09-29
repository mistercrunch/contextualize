---
name: core
references: []
---

# Contextualize - Core Principles

## Project Vision
A universal framework for managing AI agent context that enables task isolation, observability, resumability, and forking. The system treats context as a self-referencing network of concepts with tasks as the observable foundation.

## Core Principles

### 1. Context as Network
Context is not linear documentation but a self-referencing network of interconnected concepts. Each concept can reference others, creating a rich knowledge graph.

### 2. Task-Based Execution
Every substantial piece of work is a tracked task with:
- Isolated context loading (minimal necessary concepts)
- Full input/output logging
- Session persistence via IDs
- Fork capability from any point

### 3. Observability First
All agent work is observable through:
- DAG visualization of task relationships
- Complete audit trail of inputs/outputs
- Session resumability
- Context evolution tracking

### 4. Minimal Context Loading
Tasks load only necessary concepts, not entire codebases. This enables:
- Faster task execution
- Clearer agent focus
- Better token efficiency
- Reduced hallucination

### 5. Dogfooding Philosophy
The framework builds itself using its own tools. Every feature addition is a managed task, proving the system's value through usage.

## Architecture

### MCP Server Layer
- Provides tools to Claude Code
- Manages task lifecycle
- Handles context loading
- Tracks DAG relationships

### CLI Layer
- `ctx` command for management
- Rich terminal UI
- Task monitoring
- DAG visualization

### Storage Layer
- Filesystem-based persistence
- JSONL for DAG tracking
- Concept markdown files
- Task input/output logs

## Key Concepts

### Tasks
Isolated units of work with:
- Unique IDs
- Parent relationships
- Concept dependencies
- Session persistence

### Concepts
Reusable knowledge modules:
- Markdown with frontmatter
- Reference tracking
- Domain-specific knowledge
- Framework patterns

### Sessions
Resumable Claude instances:
- `claude --session-id {id}`
- Fork capability
- State preservation
- Context inheritance

## Usage Patterns

### 1. Task Launch
```
launch_task(
  description="Implement feature X",
  concepts=["python", "testing"],
  context_from_main="User requirements..."
)
```

### 2. Task Fork
```
fork_task(
  parent_id="abc123",
  description="Fix issue found in parent",
  additional_concepts=["debugging"]
)
```

### 3. Task Completion
```
complete_task(
  summary="Implemented feature with tests",
  context_learned=["New pattern discovered"],
  artifacts=["src/feature.py", "tests/test_feature.py"]
)
```

## Benefits

1. **Reduced Context Pollution**: Agents work with minimal, focused context
2. **Better Debugging**: Full observability of what went wrong and where
3. **Resumability**: Pick up exactly where you left off
4. **Parallel Work**: Multiple isolated tasks can run simultaneously
5. **Knowledge Evolution**: Concepts grow through discovered patterns

## Philosophy

> "Context is everything, but everything is not context"

The framework embraces the paradox that while context enables all understanding, loading everything as context destroys understanding. By treating context as a carefully curated network of concepts, we enable AI agents to work with the precision of domain experts rather than the confusion of generalists.

## Implementation Status

### Completed ✅
- Basic MCP server structure
- CLI with rich/typer
- Concept organization
- Task logging
- DAG tracking

### In Progress 🔄
- Full Claude integration
- Async task execution
- Context loading from files
- Fork capability
- Web-based DAG viewer

### Planned 📝
- Concept auto-discovery
- Task templates
- Performance metrics
- Multi-agent coordination
- Cloud persistence