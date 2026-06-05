"""CLI surface: `gald3r task new|list|update|sync`, `gald3r mcp`, `gald3r --version`.

Thin — every command calls the same `Gald3r` core the MCP/HTTP surfaces use.
Stdlib argparse only (zero deps), so it runs anywhere uv puts a Python.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from gald3r import __version__
from gald3r.core import Gald3r


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


def main(argv: Optional[List[str]] = None) -> int:
    _ensure_utf8()
    p = argparse.ArgumentParser(prog="gald3r", description="gald3r engine CLI")
    p.add_argument("--version", action="version", version=f"gald3r {__version__}")
    p.add_argument("--root", default=None, help="project root (defaults to nearest .gald3r/)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
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

    sub.add_parser("mcp", help="run the MCP (stdio) server")

    args = p.parse_args(argv)
    if args.cmd is None:
        p.print_help()
        return 0

    if args.cmd == "mcp":
        from gald3r.adapters import mcp as mcp_adapter
        mcp_adapter.run(root=args.root)
        return 0

    g = Gald3r(root=args.root)

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
