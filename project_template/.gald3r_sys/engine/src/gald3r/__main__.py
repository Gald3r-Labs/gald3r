"""Enables `python -m gald3r ...` (mirrors the `gald3r` console-script entry point)."""
from gald3r.adapters.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
