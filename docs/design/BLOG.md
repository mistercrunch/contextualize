# Contextualize

**Active Context Engineering for AI Coding Agents**

## The Problem

Every AI coding assistant today suffers from the same fundamental limitation: **context window overflow**. We dump entire codebases into Claude, ChatGPT, or Cursor, hoping the model can somehow navigate thousands of files and millions of tokens to understand what we need. The result? Confused agents, hallucinated imports, and forgotten requirements.

Meanwhile, each tool invents its own context format - `CLAUDE.md`, `CURSOR.md`, `.aider.conf.yml` - fragmenting the ecosystem and forcing developers to maintain multiple representations of the same knowledge.

## The Solution

**Contextualize** is an active context engineering framework that treats context not as a massive dump of information, but as a carefully orchestrated network of focused, reusable concepts. Built on top of Claude Code, it enables:

### 🎯 **Targeted Context Injection**

Launch tasks with *only* the concepts they need. No more flooding the context window with irrelevant code.

### 🔀 **Multi-Session Orchestration**

Every substantial task gets its own Claude session with its own focused context. Work on multiple features in parallel without context pollution.

### 🔍 **Full Observability**

Track every task, its inputs, outputs, and relationships in a visual DAG. Know exactly what your AI agents are doing and why.

### ⏮️ **Session Time Travel**

Resume any session exactly where it left off. Fork from failure points. Your AI's work becomes truly persistent and debuggable.

### 🦘 **Session Hopping**

Jump between related tasks, carrying forward learned context. Build a living knowledge graph as you work.

## How It Works

Instead of this:

```bash
# Traditional approach - dump everything
claude "Help me fix the auth bug" --context ./src/**/*.ts
# Claude: *drowns in 10,000 files*
```

Contextualize enables this:

```bash
# Targeted, focused context
ctx launch-async \
  --desc "Fix OAuth token refresh bug" \
  --concepts "auth,oauth,debugging"
# Claude: *gets exactly what it needs*
```

Each task runs in isolation with:

- **Minimal context** from curated concept files
- **Full logging** of inputs and outputs
- **Session persistence** via unique IDs
- **Fork capability** when things go wrong
- **DAG tracking** to visualize task relationships

## The Philosophy

> "Context is everything, but everything is not context."

We believe AI agents work best not as generalists drowning in information, but as specialists equipped with precisely the knowledge they need. Contextualize makes this possible by treating context as a **self-referencing network of concepts** rather than a linear document.

This isn't just another tool wrapper - it's a fundamental rethinking of how we structure knowledge for AI consumption. By embracing active context engineering, we enable AI agents to work with the focus of domain experts rather than the confusion of information overload.

---

> **Note:** For the original philosophical essay on context engineering, see [PHILOSOPHY.md](PHILOSOPHY.md). For the detailed framework design, see [FRAMEWORK.md](FRAMEWORK.md).

## On the Nature of Context

**Context is knowledge that enables understanding.**

The word itself comes from Latin *contexere*—"to weave together." Just as threads gain meaning through their weaving, information becomes context through its connections.

### Context is Everything

In any complex system, context is the invisible substrate that makes understanding possible. It's not just information—it's the relationships between information, the history that shaped it, the constraints that bound it, and the intentions that drive it.

Context is:

- **Applicable knowledge**: Information becomes context when it can be applied to understand or change something
- **Multi-dimensional**: The same information serves different purposes from different perspectives
- **Self-referential**: Context contains meta-context—information about how to interpret information
- **Emergent**: The whole exceeds its parts; context creates meaning through interaction

### What is Code?

Code is context crystallized.

It's the most extreme form of context—so practical, so specific, so materialized that it can be executed. Code is:

- **Context at its densest**: Every line embodies decisions, constraints, and intentions
- **Point-in-time truth**: A snapshot of understanding made runnable
- **Self-verifying context**: It either works or it doesn't

But code is also incomplete context. It shows the **what** and **how** but rarely the **why**. It's context optimized for machines, stripped of the narrative that makes it intelligible to humans.

### The Context Spectrum

Context exists on a spectrum of abstraction and locality:

```
Philosophy → Architecture → Design → Code → Comments → Variable names
    ↑                                                                ↓
Abstract, general, stable                    Concrete, specific, volatile
```

**Comments** are micro-context—the most localized form of human-readable context. They live at the boundary between human and machine understanding:

- **Inline comments**: Context at its most granular, explaining the non-obvious
- **Block comments**: Regional context, explaining local complexity
- **Doc comments**: Interface context, explaining contracts and usage

Comments are context that couldn't be expressed in code. They're admissions that code alone isn't sufficient context.

### The Paradox of Context

Context is simultaneously:

- Universal (everyone needs it) yet particular (everyone needs different parts)
- Implicit (assumed knowledge) yet explicit (must be communicated)
- Stable (conventions persist) yet dynamic (understanding evolves)
- Structured (follows patterns) yet organic (resists rigid classification)

## Why Context Demands Organization

### The Cost of Chaos

Without organization, context:

- **Decays**: Knowledge erodes with time and team changes
- **Fragments**: Understanding splits across minds, documents, and tools
- **Repeats**: The same questions get answered again and again
- **Diverges**: Multiple truths emerge about the same reality

### The Power of Structure

Organized context:

- **Accumulates**: Knowledge builds rather than resets
- **Transfers**: Understanding moves between people and tools
- **Scales**: Complexity becomes navigable
- **Converges**: Shared mental models emerge

## The Seven Dimensions of Context

Context organizes along multiple axes—some fundamental to human cognition, others emerging from the realities of collaboration and tooling.

### Primary Dimensions (Universal)

These three dimensions reflect how humans naturally organize knowledge:

#### 1. Subject Dimension (Perspectives)

Context through the lens of different disciplines and roles.

Each perspective asks different questions about the same system:

- **Architecture**: How is it structured? What are the boundaries?
- **Engineering**: How does it work? What are the patterns?
- **Product**: What problems does it solve? For whom?
- **Design**: How do users experience it? What mental models exist?
- **Operations**: How does it run? What can break?

This is context organized by *who needs to know*.

#### 2. Task Dimension (Capabilities)

Context organized by what needs to be accomplished.

Knowledge clustered around action:

- **Setup**: What's needed to begin?
- **Development**: How to build and test?
- **Debugging**: How to diagnose and fix?
- **Deployment**: How to ship and monitor?
- **Maintenance**: How to evolve and refactor?

This is context organized by *what needs to be done*.

#### 3. Outcome Dimension (Artifacts)

Context organized around deliverables and their histories.

The specifications, decisions, and learnings that produced results:

- **Features**: What was built and why?
- **Decisions**: What trade-offs were made?
- **Experiments**: What was tried and learned?
- **Migrations**: How did we get from there to here?

This is context organized by *what was achieved*.

### Secondary Dimensions (Emergent)

These dimensions arise from the mechanics of software development and collaboration:

#### 4. Temporal Dimension (When)

Context across time and change.

- **Versioning**: How did we get here?
- **Lifecycle**: Where are we in the journey?
- **Migrations**: How do we move forward?
- **Deprecations**: What's being phased out?

This is context organized by *when it matters*.

#### 5. Scope Dimension (Where)

Context boundaries and hierarchies.

- **Local vs Global**: Project-specific or universal?
- **Module boundaries**: Which subsystem owns this?
- **Environment specific**: Dev, staging, or production?
- **Inheritance chains**: What overrides what?

This is context organized by *where it applies*.

#### 6. Authority Dimension (Trust)

Context about permissions and ownership.

- **Access control**: Who can see or change this?
- **Source of truth**: Which version is canonical?
- **Ownership**: Who maintains this knowledge?
- **Confidence levels**: How certain are we?

This is context organized by *who decides*.

#### 7. Interaction Dimension (Protocol)

Context about how systems and tools engage.

- **Tool protocols**: How does each tool consume this?
- **Integration patterns**: Webhooks, APIs, events?
- **Format preferences**: Structured vs narrative?
- **Agent personalities**: Specialized behaviors and prompts?

This is context organized by *how to engage*.

## The Duplication Paradox

In a seven-dimensional space, the same piece of information naturally appears in multiple locations. This isn't inefficiency—it's perspective.

Consider a simple test command `npm test`:

- Appears in `operations/commands.yaml` (task dimension)
- Documented in `development/testing.md` (subject dimension)
- Referenced in `projects/feature-x/spec.md` (outcome dimension)
- Configured in `.claude/agents/test-runner.md` (interaction dimension)
- Versioned in `history/v2-migration.md` (temporal dimension)

Each appearance serves a different cognitive need. The duplication is the point—context gains meaning through repetition across dimensions.

## The Interplay

The magic happens at the intersections:

- A **task** viewed through different **perspectives** reveals complexity
- An **outcome** changes across **time** showing evolution
- A **scope** defines **authority** establishing boundaries
- An **interaction** protocol varies by **scope** and **subject**

Real understanding emerges from navigating these intersections. A testing strategy (task) viewed through architecture (perspective) with production scope (where) requiring approval (authority) executed by CI agents (interaction) that evolved over versions (temporal) producing a test framework (outcome).

The seven dimensions create a rich context space where knowledge lives in multiple places, each optimized for different ways of thinking and working.

## The Fundamental Tension

### Structure vs. Emergence

Too much structure and context becomes:

- Rigid, unable to adapt
- Burdensome to maintain
- Disconnected from reality

Too little structure and context becomes:

- Chaotic, impossible to navigate
- Inconsistent across sources
- Lost in noise

The art lies in finding the minimum viable structure that enables maximum understanding.

## Principles for Context Engineering

1. **Embrace multiplicity**: The same truth lives in many places, each serving different needs
2. **Segment, don't centralize**: Distribute context across focused, findable locations
3. **Layer, don't choose**: Support both human narrative and machine parsing
4. **Preserve, don't discard**: Today's implementation detail is tomorrow's crucial history
5. **Connect, don't isolate**: Context gains meaning through relationships
6. **Evolve, don't redesign**: Systems that grow beat systems that restart
7. **Optimize for discovery**: Make the right context findable at the right moment

## Existing Patterns in the Wild

The seven dimensions already exist, scattered across tools:

**`.claude/agents/`** - Interaction dimension personified. Each agent is a specialized lens for viewing and manipulating context.

**`.continue/config.yaml`** - Tool-specific interaction protocols, defining how AI engages with code.

**`.devcontainer/`** - Scope and environment dimension. Defines boundaries of development contexts.

**`CODEOWNERS`** - Pure authority dimension. Who decides what.

**`.cursorrules`** - Subject-specific guidance for an interaction protocol.

**`migrations/`** folders - Temporal dimension made explicit.

**`docs/ADR/`** (Architecture Decision Records) - Outcome dimension preserving the why behind what was built.

These patterns emerged independently because the dimensions are fundamental. The framework simply names what already exists.

## From Philosophy to Practice

### The Universal Structure

When you begin segmenting context, start with this foundation:

```
CONTEXT/
├── README.md           # Entry point, maps to other dimensions
├── OVERVIEW.md         # What this is and why it exists
├── setup.md            # How to get started (Task dimension)
├── architecture.md     # How it's structured (Subject dimension)
└── commands.yaml       # Deterministic operations (structured data)
```

### Mapping Dimensions to Directories

As your project grows, dimensions naturally map to folder structures:

#### Primary Dimensions → Core Folders

```
CONTEXT/
├── perspectives/       # Subject dimension
│   ├── engineering.md
│   ├── product.md
│   ├── design.md
│   └── operations.md
├── tasks/             # Task dimension
│   ├── setup.md
│   ├── testing.md
│   ├── debugging.md
│   └── deployment.md
└── outcomes/          # Outcome dimension
    ├── decisions/
    ├── features/
    └── migrations/
```

#### Secondary Dimensions → Cross-Cutting Organization

```
CONTEXT/
├── .claude/           # Interaction dimension
│   └── agents/
├── environments/      # Scope dimension
│   ├── local.md
│   ├── staging.md
│   └── production.md
├── history/           # Temporal dimension
│   ├── ARCHIVE/
│   └── changelog.md
└── permissions/       # Authority dimension
    └── CODEOWNERS
```

### Must-Have Files by Project Lifecycle

#### Early Stage (Exploration)

Start minimal:

- `OVERVIEW.md` - What are we building?
- `setup.md` - How to get started
- `architecture.md` - Initial design decisions

#### Active Development

Add task-oriented context:

- `tasks/testing.md` - Test strategy and commands
- `tasks/debugging.md` - Common issues and solutions
- `perspectives/engineering.md` - Coding conventions

#### Production

Add operational context:

- `operations/deployment.md` - Ship process
- `environments/*.md` - Environment-specific configs
- `operations/monitoring.md` - What to watch

#### Maintenance

Preserve history:

- `history/ARCHIVE/` - Completed project specs
- `outcomes/decisions/` - ADRs and trade-offs
- `outcomes/migrations/` - How we evolved

### The Naming Principle

Use these standard names when the concept applies:

**Universal files** (always relevant):

- `README.md` - Navigation and overview
- `setup.md` - Getting started
- `commands.yaml` - Executable operations

**Common patterns** (use when applicable):

- `testing.md` not "test-guide.md"
- `deployment.md` not "deploy-process.md"
- `architecture.md` not "system-design.md"
- `conventions.md` not "code-style.md"

The goal: A developer moving between projects finds familiar structure.

### Progressive Enhancement

Start with flat files:

```
CONTEXT/
├── README.md
├── setup.md
└── testing.md
```

Evolve to folders as complexity grows:

```
CONTEXT/
├── README.md
├── tasks/
│   ├── setup.md
│   └── testing.md
└── perspectives/
    └── architecture.md
```

Eventually reach full dimensionality:

```
CONTEXT/
├── [7 dimension folders]
└── [cross-references via links]
```

### The Anti-Pattern

Don't create empty structure. Every file should answer a real question someone has asked. Empty folders are broken promises.

## The Vision

Context engineering is the discipline of making implicit knowledge explicit, scattered knowledge organized, and tribal knowledge universal.

It's not about creating more documentation. It's about creating the right knowledge, in the right place, at the right time, for the right audience—human or machine.

When context is engineered well:

- Questions have homes
- Knowledge has structure
- Understanding has paths
- Systems become learnable

This is the future we're building: codebases that explain themselves, to everyone who asks.

---

*This manifesto defines the philosophical foundation. Implementation follows philosophy.*
