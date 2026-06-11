#!/usr/bin/env python3
"""Python port of migrate_schemas.ps1 (T1587).

gald3r schema migration engine (T1441). Migrates .gald3r/ files forward to the
current schema version when a new gald3r release introduces new required fields
or renames deprecated/removed ones. Data is NEVER deleted.

Reads .gald3r_sys/schemas/_registry.yaml, globs every file matching each
registered pattern under <project>/.gald3r/, reads each file's
``schema_version`` frontmatter (absent == v0), and runs a per-version migration
chain up to the target version.

DATA PRESERVATION GUARANTEE
  * No field is ever deleted.
  * ``added[]`` fields are populated via Population Rules (git creation date,
    registry/identity version, or a ``TODO:`` marker when unknowable).
  * ``deprecated[]`` fields are renamed to ``deprecated_<name>``.
  * ``removed[]``    fields are renamed to ``legacy_<name>``.

VERSION ORDERING
  * file == target -> skip; file > target -> skip + log (NEVER downgrade);
  * file < target -> run migration chain v(n+1)..target.

Idempotent: a second --apply pass produces zero additional changes.
Exit codes: 0 success, 1 migration errors, 2 bad inputs — same as the PS1.

Parsing/regeneration helpers live in the sibling module migrate_schemas_lib.py.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import glob as _glob
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate_schemas_lib as lib  # noqa: E402
from migrate_schemas_lib import cprint  # noqa: E402

SCRIPT_ROOT = str(Path(__file__).resolve().parent)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Mirror the PS1 param() block (both -PascalCase and --kebab-case)."""
    p = argparse.ArgumentParser(
        prog="migrate_schemas.py", allow_abbrev=False,
        description="gald3r schema migration engine (T1441). Dry-run by default; "
                    "pass -Apply/--apply to write changes.",
    )
    p.add_argument("-ProjectPath", "--project-path", dest="project_path",
                   default=os.getcwd(),
                   help="Project root containing .gald3r/ (default: current dir).")
    p.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                   help="Write changes to disk (default: dry-run report only).")
    p.add_argument("-TargetVersion", "--target-version", dest="target_version",
                   default="", help='Schema version to migrate TO (e.g. "v1").')
    p.add_argument("-SchemasDir", "--schemas-dir", dest="schemas_dir", default="",
                   help="Explicit path to the .gald3r_sys/schemas/ directory.")
    p.add_argument("-RestoreMissing", "--restore-missing", dest="restore_missing",
                   action="store_true",
                   help="T1442: restore absent single-file .gald3r/ artifacts from "
                        "the canonical template_verification/ template.")
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Migration core (per file) — Invoke-FileMigration
# ---------------------------------------------------------------------------

def invoke_file_migration(file_path: str, schema_entry: Dict[str, Optional[str]],
                          target_num: int, do_apply: bool, project_path: str,
                          schemas_dir: str, rel_version_for_files: str) -> dict:
    """Migrate one file to `target_num`; returns a status record."""
    fm = lib.read_front_matter(file_path)
    cur_ver_raw = fm.fields.get("schema_version", "").strip().strip('"').strip("'")
    cur_num = lib.convert_to_version_number(cur_ver_raw)

    base = {"File": file_path, "From": cur_num, "To": target_num,
            "Added": [], "Todos": [], "Renames": []}
    if cur_num == target_num:
        return {**base, "Status": "skipped-current"}
    if cur_num > target_num:
        return {**base, "Status": "skipped-newer"}
    # Files without YAML frontmatter (e.g. the key=value .identity dotfile)
    # cannot carry frontmatter schema metadata — skip without mutation.
    if not fm.has_front_matter:
        return {**base, "Status": "skipped-no-frontmatter"}

    added_fields: List[str] = []
    todo_fields: List[str] = []
    renames: List[Dict[str, str]] = []

    # Build the migration chain v(cur+1) .. target
    for v in range(cur_num + 1, target_num + 1):
        schema_file = lib.get_schema_file_for_id(
            schema_entry.get("schema_id"), v, schemas_dir)
        step = lib.get_migration_step(schema_file, v)

        for a in step["added"]:
            field_name = (a.get("field") or "").strip()
            if not field_name:
                continue
            # schema_version / gald3r_rel_version are written unconditionally below
            if field_name in ("schema_version", "gald3r_rel_version"):
                continue
            if field_name in fm.fields:
                continue  # already present, leave value
            # Population Rules
            val = None
            if re.search(r"created_date|reported_date", field_name, re.IGNORECASE):
                val = lib.get_git_creation_date(file_path, project_path)
            if val:
                added_fields.append(f"{field_name}={val}")
            else:
                todo_fields.append(field_name)
        for d in step["deprecated"]:
            fn = d.get("field") or ""
            if fn in fm.fields and f"deprecated_{fn}" not in fm.fields:
                renames.append({"from": fn, "to": f"deprecated_{fn}"})
        for r in step["removed"]:
            fn = r.get("field") or ""
            if fn in fm.fields and f"legacy_{fn}" not in fm.fields:
                renames.append({"from": fn, "to": f"legacy_{fn}"})

    if not do_apply:
        return {**base, "Status": "to-migrate", "Added": added_fields,
                "Todos": todo_fields, "Renames": renames}

    # ---- APPLY: rewrite frontmatter ----
    lines = list(fm.lines)

    # 1. Renames (in-place line edits within frontmatter)
    for rn in renames:
        for i in range(1, fm.fm_end):
            m = re.match(rf"^({re.escape(rn['from'])}):(\s?.*)$", lines[i])
            if m:
                lines[i] = f"{rn['to']}:{m.group(2)}"
                break

    # 2. Added fields with resolved values + TODO markers (insert before closing ---)
    insert_at = fm.fm_end  # index of closing '---'
    new_field_lines: List[str] = []
    for a in added_fields:
        name, _, value = a.partition("=")
        new_field_lines.append(f"{name}: {value}")
    for t in todo_fields:
        new_field_lines.append(f"{t}: 'TODO: populate {t} (schema migration)'")

    # 3. schema_version + gald3r_rel_version (set or overwrite)
    target_ver_str = f"v{target_num}"
    sv_found = gr_found = False
    for i in range(1, fm.fm_end):
        if re.match(r"^schema_version:", lines[i]):
            lines[i] = f"schema_version: {target_ver_str}"
            sv_found = True
        if re.match(r"^gald3r_rel_version:", lines[i]):
            lines[i] = f'gald3r_rel_version: "{rel_version_for_files}"'
            gr_found = True
    if not sv_found:
        new_field_lines.append(f"schema_version: {target_ver_str}")
    if not gr_found:
        new_field_lines.append(f'gald3r_rel_version: "{rel_version_for_files}"')

    if new_field_lines:
        lines[insert_at:insert_at] = new_field_lines

    with open(file_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(fm.newline.join(lines))

    return {**base, "Status": "migrated", "Added": added_fields,
            "Todos": todo_fields, "Renames": renames}


# ---------------------------------------------------------------------------
# Drive: glob each pattern, migrate each file
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not os.path.exists(args.project_path):
        cprint(f"ERROR: ProjectPath not found: {args.project_path}", "red")
        return 2
    project_path = os.path.realpath(args.project_path)
    dot_gald3r = os.path.join(project_path, ".gald3r")

    schemas_resolved = lib.resolve_schemas_dir(args.schemas_dir, project_path,
                                               SCRIPT_ROOT)
    if not schemas_resolved:
        cprint("ERROR: schemas dir not found (looked relative to script and under "
               f"{project_path}\\.gald3r_sys\\schemas).", "red")
        return 2
    registry_path = os.path.join(schemas_resolved, "_registry.yaml")
    if not os.path.exists(registry_path):
        cprint(f"ERROR: _registry.yaml not found in {schemas_resolved}", "red")
        return 2

    system_rel_version = lib.get_yaml_scalar(registry_path, "gald3r_rel_version") \
        or "unknown"

    # Identity gald3r_version (preferred for gald3r_rel_version population)
    identity_path = os.path.join(dot_gald3r, ".identity")
    identity_rel_version: Optional[str] = None
    if os.path.exists(identity_path):
        with open(identity_path, "r", encoding="utf-8-sig") as fh:
            for line in fh.read().splitlines():
                m = re.match(r"^\s*gald3r_version\s*=\s*(.+)$", line)
                if m:
                    identity_rel_version = m.group(1).strip().strip('"').strip("'")
                    break
    rel_version_for_files = identity_rel_version or system_rel_version

    registry_schemas = lib.parse_registry(registry_path)
    report: List[dict] = []

    proj_name = os.path.basename(project_path.rstrip("\\/"))
    mode = "--apply" if args.apply else "dry-run"

    print()
    cprint(f"gald3r schema migration ({mode}) -- project: {proj_name}", "cyan")
    cprint(f"  Schemas: {schemas_resolved}", "darkgray")
    cprint(f"  System rel version: {system_rel_version}  |  "
           f"file rel version: {rel_version_for_files}", "darkgray")

    if not os.path.exists(dot_gald3r):
        cprint(f"  No .gald3r/ directory at {dot_gald3r} -- nothing to migrate.",
               "yellow")
        return 0

    # -----------------------------------------------------------------------
    # T1442: Restore-from-canonical pass (opt-in via -RestoreMissing). Runs
    # BEFORE migration so a freshly restored file is migrated forward too.
    # -----------------------------------------------------------------------
    restore_report: List[dict] = []
    if args.restore_missing:
        canonical = lib.resolve_dot_gald3r_canonical(project_path, SCRIPT_ROOT)
        print()
        if not canonical:
            cprint("  RestoreMissing: canonical template not found (looked relative "
                   f"to script and under {project_path}\\.gald3r_sys\\"
                   "template_verification\\.gald3r) -- restore skipped.",
                   "darkyellow")
        else:
            cprint(f"  RestoreMissing: canonical template = {canonical}", "darkgray")
            for entry in registry_schemas:
                if not entry.get("pattern"):
                    continue
                # Only literal single-file patterns are restorable; never
                # bulk-restore wildcard/recursive patterns (user data).
                if re.search(r"[\*\?]", entry["pattern"]):
                    continue
                rel_path = re.sub(r"^\.gald3r/", "", entry["pattern"]) \
                    .replace("/", os.sep)
                target_file = os.path.join(dot_gald3r, rel_path)
                if os.path.isfile(target_file):
                    continue  # present -- nothing to restore
                source_file = os.path.join(canonical, rel_path)
                if not os.path.isfile(source_file):
                    restore_report.append({"Status": "restore-unavailable",
                                           "Rel": rel_path})
                    continue
                if args.apply:
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    restore_report.append({"Status": "restored", "Rel": rel_path})
                    cprint(f"    RESTORED  {rel_path}  (from template_verification)",
                           "green")
                else:
                    restore_report.append({"Status": "to-restore", "Rel": rel_path})
                    cprint(f"    WOULD RESTORE  {rel_path}  "
                           "(from template_verification)", "yellow")
            restored_count = sum(1 for r in restore_report
                                 if r["Status"] in ("restored", "to-restore"))
            unavail_count = sum(1 for r in restore_report
                                if r["Status"] == "restore-unavailable")
            verb = "restored" if args.apply else "to restore"
            cprint(f"  RestoreMissing: {restored_count} file(s) {verb}, "
                   f"{unavail_count} unavailable in template.", "cyan")

    for entry in registry_schemas:
        if not entry.get("pattern"):
            continue
        # Determine target version for this schema
        this_target_num = lib.convert_to_version_number(
            args.target_version if args.target_version else entry.get("current_version"))
        if this_target_num <= 0:
            this_target_num = 1

        # Resolve glob: pattern is repo-relative beginning with ".gald3r/"
        rel_glob = re.sub(r"^\.gald3r/", "", entry["pattern"])
        glob_full = os.path.join(dot_gald3r, rel_glob.replace("/", os.sep))

        matched = [p for p in _glob.glob(glob_full, recursive=True)
                   if os.path.isfile(p)]
        if not matched and os.path.isfile(glob_full):
            matched = [glob_full]  # literal single-file patterns (.identity)

        for file_path in sorted(matched):
            res = invoke_file_migration(
                file_path, entry, this_target_num, args.apply,
                project_path, schemas_resolved, rel_version_for_files)
            res["SchemaId"] = entry.get("schema_id")
            report.append(res)

    # -----------------------------------------------------------------------
    # T1485: Grouped-format SUBSYSTEMS.md regeneration (conditional, safe no-op).
    # -----------------------------------------------------------------------
    grouped_result = lib.update_grouped_subsystems_index(dot_gald3r, args.apply)
    if grouped_result == "regenerated":
        cprint("  SUBSYSTEMS.md regenerated grouped by L1 system "
               "(parent_system: data present).", "green")
    elif grouped_result == "to-regenerate":
        cprint("  SUBSYSTEMS.md WOULD be regenerated grouped by L1 system "
               "(run -Apply).", "yellow")
    elif grouped_result == "index-section-missing":
        cprint("  SUBSYSTEMS.md has no '## Subsystem Index' section -- "
               "grouped regen skipped.", "darkyellow")
    # no-parent-system-data / no-*-md -> silent no-op (common case)

    # -----------------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------------
    to_migrate = [r for r in report if r["Status"] == "to-migrate"]
    migrated = [r for r in report if r["Status"] == "migrated"]
    skip_current = [r for r in report if r["Status"] == "skipped-current"]
    skip_newer = [r for r in report if r["Status"] == "skipped-newer"]
    skip_no_fm = [r for r in report if r["Status"] == "skipped-no-frontmatter"]
    errors = [r for r in report if r["Status"].startswith("error")]

    if not args.apply:
        print()
        cprint(f"Files to migrate: {len(to_migrate)}", "yellow")
        for r in to_migrate:
            name = os.path.basename(r["File"])
            adds = [a.split("=")[0] for a in r["Added"]]
            adds += r["Todos"]
            adds += [f"{rn['from']}->{rn['to']}" for rn in r["Renames"]]
            add_str = f" [ADD/RENAME: {', '.join(adds)}]" if adds else ""
            todo_str = f" (TODO: {', '.join(r['Todos'])})" if r["Todos"] else ""
            print(f"  {name:<44} v{r['From']} -> v{r['To']}{add_str}{todo_str}")
        print()
        print(f"Files with TODO required:  "
              f"{sum(1 for r in to_migrate if r['Todos'])}")
        print(f"Files skipped (current):   {len(skip_current)}")
        print(f"Files skipped (newer):     {len(skip_newer)}")
        print(f"Files skipped (no fm):     {len(skip_no_fm)}")
        for r in skip_newer:
            cprint(f"    NEWER  {os.path.basename(r['File'])}  "
                   f"(file v{r['From']} > target v{r['To']}) -- left untouched",
                   "darkyellow")
        if errors:
            cprint(f"Errors:                    {len(errors)}", "red")
            for r in errors:
                cprint(f"    {os.path.basename(r['File'])}  [{r['Status']}]", "red")
        print()
        cprint("Run with -Apply to execute.", "yellow")
        return 0

    # Apply summary
    todo_count = sum(1 for r in migrated if r["Todos"])
    skipped_total = len(skip_current) + len(skip_newer) + len(skip_no_fm)
    print()
    cprint(f"Migrated:       {len(migrated):<4} files", "green")
    print(f"TODO inserted:  {todo_count:<4} files")
    print(f"Skipped:        {skipped_total:<4} files  (current: {len(skip_current)}, "
          f"newer: {len(skip_newer)}, no-fm: {len(skip_no_fm)})")
    cprint(f"Errors:         {len(errors):<4} files",
           "red" if errors else "gray")
    for r in skip_newer:
        cprint(f"    NEWER  {os.path.basename(r['File'])}  "
               f"(file v{r['From']} > target v{r['To']}) -- left untouched",
               "darkyellow")
    for r in errors:
        cprint(f"    {os.path.basename(r['File'])}  [{r['Status']}]", "red")
    print()
    if migrated:
        cprint("Schema migration complete. Run @g-medic to validate migrated files.",
               "cyan")
    else:
        cprint("Schema migration complete. No files needed migration "
               "(already current).", "cyan")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
