"""CLI surface: `gald3r task new|list|update|sync`, `gald3r mcp`, `gald3r --version`.

Thin — every command calls the same `Gald3r` core the MCP/HTTP surfaces use.
Stdlib argparse only (zero deps), so it runs anywhere uv puts a Python.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from gald3r import __version__
from gald3r import crash as _crash
from gald3r.core import Gald3r
from gald3r.debug import tracer


def _ensure_utf8() -> None:
    """Force UTF-8 on stdout/stderr so emoji status markers print on the Windows
    console (cp1252) and anywhere else. No-op on already-UTF-8 streams (mac/linux)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _print_task(t, as_json: bool) -> None:
    if as_json:
        print(json.dumps(t.to_dict(), ensure_ascii=False))
    else:
        print(f"[{t.marker}] T{t.id}  {t.title}  ({t.status}, {t.priority})  -> tasks/{t.folder}/")


def _run_migrate_home(args) -> int:
    """Handle `gald3r migrate-home` (T530) — consolidate scattered legacy per-user
    gald3r locations into the unified canonical home. Project-independent (like
    `home`): it does NOT build a Gald3r(root=...). Idempotent + non-destructive —
    legacy trees are copied, never deleted (see gald3r.migration)."""
    import platform as _platform

    from gald3r import migration as _migration

    report = _migration.migrate(
        dict(os.environ), _platform.system(), dry_run=args.dry_run
    )
    if args.json:
        out = report.to_dict()
        out["dry_run"] = bool(args.dry_run)
        print(json.dumps(out, ensure_ascii=False))
        return 0

    print(f"unified home: {report.canonical_target}")
    if report.already_migrated:
        print("  already migrated (sentinel present) — nothing to do")
        return 0
    prefix = "[dry-run] would migrate" if args.dry_run else "migrated"
    any_done = False
    for a in report.actions:
        if a.action in ("migrate", "done"):
            any_done = True
            tail = (f" ({a.files_copied} copied, {a.files_skipped} skipped)"
                    if a.action == "done" else "")
            print(f"  {prefix}: [{a.label}] {a.source}{tail}")
        elif a.action == "error":
            any_done = True
            print(f"  ! ERROR [{a.label}] {a.source}: {a.error}")
    if not any_done:
        print("  no legacy locations found — nothing to migrate")
    return 0


def _run_install_or_setup(args) -> int:
    """Handle `gald3r install` / `gald3r setup` (project-independent, like `home`).

    Both verbs accept ``agent`` / ``throne`` / ``all``, build a plan per product,
    print it (always, so --dry-run and the real run share one rendering), and —
    unless ``--dry-run`` — execute. Throne with a missing per-OS bundle fails loud
    (no silent stub): the plan carries the build command and the executor raises
    (T472, g-rl-34).
    """
    # TODO[TASK-472→TASK-528]: gald3r install throne — precompiled installer not yet available.
    # TODO[TASK-472→TASK-529]: gald3r install agent  — precompiled binary not yet available.
    # Both products currently require building from source (T528/T529 pending).
    # Block the install verb until precompiled artifacts are shipped.
    if args.cmd == "install":
        msg = (
            "gald3r install is not yet available for consumer use.\n"
            "\n"
            "  Throne (gald3r_throne) and Agent (gald3r_agent) do not yet have\n"
            "  precompiled installers — both currently require building from source.\n"
            "\n"
            "  Precompiled installers are tracked in:\n"
            "    T528 — Throne signed installer (Windows/macOS/Linux)\n"
            "    T529 — Agent packaged binary (IP-protected, no source required)\n"
            "\n"
            "  Once those ship, this command will work as documented.\n"
            "  Developer path: build from source per RELEASE.md (Throne) or\n"
            "  `uv pip install -e .` (Agent)."
        )
        if getattr(args, "json", False):
            import json as _json
            print(_json.dumps({"error": "install_not_yet_available",
                               "message": msg, "pending_tasks": ["T528", "T529"]}))
        else:
            print(msg)
        return 2

    from gald3r import install as _install

    portable = True if getattr(args, "portable", False) else None
    products = (_install.PRODUCTS if args.product == _install.PRODUCT_ALL
                else (args.product,))
    payload = []
    rc = 0
    for product in products:
        try:
            if args.cmd == "install":
                plan = _install.plan_install(
                    product, products_root=getattr(args, "products_root", None),
                    home=_install._home.resolve_install_home(portable=portable))
            else:
                plan = _install.plan_setup(product, portable=portable)
        except (_install.InstallError, ValueError) as e:
            payload.append({"product": product, "error": str(e)})
            if not args.json:
                print(f"[{product}] ERROR: {e}")
            rc = 2
            continue

        entry = {"product": product, "plan": plan.to_dict(), "executed": False, "log": []}
        if not args.json:
            print(f"== {args.cmd} {product} ({plan.host_os if args.cmd == 'install' else 'home'}) ==")
            for a in plan.actions:
                print(f"  - {a}")

        if args.dry_run:
            if not args.json:
                print("  (dry-run: nothing executed)")
        else:
            try:
                log = (_install.execute_install(plan) if args.cmd == "install"
                       else _install.execute_setup(plan, portable=portable))
                entry["executed"] = True
                entry["log"] = log
                if not args.json:
                    for line in log:
                        if line:
                            print(f"  > {line}")
            except _install.InstallError as e:
                entry["error"] = str(e)
                if not args.json:
                    print(f"  ! FAILED (no stub, no fake success): {e}")
                rc = 2
        payload.append(entry)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    return rc


def _add_selfupdate_parsers(sub) -> None:
    """Register the shared `version-check` + `upgrade` subcommands (T473/T475).

    Both surfaces (agent, template-installed project) call the SAME engine ops via these
    subcommands; the CLI is only the thin executor (see gald3r.systems.upgrade)."""
    pvc = sub.add_parser("version-check",
                         help="check world_tree for a newer gald3r version (offline-safe)")
    pvc.add_argument("--base-url", dest="base_url", default=None,
                     help="world_tree base URL (or GALD3R_WORLD_TREE_URL env)")
    pvc.add_argument("--token", default=None, help="bearer token for the JWT-gated route")
    pvc.add_argument("--timeout", type=float, default=None, help="network timeout (s)")

    pup = sub.add_parser("upgrade",
                         help="safely migrate .gald3r/ to the latest format "
                              "(timestamped gitignored backup -> migrate -> rollback)")
    pup.add_argument("--apply", action="store_true",
                     help="write changes (default: --dry-run; backup + migrate + rollback)")
    pup.add_argument("--from-dir", dest="from_dir", default=None,
                     help="source .gald3r/ snapshot (default: the live project .gald3r/)")
    pup.add_argument("--to-dir", dest="to_dir", default=None,
                     help="target-format .gald3r/ snapshot (default: resolved snapshot)")
    pup.add_argument("--from-version", dest="from_version", default=None,
                     help="source by stored version (T463 snapshot .gald3r_sys/snapshots/v<X.Y.Z>)")
    pup.add_argument("--to-version", dest="to_version", default=None,
                     help="target by stored version (T463 snapshot .gald3r_sys/snapshots/v<A.B.C>)")
    pup.add_argument("--base-url", dest="base_url", default=None,
                     help="world_tree base URL for the version delta (or GALD3R_WORLD_TREE_URL)")
    pup.add_argument("--token", default=None, help="bearer token for the version delta probe")


def _run_selfupdate(args, g) -> int:
    """Execute `version-check` / `upgrade` against the shared self-update core."""
    from gald3r.systems import upgrade as _up

    base_url = getattr(args, "base_url", None) or os.environ.get("GALD3R_WORLD_TREE_URL")
    token = getattr(args, "token", None)

    if args.cmd == "version-check":
        timeout = args.timeout if args.timeout is not None else _up.DEFAULT_TIMEOUT
        info = g.upgrade.check(base_url=base_url, token=token, timeout=timeout)
        if args.json:
            print(json.dumps(info, ensure_ascii=False))
        else:
            print(info["message"])
        return 0 if info.get("reachable") else 1

    # args.cmd == "upgrade"
    dry_run = not args.apply
    version_info = g.upgrade.check(base_url=base_url, token=token)
    res = g.upgrade.self_update(
        to_dir=args.to_dir, from_dir=args.from_dir,
        to_version=getattr(args, "to_version", None),
        from_version=getattr(args, "from_version", None),
        dry_run=dry_run, version_info=version_info,
    )
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["ok"] else 2
    delta = res["version_delta"]
    if delta.get("update_available") is None:
        print(f"version: {delta['current']} ({delta.get('note', '')})")
    else:
        avail = "update available" if delta["update_available"] else "up to date"
        print(f"version: {delta['current']} -> {delta.get('latest')} ({avail})")
    plan = res["plan"]
    if res["error"] and not res["plan"]["add"] and not res["plan"]["merge"]:
        print(f"! {res['error']}")
        return 2
    prefix = "[DRY] would" if dry_run else "applied:"
    print(f"{prefix}  ADD={len(plan['add'])}  MERGE={len(plan['merge'])}  "
          f"DEPRECATE={len(plan['deprecate'])}  SKIP(user-data)={len(plan['skip'])}")
    for rel in plan["add"]:
        print(f"  [ADD]       {rel}")
    for rel in plan["merge"]:
        print(f"  [MERGE]     {rel}")
    for rel in plan["deprecate"]:
        print(f"  [DEPRECATE] {rel}")
    if not dry_run:
        if res["backup"]:
            print(f"backup: {res['backup']}  (gitignored *.zip)")
        if res["rolled_back"]:
            print(f"! migration failed and was ROLLED BACK: {res['error']}")
            return 2
        if not res["ok"]:
            print(f"! {res['error']}")
            return 2
    return 0


def _run_init(args) -> int:
    """Handle `gald3r init` — scaffold a fresh gald3r PROJECT into a target folder.

    Delegates scaffolding to the canonical installer + PROJECT.md param-seeding
    via :mod:`gald3r.scaffold` (REUSE: setup_gald3r_project / g-skl-setup +
    gald3r.provision). When the target already contains a gald3r project, the plan
    routes to the safe-update path instead of re-initializing (don't-clobber).
    """
    from gald3r import scaffold as _scaffold

    try:
        plan = _scaffold.plan_scaffold(
            target=args.target, name=args.name, description=args.description,
            vision=args.vision, tech_stack=args.tech_stack, tier=args.tier,
        )
    except _scaffold.ScaffoldError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"! init failed (no stub, no fake success): {e}")
        return 2

    payload = {"plan": plan.to_dict(), "executed": False, "log": []}
    if not args.json:
        header = "update (don't-clobber: target already a gald3r project)" \
            if plan.mode == "update" else "init"
        print(f"== {header}: {plan.target} ==")
        for a in plan.actions:
            print(f"  - {a}")

    if args.dry_run:
        log = _scaffold.execute_scaffold(plan, dry_run=True)
        payload["log"] = log
        if not args.json:
            for line in log:
                print(f"  > {line}")
            print("  (dry-run: nothing executed)")
            if plan.mode == "update":
                print(f"  next: gald3r update --target \"{plan.target}\" --apply")
        else:
            print(json.dumps(payload, ensure_ascii=False))
        return 0

    if plan.mode == "update":
        # Don't-clobber: hand straight to the safe-update path against the target.
        if not args.json:
            print("  routing to safe-update (gald3r update) — target not re-initialized.")
        rc = _run_update_for_root(plan.target, apply=False)
        if args.json:
            payload["routed_to_update"] = True
            print(json.dumps(payload, ensure_ascii=False))
        return rc

    try:
        log = _scaffold.execute_scaffold(plan, dry_run=False)
        payload["executed"] = True
        payload["log"] = log
        if not args.json:
            for line in log:
                print(f"  > {line}")
        else:
            print(json.dumps(payload, ensure_ascii=False))
    except _scaffold.ScaffoldError as e:
        payload["error"] = str(e)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"  ! FAILED (no stub, no fake success): {e}")
        return 2
    return 0


def _run_update(args) -> int:
    """Handle `gald3r update` — route a target folder to the T473 safe-update core.

    Resolves the project root from ``--target`` (its ``.gald3r/``) and reuses the
    EXISTING ``upgrade`` executor (:func:`_run_selfupdate`) — no forked update
    logic. Without ``--target`` it behaves like ``gald3r upgrade`` on the nearest
    ``.gald3r/`` (honoring the global ``--root``).
    """
    root = args.target if args.target else args.root
    # When --target is given it must BE a gald3r project (a direct .gald3r/) — we
    # do not walk up into someone else's project. Without --target, defer to the
    # global --root / nearest-.gald3r/ resolution (matches `gald3r upgrade`).
    if args.target is not None:
        from gald3r import scaffold as _scaffold
        if not _scaffold.is_initialized(args.target):
            msg = (f"no gald3r project (.gald3r/) at target '{args.target}'. "
                   f"Run `gald3r init --target \"{args.target}\"` to scaffold one.")
            if args.json:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"! update failed: {msg}")
            return 2
    try:
        g = Gald3r(root=root)
    except FileNotFoundError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"! update failed: {e}")
        return 2
    # Reuse the shared upgrade executor verbatim (it reads args.cmd == "upgrade").
    args.cmd = "upgrade"
    return _run_selfupdate(args, g)


def _run_update_for_root(root, *, apply: bool) -> int:
    """Run the safe-update core against ``root`` (used by `init` don't-clobber routing)."""
    try:
        g = Gald3r(root=root)
    except FileNotFoundError as e:
        print(f"! update routing failed: {e}")
        return 2
    version_info = g.upgrade.check()
    res = g.upgrade.self_update(dry_run=not apply, version_info=version_info)
    plan = res["plan"]
    if res["error"] and not plan["add"] and not plan["merge"]:
        print(f"! {res['error']}")
        return 2
    prefix = "[DRY] would" if not apply else "applied:"
    print(f"  {prefix}  ADD={len(plan['add'])}  MERGE={len(plan['merge'])}  "
          f"DEPRECATE={len(plan['deprecate'])}  SKIP(user-data)={len(plan['skip'])}")
    return 0


def _run_crash_stats(args, *, reset: bool, write_report: bool) -> int:
    """Handle `gald3r crash-stats` and the global --crash-stats[-reset] flags (T433).

    Project-independent re: tier (stats are a logging concern). Roots at --root /
    nearest .gald3r/. --reset archives the JSONL and starts fresh; otherwise the
    current stats report is rendered (markdown, or JSON with --json)."""
    from gald3r.config import find_root

    try:
        root = find_root(args.root)
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False) if args.json
              else f"! crash-stats failed: {e}")
        return 2

    if reset:
        archive = _crash.reset_log(root)
        msg = (f"archived -> {archive}" if archive
               else "nothing to archive (no crash_activations.jsonl yet)")
        print(json.dumps({"reset": True, "archive": str(archive) if archive else None},
                         ensure_ascii=False) if args.json else msg)
        return 0

    stats = _crash.compute_stats(root)
    report_path = None
    if write_report:
        report_path = _crash.write_report(root, stats=stats)
    if args.json:
        out = dict(stats)
        if report_path is not None:
            out["report_path"] = str(report_path)
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(_crash.render_report(stats), end="")
        if report_path is not None:
            print(f"\n(report written: {report_path})")
    return 0


def _emit_crash_signature(mode: str, root) -> None:
    """Emit the compact CRASH stats summary per output mode (T433).

    show_in_response → stdout response signature; show_in_terminal → stdout table-ish
    summary; show_in_log → appended to the session debug log only (no stdout)."""
    try:
        stats = _crash.compute_stats(root)
        sig = _crash.render_signature(stats)
    except Exception:
        return
    if mode in (_crash.MODE_RESPONSE, _crash.MODE_TERMINAL):
        print(sig)
    elif mode == _crash.MODE_LOG:
        try:
            from gald3r.config import find_root
            base = find_root(root)
        except FileNotFoundError:
            return
        logs_dir = base / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "crash_stats_signature.log", "a", encoding="utf-8", newline="\n") as fh:
            fh.write(sig + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    _ensure_utf8()
    p = argparse.ArgumentParser(prog="gald3r", description="gald3r engine CLI")
    p.add_argument("--version", action="version", version=f"gald3r {__version__}")
    p.add_argument("--root", default=None, help="project root (defaults to nearest .gald3r/)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--debug", action="store_true",
                   help="enable debug-mode call-stack tracing (or set GALD3R_DEBUG=1)")
    p.add_argument("--debug-output", dest="debug_output", default=None,
                   choices=["terminal", "file", "both"],
                   help="debug trace sink (default terminal; or GALD3R_DEBUG_OUTPUT)")
    p.add_argument("--debug-json", dest="debug_json", action="store_true",
                   help="emit debug traces as newline-delimited JSON")
    p.add_argument("--crash-stats", dest="crash_stats", action="store_true",
                   help="display the CRASH activation stats report and exit (T433)")
    p.add_argument("--crash-stats-reset", dest="crash_stats_reset", action="store_true",
                   help="archive crash_activations.jsonl and start fresh, then exit (T433)")
    sub = p.add_subparsers(dest="cmd")

    pt = sub.add_parser("task", help="task operations").add_subparsers(dest="task_cmd")
    n = pt.add_parser("new")
    n.add_argument("--title", required=True)
    n.add_argument("--type", default="feature")
    n.add_argument("--priority", default="medium")
    n.add_argument("--status", default="pending")
    ls = pt.add_parser("list")
    ls.add_argument("--status", default=None)
    up = pt.add_parser("update")
    up.add_argument("id", type=int)
    up.add_argument("--status", default=None)
    up.add_argument("--title", default=None)
    up.add_argument("--priority", default=None)
    up.add_argument("--type", default=None)
    srh = pt.add_parser("set-release-hold", help="set release-staging hold (T419)")
    srh.add_argument("id", type=int)
    srh.add_argument("hold", choices=["none", "manual", "sync_required"])
    srh.add_argument("--reason", default="")
    srh.add_argument("--sync-project", dest="sync_project", default=None,
                     help="sync_required: partner project id")
    srh.add_argument("--sync-task", dest="sync_task", default=None,
                     help="sync_required: partner task id")
    crh = pt.add_parser("clear-release-hold", help="clear release-staging hold (T419)")
    crh.add_argument("id", type=int)
    pt.add_parser("sync")

    # goals (PROJECT.md section)
    pg = sub.add_parser("goal", help="project goal operations").add_subparsers(dest="goal_cmd")
    ga = pg.add_parser("add"); ga.add_argument("--text", required=True)
    pg.add_parser("list")
    gu = pg.add_parser("update"); gu.add_argument("id"); gu.add_argument("--text", required=True)
    gr = pg.add_parser("remove"); gr.add_argument("id")

    # bugs (folder + BUGS.md)
    pb = sub.add_parser("bug", help="bug operations").add_subparsers(dest="bug_cmd")
    bn = pb.add_parser("new")
    bn.add_argument("--title", required=True)
    bn.add_argument("--severity", default="medium")
    bn.add_argument("--kind", default="code")
    bn.add_argument("--status", default="open")
    bl = pb.add_parser("list"); bl.add_argument("--status", default=None)
    bu = pb.add_parser("update")
    bu.add_argument("id")
    bu.add_argument("--status", default=None)
    bu.add_argument("--severity", default=None)
    bu.add_argument("--title", default=None)
    pb.add_parser("sync")

    # vault (file-first knowledge store)
    pv = sub.add_parser("vault", help="vault operations").add_subparsers(dest="vault_cmd")
    vi = pv.add_parser("ingest")
    vi.add_argument("--title", required=True)
    vi.add_argument("--type", default="article")
    vi.add_argument("--source", required=True)
    vi.add_argument("--tags", default="", help="comma-separated")
    vi.add_argument("--ingestion-type", dest="ingestion_type", default="manual")
    vl = pv.add_parser("list"); vl.add_argument("--type", default=None)
    pv.add_parser("reindex")
    pv.add_parser("lint")

    # inbox (absorb staged task/bug drafts -> live state; replaces hot_inbox_intake.ps1)
    pi = sub.add_parser("inbox", help="intake staged task/bug drafts from inbox folders")
    pi.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="show what would be ingested without writing")

    # doctor (read-only health check; absorbs gald3r_system_test.ps1)
    pdoc = sub.add_parser("doctor", help="read-only health check across systems")
    pdoc.add_argument("--only", default=None, help="comma-separated subset (structure,tasks,bugs,skills)")
    pdoc.add_argument("--fail-below", dest="fail_below", type=int, default=0,
                      help="exit 1 if overall score < N")

    # validate (deterministic gate: schema + status normalization + folder placement, T520)
    pval = sub.add_parser("validate",
                          help="validate task/bug files (schema, status vocab, folder placement)")
    pval.add_argument("paths", nargs="*",
                      help="specific files to validate (default: all tasks/ + bugs/)")
    pval.add_argument("--fix", action="store_true",
                      help="apply safe normalizations (status canonicalization + folder moves)")

    # platform (capability reporting; absorbs check_platform_status.ps1 read path)
    pplat = sub.add_parser("platform", help="platform capability reporting").add_subparsers(dest="platform_cmd")
    pps = pplat.add_parser("status"); pps.add_argument("--platform", default="all")

    # tier (product tier show/set; absorbs the pure half of tier_sync.ps1)
    ptier = sub.add_parser("tier", help="product tier show/set").add_subparsers(dest="tier_cmd")
    ptier.add_parser("show")
    ptset = ptier.add_parser("set"); ptset.add_argument("tier")

    # sync (canonical -> platform-mirror parity; absorbs platform_parity_sync.ps1)
    psync = sub.add_parser("sync", help="canonical -> platform-mirror parity (check/apply)")
    psync.add_argument("--apply", action="store_true", help="write mirrors (default: check only)")
    psync.add_argument("--platform", default=None, help="limit to one full-tree mirror target")
    pparity = sub.add_parser("parity", help="alias: sync check (gap report only)")
    pparity.add_argument("--platform", default=None)

    # release (folder + RELEASES.md)
    pr = sub.add_parser("release", help="release operations").add_subparsers(dest="release_cmd")
    rn = pr.add_parser("new")
    rn.add_argument("--title", required=True)
    rn.add_argument("--version", required=True)
    rn.add_argument("--target-date", dest="target_date", default=None)
    rn.add_argument("--status", default="planned")
    pr.add_parser("list")
    rs = pr.add_parser("ship"); rs.add_argument("id"); rs.add_argument("--version", default=None)
    pr.add_parser("roadmap")

    # workspace (controller-tier: WPAC / Workspace-Control)
    pw = sub.add_parser("workspace", help="cross-project coordination (controller tier)")
    pw_sub = pw.add_subparsers(dest="workspace_cmd")
    pw_sub.add_parser("status")
    pw_sub.add_parser("validate")
    pw_sub.add_parser("conflicts")
    wa = pw_sub.add_parser("inbox-add")
    wa.add_argument("--section", default="REQUEST")
    wa.add_argument("--from", dest="from_project", required=True)
    wa.add_argument("--summary", required=True)

    # prompts (the judgment layer — package assets, served not executed)
    pp = sub.add_parser("prompt", help="judgment/prompt-asset library").add_subparsers(dest="prompt_cmd")
    pl = pp.add_parser("list"); pl.add_argument("--kind", default=None)
    pget = pp.add_parser("get")
    pget.add_argument("id")
    pget.add_argument("--input", action="append", default=[], metavar="k=v",
                      help="bind a ${slot} (repeatable)")

    # version-check / upgrade (self-update: version probe + safe .gald3r/ migration; T473/T475)
    _add_selfupdate_parsers(sub)

    # crash-stats (CRASH activation tracking — T433). On-demand stats report;
    # equivalent to the `@g-crash-stats` command. --reset archives the JSONL.
    pcs = sub.add_parser("crash-stats",
                         help="show CRASH activation stats (Commands/Rules/Agents/Skills/Hooks)")
    pcs.add_argument("--reset", action="store_true",
                     help="archive crash_activations.jsonl and start fresh")
    pcs.add_argument("--write-report", dest="write_report", action="store_true",
                     help="also write the dated crash_stats_YYYYMMDD.md report")

    sub.add_parser("mcp", help="run the MCP (stdio) server")

    # home (centralized install home — independent of any .gald3r/ project; T471)
    ph = sub.add_parser("home", help="show the centralized gald3r install home")
    ph.add_argument("--portable", action="store_true",
                    help="resolve the USB-portable home (or set GALD3R_PORTABLE=1)")
    ph.add_argument("--ensure", action="store_true",
                    help="create the home + settings/logs/gald3r_vault + VERSION if missing")

    # migrate-home (one-time, idempotent consolidation of scattered legacy
    # per-user locations into the unified home; independent of any .gald3r/; T530)
    pmh = sub.add_parser(
        "migrate-home",
        help="migrate scattered legacy gald3r per-user locations into the unified home")
    pmh.add_argument("--dry-run", dest="dry_run", action="store_true",
                     help="show what would be migrated without copying anything")

    # install / setup (per-OS product install; independent of any .gald3r/; T472)
    pins = sub.add_parser("install", help="install gald3r_agent / gald3r_throne for this OS")
    pins.add_argument("product", choices=["agent", "throne", "all"])
    pins.add_argument("--dry-run", dest="dry_run", action="store_true",
                      help="print the install plan (artifact, paths, PATH changes) and exit")
    pins.add_argument("--products-root", dest="products_root", default=None,
                      help="dir containing gald3r_agent/ + gald3r_throne/ (or GALD3R_PRODUCTS_ROOT)")
    pins.add_argument("--portable", action="store_true",
                      help="resolve the USB-portable install home")
    pset = sub.add_parser("setup", help="initialize gald3r_agent / gald3r_throne against the install home")
    pset.add_argument("product", choices=["agent", "throne", "all"])
    pset.add_argument("--dry-run", dest="dry_run", action="store_true",
                      help="print the setup plan without writing")
    pset.add_argument("--portable", action="store_true",
                      help="resolve the USB-portable install home")

    # init (scaffold a fresh gald3r PROJECT into a target folder; T477). Distinct
    # top-level verb from `setup <product>` (T472) — no positional, so the two
    # never share a positional argument and argparse cannot confuse them.
    pinit = sub.add_parser(
        "init",
        help="scaffold a fresh gald3r project into a target folder "
             "(CWD or --target) and seed PROJECT.md basics")
    pinit.add_argument("--target", default=None,
                       help="target project folder (default: current directory; "
                            "created if missing)")
    pinit.add_argument("--name", default="",
                       help="project name (default: install-home identity default "
                            "or the target folder name)")
    pinit.add_argument("--description", default="",
                       help="PROJECT.md Mission body (what the project does)")
    pinit.add_argument("--vision", default="",
                       help="PROJECT.md Vision body (one-paragraph vision)")
    pinit.add_argument("--tech-stack", dest="tech_stack", default="",
                       help="PROJECT.md Tech Stack body")
    pinit.add_argument("--tier", default="",
                       help="template tier label (default: install-home default or "
                            "'full')")
    pinit.add_argument("--dry-run", dest="dry_run", action="store_true",
                       help="print the scaffold/seed plan without writing")

    # update (alias: route a target folder to the T473 safe-update / upgrade path).
    pupd = sub.add_parser(
        "update",
        help="route a target folder to the safe-update path (alias of `upgrade`; "
             "timestamped gitignored backup -> migrate -> rollback)")
    pupd.add_argument("--target", default=None,
                      help="target gald3r project folder (default: nearest .gald3r/)")
    pupd.add_argument("--apply", action="store_true",
                      help="write changes (default: --dry-run)")
    pupd.add_argument("--from-dir", dest="from_dir", default=None,
                      help="source .gald3r/ snapshot (default: the live project .gald3r/)")
    pupd.add_argument("--to-dir", dest="to_dir", default=None,
                      help="target-format .gald3r/ snapshot (default: resolved snapshot)")
    pupd.add_argument("--base-url", dest="base_url", default=None,
                      help="world_tree base URL for the version delta (or GALD3R_WORLD_TREE_URL)")
    pupd.add_argument("--token", default=None, help="bearer token for the version delta probe")

    args = p.parse_args(argv)
    # Debug mode: CLI flags take precedence over env; env was applied at import.
    if args.debug or args.debug_output or args.debug_json:
        tracer().enable(
            output_mode=args.debug_output or "terminal",
            json_mode=args.debug_json,
            root=args.root,
        )

    # CRASH activation stats (T433): the global --crash-stats / --crash-stats-reset
    # flags act on their own (no subcommand needed) and exit early.
    if getattr(args, "crash_stats_reset", False):
        return _run_crash_stats(args, reset=True, write_report=False)
    if getattr(args, "crash_stats", False):
        return _run_crash_stats(args, reset=False, write_report=False)

    if args.cmd == "crash-stats":
        return _run_crash_stats(args, reset=args.reset, write_report=args.write_report)

    if args.cmd is None:
        p.print_help()
        return 0

    if args.cmd == "mcp":
        from gald3r.adapters import mcp as mcp_adapter
        mcp_adapter.run(root=args.root)
        return 0

    if args.cmd == "home":
        from gald3r import home as home_mod
        portable = True if args.portable else None
        path = (home_mod.ensure_install_home(portable=portable) if args.ensure
                else home_mod.resolve_install_home(portable=portable))
        info = {
            "home": str(path),
            "portable": bool(args.portable or home_mod._is_truthy(
                os.environ.get(home_mod.PORTABLE_ENV_VAR))),
            "settings": str(home_mod.subdir(home_mod.SETTINGS_DIR, home=path)),
            "logs": str(home_mod.subdir(home_mod.LOGS_DIR, home=path)),
            "vault": str(home_mod.subdir(home_mod.VAULT_DIR, home=path)),
            "version_file": str(path / home_mod.VERSION_FILE),
            "ensured": bool(args.ensure),
        }
        if args.json:
            print(json.dumps(info, ensure_ascii=False))
        else:
            print(f"install home: {info['home']}"
                  + ("  (portable)" if info["portable"] else ""))
            print(f"  settings : {info['settings']}")
            print(f"  logs     : {info['logs']}")
            print(f"  vault    : {info['vault']}")
            print(f"  version  : {info['version_file']}")
        return 0

    if args.cmd == "migrate-home":
        return _run_migrate_home(args)

    if args.cmd in ("install", "setup"):
        return _run_install_or_setup(args)

    if args.cmd == "init":
        # Project-scaffold (T477): project-INDEPENDENT (the target may have no
        # .gald3r/ yet), so it does NOT build a Gald3r(root=...). Don't-clobber
        # routes an already-initialized target to the update/upgrade path.
        return _run_init(args)

    # `update` is an alias of `upgrade` against a target folder: root it at
    # --target (its .gald3r/) so the shared T473 self-update core operates there.
    if args.cmd == "update":
        return _run_update(args)

    g = Gald3r(root=args.root)

    # CRASH activation tracking (T433): when GALD3R_CRASH_STATS is set, persist a
    # JSONL record for this command dispatch (zero overhead + no record when the
    # env var is unset/off — record_activation short-circuits on a single env read).
    # The shipped CLI dispatch is inline (not a wrapped _dispatch), so the record
    # is written here at dispatch entry rather than via the debug-tracer bridge.
    crash_mode = _crash.resolve_mode()
    if crash_mode != _crash.MODE_OFF:
        _crash.record_activation(
            "command", f"cli:{args.cmd}",
            trigger_source=f"gald3r {args.cmd}", root=args.root,
        )

    rc = _dispatch_command(args, p, g)

    # Output-mode side effects (response / log / terminal) after dispatch.
    if crash_mode != _crash.MODE_OFF:
        _emit_crash_signature(crash_mode, args.root)
    return rc


def _dispatch_command(args, p, g) -> int:
    """Inline command dispatch for the shipped CLI (extracted from main() so the
    CRASH stats output-mode side effects can wrap a single dispatch call)."""
    if args.cmd in ("version-check", "upgrade"):
        return _run_selfupdate(args, g)

    if args.cmd == "task":
        if args.task_cmd == "new":
            t = g.tasks.create(title=args.title, type=args.type,
                               priority=args.priority, status=args.status)
            _print_task(t, args.json)
        elif args.task_cmd == "list":
            tasks = g.tasks.list(status=args.status)
            if args.json:
                print(json.dumps([t.to_dict() for t in tasks], ensure_ascii=False))
            else:
                for t in tasks:
                    _print_task(t, False)
                print(f"\n{len(tasks)} task(s)" + (f" with status={args.status}" if args.status else ""))
        elif args.task_cmd == "update":
            t = g.tasks.update(args.id, status=args.status, title=args.title,
                               priority=args.priority, type=args.type)
            _print_task(t, args.json)
        elif args.task_cmd == "set-release-hold":
            sync_with = None
            if args.sync_project and args.sync_task:
                sync_with = [{"project": args.sync_project, "task": args.sync_task,
                              "reason": args.reason}]
            t = g.tasks.set_release_hold(args.id, args.hold, reason=args.reason,
                                         sync_with=sync_with)
            _print_task(t, args.json)
        elif args.task_cmd == "clear-release-hold":
            t = g.tasks.clear_release_hold(args.id)
            _print_task(t, args.json)
        elif args.task_cmd == "sync":
            rep = g.tasks.sync()
            print(json.dumps(rep, ensure_ascii=False) if args.json
                  else f"synced: {rep['tasks']} task(s); phantom={rep['phantom']}; orphan={rep['orphan']}")
        else:
            p.parse_args(["task", "--help"])
        return 0

    if args.cmd == "goal":
        if args.goal_cmd == "add":
            gl = g.goals.add(args.text)
            print(json.dumps(gl.to_dict(), ensure_ascii=False) if args.json else f"{gl.id}: {gl.text}")
        elif args.goal_cmd == "update":
            gl = g.goals.update(args.id, args.text)
            print(f"{gl.id}: {gl.text}")
        elif args.goal_cmd == "remove":
            print("removed" if g.goals.remove(args.id) else "not found")
        else:
            goals = g.goals.list()
            if args.json:
                print(json.dumps([x.to_dict() for x in goals], ensure_ascii=False))
            else:
                for x in goals:
                    print(f"{x.id}: {x.text}")
                print(f"\n{len(goals)} goal(s)")
        return 0

    if args.cmd == "bug":
        def _pb(it):
            if args.json:
                print(json.dumps(it.to_dict(), ensure_ascii=False))
            else:
                print(f"[{g.bugs.marker(it.status)}] {it.id}  {it.fm.get('title','')}  "
                      f"({it.status}, {it.fm.get('severity','')}, kind={it.fm.get('kind','')})")
        if args.bug_cmd == "new":
            _pb(g.bugs.create(title=args.title, severity=args.severity,
                              kind=args.kind, status=args.status))
        elif args.bug_cmd == "list":
            bugs = g.bugs.list(status=args.status)
            if args.json:
                print(json.dumps([b.to_dict() for b in bugs], ensure_ascii=False))
            else:
                for b in bugs:
                    _pb(b)
                print(f"\n{len(bugs)} bug(s)")
        elif args.bug_cmd == "update":
            _pb(g.bugs.update(args.id, status=args.status,
                              severity=args.severity, title=args.title))
        elif args.bug_cmd == "sync":
            print(json.dumps(g.bugs.sync(), ensure_ascii=False))
        else:
            p.parse_args(["bug", "--help"])
        return 0

    if args.cmd == "vault":
        if args.vault_cmd == "ingest":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
            n = g.vault.ingest(title=args.title, type=args.type, source=args.source,
                               tags=tags, ingestion_type=args.ingestion_type)
            print(json.dumps(n.to_dict(), ensure_ascii=False) if args.json
                  else f"ingested -> {n.rel}  tags={n.tags}")
        elif args.vault_cmd == "reindex":
            rep = g.vault.reindex()
            print(json.dumps(rep, ensure_ascii=False) if args.json
                  else f"reindexed: {rep['count']} note(s); {len(rep['tags'])} distinct tag(s)")
        elif args.vault_cmd == "lint":
            issues = g.vault.lint()
            if args.json:
                print(json.dumps(issues, ensure_ascii=False))
            else:
                for i in issues:
                    print(f"[{i['severity']}] {i['note']}: {i['issue']}")
                print(f"\n{len(issues)} issue(s)")
        else:
            notes = g.vault.list(type=getattr(args, "type", None))
            if args.json:
                print(json.dumps([n.to_dict() for n in notes], ensure_ascii=False))
            else:
                for n in notes:
                    print(f"{n.rel}  ({n.type})  tags={n.tags}")
                print(f"\n{len(notes)} note(s)")
        return 0

    if args.cmd == "inbox":
        rep = g.inbox.intake(dry_run=args.dry_run)
        if args.json:
            print(json.dumps(rep, ensure_ascii=False))
        elif rep["total"] == 0:
            print("inbox empty — nothing to intake")
        else:
            for c in rep["created"]:
                pfx = "[dry-run] would create" if rep["dry_run"] else "created"
                print(f"  {pfx}: {c['id']}  {c['title']}  (from {c['from']})")
            tail = " (dry-run: no files written)" if rep["dry_run"] else ""
            print(f"\nintake: {rep['tasks_ingested']} task(s), {rep['bugs_ingested']} bug(s){tail}")
        return 0

    if args.cmd == "doctor":
        only = [s.strip() for s in args.only.split(",")] if args.only else None
        rep = g.doctor.check(only=only)
        if args.json:
            print(json.dumps(rep, ensure_ascii=False))
        else:
            for s in rep["systems"]:
                sc = "-" if s["score"] is None else f"{s['score']}%"
                print(f"  [{s['status']:>7}] {s['name']:<10} {sc:>5}  ({s['passed']}/{s['passed'] + s['failed']})")
                for fail in s["failures"]:
                    print(f"      x {fail}")
            print(f"\nOVERALL: {rep['overall_score']}% functional "
                  f"({rep['systems_passing']}/{rep['systems_tested']} systems passing)")
        return 1 if (args.fail_below and rep["overall_score"] < args.fail_below) else 0

    if args.cmd == "validate":
        rep = g.validate.run(paths=args.paths or None, fix=args.fix)
        if args.json:
            print(json.dumps(rep, ensure_ascii=False))
        else:
            for v in rep["violations"]:
                mark = "fixed" if v["fixed"] else v["kind"]
                print(f"  [{mark:>7}] {v['item']} {v['field']:<11} {v['file']}")
                print(f"            {v['message']}")
            verb = "fixed" if args.fix else "found"
            print(f"\nvalidate: {rep['checked']} file(s) checked — "
                  f"{rep['errors']} error(s), {rep['fixable']} fixable ({rep['fixed']} {verb}), "
                  f"{rep['warnings']} warning(s)")
            if not rep["ok"]:
                print("  -> run `gald3r validate --fix` to normalize fixable findings")
        return 0 if rep["ok"] else 1

    if args.cmd == "platform":
        if args.platform_cmd == "status":
            rep = g.platform.status(platform=args.platform)
            if args.json:
                print(json.dumps(rep, ensure_ascii=False))
            else:
                for r in rep["rows"]:
                    tier = next((r[k] for k in r if "tier" in k.lower()), "")
                    extra = f"  {r['readiness']}" if r.get("readiness") else ""
                    print(f"  {r['platform']:<14} {tier}{extra}")
                tally = ", ".join(f"{k}={v}" for k, v in rep["summary"].items() if k != "total")
                print(f"\n{rep['summary'].get('total', 0)} platform(s): {tally}")
        else:
            p.parse_args(["platform", "--help"])
        return 0

    if args.cmd == "tier":
        if args.tier_cmd == "set":
            rep = g.tiers.set(args.tier)
            print(json.dumps(rep, ensure_ascii=False) if args.json
                  else f"tier: {rep['old']} -> {rep['new']}" + ("" if rep["changed"] else " (unchanged)"))
        else:
            rep = g.tiers.show()
            print(json.dumps(rep, ensure_ascii=False) if args.json
                  else f"tier: {rep['tier']} (position {rep['position'] + 1}/{len(rep['ladder'])}; ladder {rep['ladder']})")
        return 0

    if args.cmd in ("sync", "parity"):
        do_apply = args.cmd == "sync" and getattr(args, "apply", False)
        rep = g.sync.apply(platform=args.platform) if do_apply else g.sync.check(platform=args.platform)
        if args.json:
            print(json.dumps(rep, ensure_ascii=False))
        elif do_apply:
            for r in rep["platforms"]:
                print(f"  {r['platform']:<10} wrote {r['written']}, removed {r['removed']} (of {r['projected']})")
            print(f"\napplied: {rep['total_written']} written, {rep['total_removed']} removed")
        else:
            for r in rep["platforms"]:
                tag = ("in parity" if r["in_parity"]
                       else f"{len(r['missing'])} missing, {len(r['drift'])} drift, {len(r['extra'])} extra")
                print(f"  {r['platform']:<10} {tag}  (projected {r['projected']})")
            verdict = "IN PARITY" if rep["in_parity"] else f"{rep['total_gaps']} gap(s)"
            print(f"\n{verdict}")
        return 0 if (do_apply or rep.get("in_parity")) else 1

    if args.cmd == "release":
        def _pr(it):
            print(json.dumps(it.to_dict(), ensure_ascii=False) if args.json
                  else f"{it.id}  {it.fm.get('title','')}  v{it.fm.get('version','?')}  "
                       f"({it.status}, target={it.fm.get('target_date','—')})")
        if args.release_cmd == "new":
            _pr(g.release.create(title=args.title, version=args.version,
                                 target_date=args.target_date, status=args.status))
        elif args.release_cmd == "ship":
            _pr(g.release.ship(args.id, version=args.version))
        elif args.release_cmd == "roadmap":
            road = g.release.roadmap()
            if args.json:
                print(json.dumps([r.to_dict() for r in road], ensure_ascii=False))
            else:
                for r in road:
                    _pr(r)
                nxt = g.release.next_target_date()
                print(f"\n{len(road)} upcoming; next target ~ {nxt or 'n/a'}")
        else:
            rels = g.release.list()
            if args.json:
                print(json.dumps([r.to_dict() for r in rels], ensure_ascii=False))
            else:
                for r in rels:
                    _pr(r)
                print(f"\n{len(rels)} release(s)")
        return 0

    if args.cmd == "workspace":
        try:
            ws = g.workspace
        except PermissionError as e:
            print(json.dumps({"error": str(e)}) if args.json else f"refused: {e}")
            return 2
        if args.workspace_cmd == "validate":
            errs = ws.validate_manifest()
            print(json.dumps({"valid": not errs, "errors": errs}, ensure_ascii=False) if args.json
                  else ("manifest valid" if not errs else "INVALID:\n  " + "\n  ".join(errs)))
        elif args.workspace_cmd == "conflicts":
            conf = ws.conflicts()
            if args.json:
                print(json.dumps([c.to_dict() for c in conf], ensure_ascii=False))
            else:
                for c in conf:
                    print(f"[CONFLICT] {c.from_project} | {c.summary}")
                print(f"\n{len(conf)} blocking conflict(s)")
        elif args.workspace_cmd == "inbox-add":
            it = ws.add_item(args.section, args.from_project, args.summary)
            print(json.dumps(it.to_dict(), ensure_ascii=False) if args.json
                  else f"added to [{it.section}]: {it.summary}")
        else:
            print(json.dumps(ws.status(), ensure_ascii=False) if args.json
                  else "  ".join(f"{k}={v}" for k, v in ws.status().items()))
        return 0

    if args.cmd == "prompt":
        lib = g.prompts
        if args.prompt_cmd == "get":
            values = dict(kv.split("=", 1) for kv in args.input if "=" in kv)
            try:
                text = lib.render(args.id, **values)
            except (KeyError, ValueError) as e:
                print(json.dumps({"error": str(e)}) if args.json else f"error: {e}")
                return 2
            print(json.dumps({"id": args.id, "text": text}, ensure_ascii=False)
                  if args.json else text)
        else:
            assets = lib.list(kind=getattr(args, "kind", None))
            if args.json:
                print(json.dumps([a.meta() for a in assets], ensure_ascii=False))
            else:
                for a in assets:
                    inp = f"  inputs={a.inputs}" if a.inputs else ""
                    print(f"{a.id:28} [{a.kind}]  {a.title}{inp}  ← {a.source}")
                print(f"\n{len(assets)} prompt asset(s)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
