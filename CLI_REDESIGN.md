# CLI Redesign

## Commands to Keep (Working)

### Core Workflow
- `ctx init` - Initialize project structure
- `ctx launch <description>` - Launch task with focused context
  - `--concepts/-c` - Comma-separated concepts to load
  - `--bg/-b` - Run in background
  - `--context` - Additional context
- `ctx tasks` - List recent tasks
  - `--limit/-l` - Number to show
  - `--verbose/-v` - Detailed view
- `ctx inspect <task-id>` - View task details
- `ctx resume <task-id>` - Resume a session
- `ctx fork <task-id> <description>` - Fork from existing task

### Concept Management
- `ctx concepts` - List all concepts
- `ctx concepts <name>` - Display specific concept

### Monitoring
- `ctx status` - Check running/completed tasks

### Utility
- `ctx version` - Version info

## Commands to Remove/Defer

### Removed (Not Working/Needed)
- `start` - MCP config doesn't work as intended
- `install` - Needs rethinking for Claude integration
- `launch-async` - Just use `launch --bg` instead
- `dogfood` - Too specific, not general purpose
- `dag` - Text DAG not useful, needs web version

### To Add Later

#### Session Management
- `ctx sessions` - List all sessions with status
- `ctx kill <task-id>` - Stop a running background task
- `ctx clean` - Clean up old logs/sessions

#### Concept Tools
- `ctx concept new <name>` - Create concept from template
- `ctx concept graph` - Show concept dependency graph
- `ctx concept validate` - Check references are valid

#### Export/Import
- `ctx export <task-id>` - Export task for sharing
- `ctx import <file>` - Import task/concept bundle

#### Analytics
- `ctx stats` - Usage statistics
- `ctx dag --web` - Web-based DAG viewer

## Design Principles

1. **Verb-Noun Pattern**: `ctx <verb> <noun>` for clarity
2. **Progressive Disclosure**: Basic commands simple, advanced via flags
3. **Contextual Help**: Commands show what to do next
4. **Partial Matching**: Task IDs can be partial (first 4+ chars)
5. **Smart Defaults**: Most commands work with minimal input

## Example Workflow

```bash
# Initialize
ctx init

# Create concepts
echo "# Auth system docs" > context/concepts/auth.md

# Launch task
ctx launch "Fix OAuth bug" --concepts auth,debugging

# Check status
ctx tasks
ctx inspect 8f3d

# Fork if needed
ctx fork 8f3d "Try different approach"

# Resume later
ctx resume 8f3d
```