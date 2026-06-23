#!/usr/bin/env python3
"""Tests for the T513 platform freshness loop — GAP A (spec_refresh) + GAP B (generate_status).

Real tests against built fixtures (a tiny self-contained repo skeleton with a
PLATFORM_REGISTRY.yaml, two PLATFORM_SPEC.md files, a PLATFORM_STATUS.md, and JSON
crawl snapshots/ledgers). No DB, no network, no migration — the host-side path.

Run from this directory::

    python test_platform_freshness_loop.py
    # or: uv run --extra dev pytest test_platform_freshness_loop.py  (if pytest present)
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make the scripts dir (parent of tests/) importable.
_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

import platform_spec_io as psio  # noqa: E402


OK, WARN, NO, UNK = psio.OK, psio.WARN, psio.NO, psio.UNK


# --------------------------------------------------------------------------- #
# Fixture builders                                                            #
# --------------------------------------------------------------------------- #
REGISTRY_YAML = """\
schema_version: 1
generated_by: test
platforms:
  - name: cursor
    display_name: Cursor
    overlay_dir: cursor
    spec_path: g-skl-platform-cursor/PLATFORM_SPEC.md
    lifecycle: active
    alias_of: null
    support_level: tier1
    notes: Reference platform.
  - name: warp
    display_name: Warp
    overlay_dir: warp
    spec_path: g-skl-platform-warp/PLATFORM_SPEC.md
    lifecycle: active
    alias_of: null
    support_level: tier2
    notes: Partial.
"""

CURSOR_SPEC = """\
---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: cursor
crawl_max_age_days: 7
last_doc_scan: 2026-06-02
status: ✅
---

# PLATFORM_SPEC.md — Cursor

## 6. Hooks System — ✅ NATIVE

Cursor supports lifecycle hooks via hooks.json.

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
"""

# Warp: Hooks ❌ in the curated spec (the disagreement target).
WARP_SPEC = """\
---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: warp
crawl_max_age_days: 14
last_doc_scan: 2026-06-02
status: ⚠️
---

# PLATFORM_SPEC.md — Warp

## 6. Hooks Support

Warp has no lifecycle hooks.

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
"""

STATUS_MD = """\
# PLATFORM_STATUS.md — Cross-Platform Capability Index

> ## BANNER — stale, regenerate.

Legend: ✅ verified · ⚠️ partial · ❌ not supported · ❓ untested.

| Platform | Status | Last Doc Scan | Hooks | Rules | Skills | Commands | MCP | Notes |
|---|---|---|---|---|---|---|---|---|
| cursor | ✅ | 2026-06-02 | ✅ | ✅ | ✅ | ✅ | ✅ | Reference platform — all six native. |
| warp | ⚠️ | 2026-06-02 | ❌ | ✅ | ✅ | ⚠️ | ✅ | Hand-curated Warp note (must survive regen). |
---

## Summary

- **Total platforms**: 2
- **Healthy (✅)**: 1

## Platform-Specific vs. Cursor-Copy

Curated trailing prose that must be preserved verbatim.
"""


def _build_repo(root: Path) -> None:
    """Lay out a minimal repo skeleton resolve_spec_path + generate_status accept."""
    reg = root / "gald3r_templates" / "gald3r_core" / "platforms"
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "PLATFORM_REGISTRY.yaml").write_text(REGISTRY_YAML, encoding="utf-8")

    skills = root / "gald3r_templates" / "gald3r_core" / "project_template" / ".claude" / "skills"
    for name, spec in (("cursor", CURSOR_SPEC), ("warp", WARP_SPEC)):
        d = skills / f"g-skl-platform-{name}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "PLATFORM_SPEC.md").write_text(spec, encoding="utf-8")

    gald3r = root / ".gald3r"
    gald3r.mkdir(parents=True, exist_ok=True)
    (gald3r / "PLATFORM_STATUS.md").write_text(STATUS_MD, encoding="utf-8")


def _import_consumers():
    """Import the consumers AFTER clearing cached registry/roster module state so
    each test's fixture registry is picked up fresh."""
    for mod in ("platform_registry", "check_platform_status",
                "spec_refresh", "generate_status"):
        sys.modules.pop(mod, None)
    psio._LEDGER = None if hasattr(psio, "_LEDGER") else None
    import platform_registry  # noqa: F401
    platform_registry._CACHE = None
    import spec_refresh
    import generate_status
    return spec_refresh, generate_status


# --------------------------------------------------------------------------- #
# platform_spec_io unit tests                                                 #
# --------------------------------------------------------------------------- #
class TestSpecIO(unittest.TestCase):
    def test_capability_cells_from_summary(self):
        cells = psio.capability_cells(CURSOR_SPEC)
        self.assertEqual(cells, {"Hooks": OK, "Rules": OK, "Skills": OK,
                                 "Commands": OK, "MCP": OK})

    def test_warp_hooks_no_from_summary(self):
        cells = psio.capability_cells(WARP_SPEC)
        self.assertEqual(cells["Hooks"], NO)
        self.assertEqual(cells["Commands"], WARN)

    def test_frontmatter_field(self):
        self.assertEqual(psio.get_frontmatter_field(CURSOR_SPEC, "last_doc_scan"),
                         "2026-06-02")
        self.assertEqual(psio.spec_threshold(WARP_SPEC), 14)

    def test_docs_fresh_cell(self):
        self.assertEqual(psio.docs_fresh_cell(None, 7), UNK)
        self.assertEqual(psio.docs_fresh_cell("never", 7), UNK)
        self.assertEqual(psio.docs_fresh_cell("1999-01-01", 7), WARN)  # very old

    def test_load_crawl_ledger_iso_to_date_and_alias(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "reg.json"
            p.write_text(json.dumps({"registry": [
                {"platform": "cursor", "last_crawled_at": "2026-06-21T08:30:00Z",
                 "pages_count": 42, "crawl_status": "success"},
                {"platform": "claude_code", "last_crawled_at": "2026-06-20",
                 "pages_count": 10, "crawl_status": "success"},
            ]}), encoding="utf-8")
            ledger = psio.load_crawl_ledger(p)
            self.assertEqual(ledger["cursor"]["last_doc_scan"], "2026-06-21")
            # claude roster id resolves to claude_code registry key.
            self.assertEqual(psio.ledger_last_doc_scan(ledger, "claude"), "2026-06-20")
            self.assertIsNone(psio.ledger_last_doc_scan(ledger, "warp"))

    def test_load_crawl_ledger_missing_returns_empty(self):
        self.assertEqual(psio.load_crawl_ledger(None), {})
        self.assertEqual(psio.load_crawl_ledger(Path("/nope/does/not/exist.json")), {})

    def test_resolve_last_doc_scan_prefers_ledger_then_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "reg.json"
            p.write_text(json.dumps({"registry": [
                {"platform": "cursor", "last_crawled_at": "2026-06-21T00:00:00Z"}]}),
                encoding="utf-8")
            ledger = psio.load_crawl_ledger(p)
            # ledger wins
            self.assertEqual(
                psio.resolve_last_doc_scan(CURSOR_SPEC, "cursor", ledger), "2026-06-21")
            # no ledger row -> frontmatter
            self.assertEqual(
                psio.resolve_last_doc_scan(WARP_SPEC, "warp", ledger), "2026-06-02")


# --------------------------------------------------------------------------- #
# GAP A — spec_refresh tests                                                  #
# --------------------------------------------------------------------------- #
class TestSpecRefresh(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _build_repo(self.root)
        self.spec_refresh, _ = _import_consumers()

    def tearDown(self):
        self._td.cleanup()

    def _snapshot(self, results):
        p = self.root / "snap.json"
        p.write_text(json.dumps({"results": results}), encoding="utf-8")
        return p

    def _ledger(self, rows):
        p = self.root / "led.json"
        p.write_text(json.dumps({"registry": rows}), encoding="utf-8")
        return p

    def test_proposal_stamps_last_doc_scan_from_ledger(self):
        snap = self._snapshot([
            {"title": "Hooks", "content": "Cursor supports lifecycle hooks in hooks.json: sessionStart, preToolUse."},
            {"title": "MCP", "content": "MCP via mcp.json."},
        ])
        led = self._ledger([{"platform": "cursor",
                             "last_crawled_at": "2026-06-21T08:30:00Z",
                             "pages_count": 42, "crawl_status": "success"}])
        out = self.root / "out"
        prop = self.spec_refresh.run("cursor", snap, led, self.root, apply=False, out_dir=out)
        self.assertFalse(prop["empty"])
        self.assertTrue(prop["last_doc_scan_changed"])
        self.assertEqual(prop["proposed_last_doc_scan"], "2026-06-21")
        # No disagreement: docs evidence Hooks ✅, spec says ✅.
        self.assertEqual(prop["needs_review"], [])
        # Proposed draft preserves curated cells and stamps the new scan date.
        self.assertIn("last_doc_scan: 2026-06-21", prop["proposed_text"])
        self.assertTrue((out / "PLATFORM_SPEC.md.proposed").exists())
        self.assertTrue((out / "PLATFORM_SPEC.md.proposal.md").exists())

    def test_disagreement_surfaces_needs_review_no_autoflip(self):
        # Warp spec says Hooks ❌; docs now evidence native hooks (a breaking change).
        snap = self._snapshot([{"title": "Hooks",
            "content": "Warp now supports lifecycle hooks: preToolUse, sessionStart events in hooks.json."}])
        out = self.root / "out"
        prop = self.spec_refresh.run("warp", snap, None, self.root, apply=False, out_dir=out)
        self.assertFalse(prop["empty"])
        caps = [r["capability"] for r in prop["needs_review"]]
        self.assertIn("Hooks", caps)
        review = next(r for r in prop["needs_review"] if r["capability"] == "Hooks")
        self.assertEqual(review["spec_cell"], NO)
        self.assertEqual(review["doc_evidence"], OK)
        # The proposed draft must NOT have flipped the curated ❌ to ✅.
        self.assertIn("| ❌ | ✅ | ✅ | ⚠️ | ✅ |", prop["proposed_text"])

    def test_empty_proposal_is_idempotent_noop(self):
        # No ledger, docs agree with the curated cursor spec, scan already current.
        snap = self._snapshot([
            {"title": "Hooks", "content": "Cursor supports hooks via hooks.json."},
            {"title": "Rules", "content": "Rules in .cursor/rules and AGENTS.md."},
            {"title": "Skills", "content": "SKILL.md agent skills."},
            {"title": "Commands", "content": "Custom slash command markdown."},
            {"title": "MCP", "content": "MCP via mcp.json."},
        ])
        prop = self.spec_refresh.run("cursor", snap, None, self.root, apply=False,
                                     out_dir=self.root / "out")
        self.assertTrue(prop["empty"])
        self.assertEqual(prop["diff"], "")

    def test_no_blind_write_without_apply(self):
        spec = (self.root / "gald3r_templates" / "gald3r_core" / "project_template"
                / ".claude" / "skills" / "g-skl-platform-cursor" / "PLATFORM_SPEC.md")
        before = spec.read_text(encoding="utf-8")
        snap = self._snapshot([{"title": "Hooks", "content": "Cursor hooks via hooks.json."}])
        led = self._ledger([{"platform": "cursor", "last_crawled_at": "2026-06-21T00:00:00Z"}])
        self.spec_refresh.run("cursor", snap, led, self.root, apply=False,
                              out_dir=self.root / "out")
        self.assertEqual(spec.read_text(encoding="utf-8"), before)  # untouched

    def test_apply_lands_only_scan_stamp(self):
        spec = (self.root / "gald3r_templates" / "gald3r_core" / "project_template"
                / ".claude" / "skills" / "g-skl-platform-cursor" / "PLATFORM_SPEC.md")
        snap = self._snapshot([{"title": "Hooks", "content": "Cursor hooks via hooks.json."}])
        led = self._ledger([{"platform": "cursor", "last_crawled_at": "2026-06-21T00:00:00Z"}])
        prop = self.spec_refresh.run("cursor", snap, led, self.root, apply=True,
                                     out_dir=self.root / "out")
        self.assertTrue(prop["applied"])
        after = spec.read_text(encoding="utf-8")
        self.assertIn("last_doc_scan: 2026-06-21", after)
        # Capability cells unchanged by --apply.
        self.assertIn("| ✅ | ✅ | ✅ | ✅ | ✅ |", after)


# --------------------------------------------------------------------------- #
# GAP B — generate_status tests                                               #
# --------------------------------------------------------------------------- #
class TestGenerateStatus(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _build_repo(self.root)
        _, self.generate_status = _import_consumers()

    def tearDown(self):
        self._td.cleanup()

    def _status_path(self):
        return self.root / ".gald3r" / "PLATFORM_STATUS.md"

    def test_regen_preserves_status_verdict_and_notes(self):
        rep = self.generate_status.run(self.root, None, apply=True, timestamp=False)
        text = self._status_path().read_text(encoding="utf-8")
        # curated Notes survive
        self.assertIn("Hand-curated Warp note (must survive regen).", text)
        self.assertIn("Reference platform — all six native.", text)
        # curated Status verdict preserved (warp ⚠️)
        warp_row = next(l for l in text.splitlines() if l.startswith("| warp "))
        self.assertEqual(warp_row.strip("|").split("|")[1].strip(), WARN)
        # curated trailing prose preserved
        self.assertIn("Curated trailing prose that must be preserved verbatim.", text)

    def test_capability_cells_match_spec(self):
        self.generate_status.run(self.root, None, apply=True, timestamp=False)
        text = self._status_path().read_text(encoding="utf-8")
        warp_row = next(l for l in text.splitlines() if l.startswith("| warp "))
        cells = [c.strip() for c in warp_row.strip("|").split("|")]
        # Platform | Status | LastDocScan | Hooks | Rules | Skills | Commands | MCP | Notes
        self.assertEqual(cells[3], NO)    # Hooks (from spec ## Capability Summary)
        self.assertEqual(cells[6], WARN)  # Commands

    def test_last_doc_scan_from_ledger_not_now(self):
        led = self.root / "led.json"
        led.write_text(json.dumps({"registry": [
            {"platform": "cursor", "last_crawled_at": "2026-06-21T00:00:00Z"}]}),
            encoding="utf-8")
        self.generate_status.run(self.root, led, apply=True, timestamp=False)
        text = self._status_path().read_text(encoding="utf-8")
        cursor_row = next(l for l in text.splitlines() if l.startswith("| cursor "))
        cells = [c.strip() for c in cursor_row.strip("|").split("|")]
        self.assertEqual(cells[2], "2026-06-21")  # ledger date, not "now"
        # warp has no ledger row -> falls back to spec frontmatter
        warp_row = next(l for l in text.splitlines() if l.startswith("| warp "))
        wcells = [c.strip() for c in warp_row.strip("|").split("|")]
        self.assertEqual(wcells[2], "2026-06-02")

    def test_idempotent_modulo_timestamp(self):
        # apply once (no timestamp), capture; apply again; must be byte-identical.
        self.generate_status.run(self.root, None, apply=True, timestamp=False)
        first = self._status_path().read_text(encoding="utf-8")
        self.generate_status.run(self.root, None, apply=True, timestamp=False)
        second = self._status_path().read_text(encoding="utf-8")
        self.assertEqual(first, second)
        # And a second run reports no change.
        rep = self.generate_status.run(self.root, None, apply=False, timestamp=False)
        self.assertFalse(rep["changed"])

    def test_timestamp_line_is_only_nondeterministic_byte(self):
        r1 = self.generate_status.run(self.root, None, apply=False, timestamp=True)
        r2 = self.generate_status.run(self.root, None, apply=False, timestamp=True)
        self.assertEqual(
            self.generate_status.normalize_for_compare(r1["rendered"]),
            self.generate_status.normalize_for_compare(r2["rendered"]),
        )

    def test_status_matches_matrix_zero_crosscheck_warnings(self):
        """The whole point of T513: after a STATUS regen on unchanged spec inputs,
        the matrix cross-check (Matrix-cell vs STATUS-cell) must produce ZERO
        disagreement warnings for resolvable specs."""
        import check_platform_status as cps
        self.generate_status.run(self.root, None, apply=True, timestamp=False)
        status_rows = {r["Platform"]: r for r in cps.parse_status_rows(self._status_path())}
        specs_root = self.root / ".gald3r_sys" / "platforms"
        disagreements = []
        for p in cps.KNOWN_PLATFORMS:
            spec_path = cps.resolve_spec_path(self.root, specs_root, p)
            if spec_path is None:
                continue
            content = spec_path.read_text(encoding="utf-8")
            matrix_cells = psio.capability_cells(content)
            srow = status_rows[p]
            for cap in psio.CAPABILITY_COLUMNS:
                if srow[cap] in psio.VALID_CELLS and matrix_cells[cap] != srow[cap]:
                    disagreements.append((p, cap, matrix_cells[cap], srow[cap]))
        self.assertEqual(disagreements, [], f"cross-check drift: {disagreements}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
