---
description: 'UV package manager and virtual environment standards for Python projects'
globs:
  - '**/*.py'
  - '**/requirements.txt'
  - '**/pyproject.toml'
alwaysApply: false
---

# Python Virtual Environment (UV)

**CRITICAL**: Use UV, never `pip install` or `python -m venv` directly.

## Core Commands
```bash
uv venv                           # Create .venv/
uv pip install <package>          # Install
uv pip install -r requirements.txt
uv run python script.py           # Run in UV env
uv pip freeze > requirements.txt  # Save packages

# Activate (Windows)
.venv\Scripts\activate
# Activate (Unix/Mac)
source .venv/bin/activate
```

## Dependency Sync (MANDATORY)
`requirements.txt` AND `pyproject.toml` must ALWAYS match.
When adding a package: install → freeze → update pyproject.toml → commit both.

```toml
[project]
dependencies = ["package==version"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Code Standards
- Line length: 88-100 chars (black)
- Type hints on all new public functions
- Docstrings: Google style
- No bare `except:` — always catch specific exceptions
