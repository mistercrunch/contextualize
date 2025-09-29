"""
Concept data models for Contextualize
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Concept:
    """Individual concept representation"""

    # Core properties
    name: str
    content: str
    references: List[str] = field(default_factory=list)

    # File reference
    file_path: Optional[Path] = None

    @classmethod
    def from_file(cls, file_path: Path) -> Optional["Concept"]:
        """Load concept from markdown file"""
        if not file_path.exists():
            return None

        content = file_path.read_text()

        # Parse frontmatter
        name = file_path.stem
        references = []

        # Simple frontmatter parsing
        lines = content.split("\n")
        if len(lines) > 2 and lines[0] == "---":
            for i, line in enumerate(lines[1:], 1):
                if line == "---":
                    # Found end of frontmatter
                    content = "\n".join(lines[i + 1 :])
                    break
                elif line.startswith("name:"):
                    name = line.replace("name:", "").strip()
                elif line.startswith("references:"):
                    refs_str = line.replace("references:", "").strip()
                    if refs_str and refs_str != "[]":
                        # Parse reference list
                        refs_str = refs_str.strip("[]")
                        references = [r.strip() for r in refs_str.split(",")]

        return cls(name=name, content=content, references=references, file_path=file_path)

    def save(self, file_path: Optional[Path] = None):
        """Save concept to markdown file"""
        if file_path:
            self.file_path = file_path
        if not self.file_path:
            raise ValueError("No file path specified")

        # Build frontmatter
        refs_str = f"[{', '.join(self.references)}]" if self.references else "[]"

        full_content = f"""---
name: {self.name}
references: {refs_str}
---

{self.content}"""

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(full_content)

    def get_size(self) -> int:
        """Get content size in characters"""
        return len(self.content)

    def get_referenced_by(self, concepts: Dict[str, "Concept"]) -> List[str]:
        """Get list of concepts that reference this one"""
        referenced_by = []
        for other_name, other_concept in concepts.items():
            if self.name in other_concept.references:
                referenced_by.append(other_name)
        return referenced_by

    def validate_references(self, concepts: Dict[str, "Concept"]) -> List[str]:
        """Validate that all references exist, return missing ones"""
        missing = []
        for ref in self.references:
            if ref not in concepts:
                missing.append(ref)
        return missing

    def remove(self):
        """Remove concept file"""
        if self.file_path and self.file_path.exists():
            self.file_path.unlink()


class ConceptCollection:
    """Collection of concepts with management methods"""

    def __init__(self, concepts_dir: Path = Path("context/concepts")):
        self.concepts_dir = concepts_dir
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self._concepts: Dict[str, Concept] = {}
        self._loaded = False

    @classmethod
    def from_path(cls, path: Path) -> "ConceptCollection":
        """Create ConceptCollection from a specific path"""
        return cls(concepts_dir=path)

    def load(self, force_reload: bool = False) -> Dict[str, Concept]:
        """Load all concepts from filesystem"""
        if self._loaded and not force_reload:
            return self._concepts

        self._concepts = {}

        if not self.concepts_dir.exists():
            self._loaded = True
            return self._concepts

        # Load from markdown files
        for concept_file in self.concepts_dir.glob("*.md"):
            concept = Concept.from_file(concept_file)
            if concept:
                self._concepts[concept.name] = concept

        self._loaded = True
        return self._concepts

    def get(self, name: str) -> Optional[Concept]:
        """Get concept by name"""
        self.load()
        return self._concepts.get(name)

    def list(self) -> List[Concept]:
        """List all concepts"""
        self.load()
        return list(self._concepts.values())

    def add(self, concept: Concept) -> Concept:
        """Add new concept to collection"""
        # Save to filesystem
        file_path = self.concepts_dir / f"{concept.name}.md"
        concept.save(file_path)

        # Add to memory
        self._concepts[concept.name] = concept

        return concept

    def remove(self, name: str) -> bool:
        """Remove concept by name"""
        concept = self.get(name)
        if not concept:
            return False

        # Remove from filesystem
        concept.remove()

        # Remove from memory
        if name in self._concepts:
            del self._concepts[name]

        return True

    def create(self, name: str, references: List[str] = None) -> Concept:
        """Create a new concept with template"""
        references = references or []

        template_content = f"""# {name.title()} Concepts

## Overview
[Add overview here]

## Key Points
- [Add key points]

## Examples
[Add examples if applicable]
"""

        concept = Concept(name=name, content=template_content, references=references)

        return self.add(concept)

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get concept dependency graph"""
        self.load()

        graph = {}
        for name, concept in self._concepts.items():
            graph[name] = concept.references

        return graph

    def get_referenced_by(self, name: str) -> List[str]:
        """Get concepts that reference a specific concept"""
        concept = self.get(name)
        if not concept:
            return []

        return concept.get_referenced_by(self._concepts)

    def validate_all_references(self) -> Dict[str, List[str]]:
        """Validate all concept references, return missing ones"""
        self.load()

        issues = {}
        for name, concept in self._concepts.items():
            missing = concept.validate_references(self._concepts)
            if missing:
                issues[name] = missing

        return issues

    def get_load_order(self) -> List[str]:
        """Get concepts in dependency order (topological sort)"""
        self.load()

        # Build dependency graph
        graph = self.get_dependency_graph()

        # Topological sort
        visited = set()
        order = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)

            # Visit dependencies first
            for dep in graph.get(name, []):
                if dep in graph:  # Only visit existing concepts
                    visit(dep)

            order.append(name)

        # Visit all concepts
        for name in graph:
            visit(name)

        return order

    def load_with_dependencies(self, concept_names: List[str]) -> str:
        """Load concepts with all their dependencies"""
        self.load()

        # Collect all needed concepts
        needed = set()
        to_process = list(concept_names)

        while to_process:
            name = to_process.pop()
            if name in needed:
                continue

            concept = self.get(name)
            if concept:
                needed.add(name)
                to_process.extend(concept.references)

        # Load in dependency order
        order = self.get_load_order()
        content = ""

        for name in order:
            if name in needed:
                concept = self.get(name)
                if concept:
                    content += f"\n## Concept: {name}\n"
                    content += concept.content
                    content += "\n" + "-" * 40 + "\n"

        return content

    def stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        self.load()

        total_size = sum(c.get_size() for c in self._concepts.values())
        ref_count = sum(len(c.references) for c in self._concepts.values())

        return {
            "total": len(self._concepts),
            "total_size": total_size,
            "avg_size": total_size // len(self._concepts) if self._concepts else 0,
            "total_references": ref_count,
            "validation_issues": len(self.validate_all_references()),
        }


# Usage example:
if __name__ == "__main__":
    # Create collection
    concepts = ConceptCollection()

    # Load all concepts
    concepts.load()

    # Create new concept
    new_concept = concepts.create("auth", references=["core", "security"])

    # Get concept
    auth = concepts.get("auth")

    # Load with dependencies
    content = concepts.load_with_dependencies(["auth", "testing"])

    # Validate references
    issues = concepts.validate_all_references()
    if issues:
        print("Reference issues:", issues)

    # Get stats
    stats = concepts.stats()
    print(f"Total concepts: {stats['total']}")
    print(f"Average size: {stats['avg_size']} chars")
