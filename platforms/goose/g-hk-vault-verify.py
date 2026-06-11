#!/usr/bin/env python3
"""Python port of g-hk-vault-verify.ps1 (T1584).

Vault existence / structure verification (T1456).

Verifies that the configured vault directory exists and carries the expected
research/ subdirectory layout, then emits a single status line:
  Vault at {path}: OK | NOT FOUND | PARTIAL (missing: ...)

Fail-soft by design: never throws, never blocks session start. When the
vault is not configured (vault_location absent or {LOCAL}) it prints
nothing.

Two ways to use it:
  1. Import it from another hook, then call get_gald3r_vault_status_banner():
       spec = importlib.util.spec_from_file_location(
           "g_hk_vault_verify", hooks_dir / "g-hk-vault-verify.py")
       mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
       line = mod.get_gald3r_vault_status_banner(project_root)
  2. Run it directly: prints the status line (if any) to stdout and exits 0.
"""
# @subsystems: VAULT_AND_RESEARCH
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401


def get_gald3r_vault_status_banner(project_root: str = "") -> str:
    """Return the vault status banner line, or "" when silent/not configured."""
    try:
        root = Path(project_root) if project_root else Path.cwd()

        # Expected research/ subdirs from the canonical vault layout
        # (g-skl-vault SKILL.md).
        research_subdirs = ["articles", "github", "harvests", "papers", "platforms", "videos"]

        identity_path = root / ".gald3r" / ".identity"
        if not identity_path.exists():
            return ""

        # Read vault_location directly from .identity (the CONFIGURED value,
        # not a resolved/auto-created path) so we can detect a missing shared
        # vault.
        vault_location = ""
        for line in identity_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*vault_location\s*=\s*(.+)$", line)
            if m:
                vault_location = m.group(1).strip().strip('"').strip("'")
                break

        # Not configured, or local-only fallback: nothing to verify, stay silent.
        if not vault_location or vault_location == "{LOCAL}":
            return ""

        # NOT FOUND: configured path does not exist on disk.
        vault_path = Path(vault_location)
        if not vault_path.exists():
            return (
                f"- Vault at `{vault_location}`: NOT FOUND -- run `@g-vault init`"
                " to build the vault structure"
            )

        # Vault root exists. Check the research/ subdir layout.
        research_root = vault_path / "research"
        missing = []
        if not research_root.exists():
            missing.append("research/")
        else:
            for sub in research_subdirs:
                if not (research_root / sub).exists():
                    missing.append("research/" + sub + "/")

        if missing:
            missing_list = ", ".join(missing)
            return (
                f"- Vault at `{vault_location}`: PARTIAL (missing: {missing_list})"
                " -- run `@g-vault init` to create the missing folders"
            )

        return f"- Vault at `{vault_location}`: OK"
    except Exception:
        # Fail-soft: never surface an error, never block.
        return ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the configured vault directory exists with the expected"
            " research/ layout; prints a single status line (or nothing)."
        )
    )
    parser.parse_args(argv)
    banner = get_gald3r_vault_status_banner(str(Path.cwd()))
    if banner:
        print(banner)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail-soft: never block session start.
        sys.exit(0)
