---
name: testing
references: [core, python]
---

# Testing Concepts

## Philosophy

- Test behavior, not implementation
- Write tests that tell a story
- Each test should have a clear purpose

## Framework

- pytest as primary test framework
- Mock for external dependencies
- Fixtures for test data setup
- Coverage targets: 80%+ for core logic

## Commands

- Run all tests: `pytest`
- Run specific: `pytest path/to/test.py`
- With coverage: `pytest --cov`
- Watch mode: `pytest-watch`

## Test Organization

- Unit tests in tests/unit/
- Integration tests in tests/integration/
- E2E tests validate full task flows

## Patterns

- Use descriptive test names
- Arrange-Act-Assert pattern
- Mock external dependencies
- Test edge cases and error paths
- Parameterized tests for variants
- Async test support with pytest-asyncio
- Snapshot testing for DAG outputs
