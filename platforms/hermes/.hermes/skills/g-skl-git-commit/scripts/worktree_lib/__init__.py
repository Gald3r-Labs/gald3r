"""worktree_lib — decomposed implementation of the gald3r worktree helper.

Python port of gald3r_worktree.ps1 (T1585). Modules:

    gitio      — git/process IO, paths, time, atomic writes (engine-utils aware)
    manifest   — worktree root resolution + .gald3r-worktree.json ownership IO
    actions    — Create / Remove / Cleanup / Keep / MergeToMain
    agents     — Run / Cancel / CancelAll (T1123)
    continuity — Checkpoint / Resume / Steer / Queue (T967, T969)
    locks      — swarm file-lock manifests + LockReport (T1059)

The CLI entry point is the sibling ``gald3r_worktree.py``.
"""
# @subsystems: AGENT_ORCHESTRATION

__all__ = ["actions", "agents", "continuity", "gitio", "locks", "manifest"]
