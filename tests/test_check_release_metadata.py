"""Metadata checks are deliberately read-only and do not duplicate asset catalogs."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_release_metadata", ROOT / ".github/scripts/check_release_metadata.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def release(tag="v5.0.54", draft=True):
    return {"tag_name": tag, "draft": draft, "prerelease": False,
            "body": f"Downloads: https://github.com/{checker.REPOSITORY}/releases/download/{tag}/example.zip",
            "assets": [{"name": "SHA256SUMS.txt", "state": "uploaded", "size": 100}]}


class MetadataTests(unittest.TestCase):
    def test_staged_and_published_releases_are_never_changed(self):
        for draft in (True, False):
            pages = [[release(draft=draft)]]
            before = copy.deepcopy(pages)
            self.assertEqual(checker.check_metadata("v5.0.54", pages), "draft" if draft else "published")
            self.assertEqual(pages, before)

    def test_historic_notes_only_beta_flags_preserved(self):
        for tag in ("v5.0.53", "v5.0.0-beta.51", "v4.0.0-rc.1"):
            item = release(tag)
            item.update(body="Historic notes", assets=[], prerelease=True)
            self.assertEqual(checker.check_metadata(tag, [[item]]), "draft")
            self.assertTrue(item["prerelease"])

    def test_modern_boundary_requires_mirror_metadata(self):
        for tag in ("v5.0.54", "v5.0.55", "v6.0.0"):
            item = release(tag)
            item["assets"] = []
            with self.assertRaisesRegex(ValueError, "checksum"):
                checker.check_metadata(tag, [[item]])

    def test_missing_or_duplicate_release_refused(self):
        for pages in ([], [[]], [[release(), release()]]):
            with self.assertRaisesRegex(ValueError, "one existing"):
                checker.check_metadata("v5.0.54", pages)

    def test_empty_notes_refused(self):
        for body in (None, "", " \n"):
            item = release()
            item["body"] = body
            with self.assertRaisesRegex(ValueError, "no notes"):
                checker.check_metadata("v5.0.54", [[item]])

    def test_unfinished_or_empty_checksum_refused(self):
        for change in ({"size": 0}, {"size": True}, {"state": "starter"}, {"name": "other.txt"}):
            item = release()
            item["assets"][0].update(change)
            with self.assertRaisesRegex(ValueError, "checksum"):
                checker.check_metadata("v5.0.54", [[item]])

    def test_unknown_draft_state_is_not_reported_as_published(self):
        item = release()
        item.pop("draft")
        with self.assertRaisesRegex(ValueError, "draft state"):
            checker.check_metadata("v5.0.54", [[item]])

    def test_wrong_repository_or_tag_links_refused(self):
        for body in ("notes only", "https://github.com/Gald3r-Labs/gald3r_core/releases/download/v5.0.54/a.zip",
                     "https://github.com/Gald3r-Labs/gald3r/releases/download/v5.0.53/a.zip"):
            item = release()
            item["body"] = body
            with self.assertRaisesRegex(ValueError, "download links"):
                checker.check_metadata("v5.0.54", [[item]])

    def test_invalid_tags_fail_before_subprocess(self):
        with patch.object(checker.subprocess, "run") as run:
            for tag in ("main", "v5.0.54\n", "v05.0.54", "../v5.0.54"):
                self.assertEqual(checker.main(["--tag", tag]), 1)
            run.assert_not_called()

    def test_authenticated_pagination_get_is_the_only_remote_command(self):
        with patch.object(checker.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([[], [release()]]), "")) as run:
            self.assertEqual(checker.main(["--tag", "v5.0.54"]), 0)
            self.assertEqual(run.call_args.args[0], ["gh", "api", "--hostname", "github.com", "--method", "GET",
                             "repos/Gald3r-Labs/gald3r/releases?per_page=100", "--paginate", "--slurp"])
            self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_remote_failure_is_not_success_or_creation(self):
        with patch.object(checker.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "credential-not-printed")) as run:
            self.assertEqual(checker.main(["--tag", "v5.0.54"]), 1)
            self.assertEqual(run.call_count, 1)

    def test_public_workflow_mode_refuses_visible_draft(self):
        with patch.object(checker.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([[release()]]), "")) as run:
            self.assertEqual(checker.main(["--tag", "v5.0.54", "--require-published"]), 1)
            self.assertEqual(run.call_count, 1)

    def test_public_workflow_mode_accepts_published_metadata(self):
        with patch.object(checker.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([[release(draft=False)]]), "")) as run:
            self.assertEqual(checker.main(["--tag", "v5.0.54", "--require-published"]), 0)
            self.assertEqual(run.call_count, 1)

    def test_tag_push_does_not_query_partial_or_invisible_drafts(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("release:\n    types: [published]", workflow)
        self.assertIn("if: github.event_name == 'release' || github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("--require-published", workflow)
        self.assertIn("inputs.tag || github.event.release.tag_name", workflow)
        self.assertNotIn("inputs.tag || github.ref_name", workflow)

    def test_workflow_has_no_writer_and_retains_readonly_permissions(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("check_release_metadata.py", workflow)
        for forbidden in ("contents: write", "action-gh-release", "body_path:", "draft: false", "gh release create", "gh release edit"):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
