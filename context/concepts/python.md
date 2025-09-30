---
name: python
references: [core]
---

# Python Development Concepts

## Code Style

- Use ruff for linting and formatting
- Follow PEP 8 (enforced by ruff)
- Use type hints for clarity
- Docstrings for public functions
- Meaningful variable names
- Run: `ruff check --fix` and `ruff format`

## Common Patterns

- Context managers (with statement)
- List comprehensions (when readable)
- Pathlib for file operations
- json module for serialization

## Error Handling

- Use specific exceptions
- Don't catch bare except
- Log errors appropriately
- Fail gracefully with helpful messages

## Testing

- pytest as test framework
- Mock for external dependencies
- Fixtures for test data
- Coverage targets
