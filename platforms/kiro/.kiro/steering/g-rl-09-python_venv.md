---
description: 'UV package manager and virtual environment standards for Python projects'
globs:
  - '**/*.py'
  - '**/requirements.txt'
  - '**/pyproject.toml'
alwaysApply: false
subsystem_memberships: [PLATFORM_INTEGRATION]
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

## `gald3r` CLI Invocations (BUG-591)

**This mandate covers the `gald3r` CLI binary itself, not just Python scripts.** In a
`gald3r_core` dev checkout (this repo, or any worktree of it), always invoke the CLI as
**`uv run gald3r <verb>`**, never bare `gald3r <verb>`.

A bare `gald3r` call resolves whatever the OS finds first on `PATH` — which can be a stale,
globally-installed build that silently shadows this checkout's own dev source. Confirmed live
damage from exactly this shadowing (BUG-591): `gald3r decision list` returning "invalid choice"
against a build missing whole verb groups; `gald3r db backfill` silently ingesting far fewer
records than the dev checkout; and a worktree-isolated agent's own `gald3r bug update`/
`gald3r task update` call resolving PAST its own `.gald3r/` and writing into the MAIN checkout's
`.gald3r/BUGS.md` instead — defeating worktree isolation entirely. None of these failures raise an
error; they just quietly produce wrong results. `uv run gald3r <verb>` always resolves and runs
this checkout's own source, regardless of what else is on `PATH`.

This applies to every `gald3r` invocation an agent makes directly (task/bug/worktree/housekeep/
search/validate verbs, etc.), including inside the `g-go`/`g-go-code`/`g-go-code-swarm`/
`g-go-review`/`g-go-go` pipeline commands — see those command files' "CLI Invocation Rule
(BUG-591)" section for the pipeline-specific wiring, including a machine-actionable staleness
hard-fail check a coordinator may run before a swarm dispatch.

### Windows dual-exe contract: `gald3r.exe` vs `gald3rw.exe` (T607, resolves BUG-650)

The Windows release ships **two** compiled executables on `PATH`:

| Binary | PE subsystem | Use it for |
|---|---|---|
| `gald3r.exe` | Console (3), `--windows-console-mode=force` | Terminals, scripts, scheduled tasks, AI-agent shells — always waits, always prints, always returns a real exit code, including from a console-less PowerShell host. **This is the one to invoke from an agent shell or automation script.** |
| `gald3rw.exe` | GUI (2), `--windows-console-mode=attach` | Throne, IDE hooks, the valk daemon, and any other spawn from a process that must never flash a console window (the BUG-556 fix). Not for interactive/scripted invocation. |

**Always invoke `gald3r`, never `gald3rw`, from a shell or automation script.** Dev
checkouts are unaffected either way: `uv run gald3r <verb>` (already mandatory above)
runs the console-subsystem Python entry point directly, not either compiled binary.

**Pre-T607 history**: before this split, only one binary existed and it was built
GUI-subsystem (`--windows-console-mode=attach`, `gald3rw.exe`'s shape today). From a
**console-less PowerShell host** — which includes many AI-agent persistent shells — a
bare `gald3r ...` call returned **instantly with no output and a blank exit code**:
PowerShell does not wait for GUI-subsystem exes and there is no console to attach, so
stdout was silently lost. **If you ever see that failure mode, you are on a stale,
pre-T607 install (or have invoked `gald3rw.exe` directly by mistake) — never interpret
it as "no matches" / "command unavailable"; it is the same false-negative class as
g-rl-43's gitignore blindness.** Update to a current release (or re-run `gald3r sync`/
`gald3r platform install` on an installed overlay) rather than working around it.

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
