"""Regression tests for the Workspace-Control template export helper.

Restored under T1532 (framework test harness re-arm). Only the import path was
fixed for the gald3r_templates layout; the test logic is unchanged from the
original gald3r_dev copy.

Coverage focus:
- BUG-030: paths_overlap must be case-insensitive on Windows (and remain
  case-sensitive on POSIX) and must continue to handle backslash/forward-slash
  normalization, exact matches, prefix matches, and non-overlap cases.

In gald3r_dev the export script lived at ``scripts/workspace_template_export.py``.
After the gald3r_dev -> gald3r_templates split it lives at
``custom_scripts/_delete_when_sure/workspace_template_export.py``. This test sits
at ``custom_scripts/tests/`` so ``parents[1]`` is ``custom_scripts`` and the
export module is one directory over in ``_delete_when_sure``.

Run via:
    python -m pytest custom_scripts/tests/test_workspace_template_export.py -v

or directly:
    python custom_scripts/tests/test_workspace_template_export.py
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

CUSTOM_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
# The export helper currently lives under custom_scripts/_delete_when_sure/.
# If it is ever promoted up into custom_scripts/ proper, add that directory too;
# both candidates are placed on sys.path so the import survives the move.
EXPORT_DIRS = [
    CUSTOM_SCRIPTS_DIR / "_delete_when_sure",
    CUSTOM_SCRIPTS_DIR,
]
for _candidate in EXPORT_DIRS:
    if _candidate.is_dir():
        sys.path.insert(0, str(_candidate))

from workspace_template_export import (  # noqa: E402
    IS_CASE_INSENSITIVE_FS,
    paths_overlap,
)


class PathsOverlapTests(unittest.TestCase):
    """BUG-030 acceptance-criteria coverage."""

    def test_exact_match_returns_true(self):
        self.assertTrue(paths_overlap("scripts/foo.py", "scripts/foo.py"))

    def test_no_overlap_returns_false(self):
        self.assertFalse(paths_overlap("scripts/foo.py", "scripts/bar.py"))

    def test_backslash_to_forward_slash_normalization(self):
        self.assertTrue(paths_overlap(r"src\lib\foo.py", "src/lib/foo.py"))

    def test_directory_prefix_match_returns_true(self):
        self.assertTrue(paths_overlap("scripts/", "scripts/foo.py"))
        self.assertTrue(paths_overlap("scripts/foo.py", "scripts/"))

    def test_empty_paths_return_false(self):
        self.assertFalse(paths_overlap("", "scripts/foo.py"))
        self.assertFalse(paths_overlap("scripts/foo.py", ""))
        self.assertFalse(paths_overlap("/", "/"))

    def test_case_handling_matches_platform(self):
        result = paths_overlap("Scripts/Foo.py", "scripts/foo.py")
        if IS_CASE_INSENSITIVE_FS:
            self.assertTrue(
                result,
                "Windows should treat case-different paths as overlapping "
                "(BUG-030 AC).",
            )
        else:
            self.assertFalse(
                result,
                "POSIX must remain case-sensitive (BUG-030 explicit "
                "preserve-Linux-behavior requirement).",
            )

    def test_case_handling_constant_matches_os(self):
        self.assertEqual(IS_CASE_INSENSITIVE_FS, os.name == "nt")

    def test_partial_substring_does_not_falsely_overlap(self):
        # 'scripts/foo' is NOT a parent of 'scripts/foobar' — overlap must
        # require a real path-segment boundary (the trailing slash check).
        self.assertFalse(paths_overlap("scripts/foo", "scripts/foobar"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
