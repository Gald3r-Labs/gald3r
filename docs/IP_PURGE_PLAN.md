# IP Purge Plan — `project_template/.gald3r_sys` (BUG-639)

> Status as of this writing (branch `reconcile/v4`, built on commit `2d1c871`): the **forward
> purge is done**. `project_template/.gald3r_sys/` is removed from the current tree, removed
> from tracking, and guarded by `.gitignore`. This document is about the **remaining decision**:
> whether the content also needs to be scrubbed from git **history**, and if so, how.
>
> This plan describes options and exact commands. **Nothing in this document has been
> executed.** A history rewrite is destructive and requires a force-push; only the repo owner
> should decide to run it, and only the owner (or someone they explicitly authorize) should run
> the force-push itself.

## 1. What was purged, and what's left in history

`git log --oneline --all -- project_template/.gald3r_sys` shows **16 commits** touching this
path, going back to the template's first release:

```
f31d520 release: v2.0.1
1f2cf2d chore: release v2.0.0 -- full platform parity sync + template restructure
41a015b feat(template): initial release — gald3r v1.10.0
... (13 more commits between v1.10.0 and the 2026-08-02 purge)
```

Commit `2d1c871` (`chore(template): purge project_template/.gald3r_sys -- retired
compiled-into-binary IP (BUG-639)`) removes all 328 files (45,320 lines) from the tree **as of
that commit forward**. It does **not** remove them from the 16 prior commits — anyone who has
ever cloned this repo, or who clones it today and walks history (`git log -p`, `git checkout
<old-sha>`), can still retrieve every file.

**Content that is still reachable in history**: `project_types/*.yaml` + `_schema.yaml`
(validation IP), `skill_packs/` (marketplace-gate payload per T172/T288), `scripts/*.py`,
`_platform_capabilities.json`, an `engine/README` stub. This is the exact material the
2026-07-14 owner QA NO-GO (T56) designated as compiled-into-binary IP.

## 2. Exposure already accepted (facts, not a recommendation)

- The content was live and trackable on GitHub for **~3–5 weeks** before the forward purge
  (first shipped in the wholesale P5 cutover; the parity harness checked the generated
  `platforms/` overlays but nobody purged this specific payload — see BUG-639's own
  description for the mechanism).
- The repo is **public**, has **4 known forks** (`broisonshop-create/gald3r`,
  `Haizard/gald3r`, `KingofPoly/gald3r`, `louisklinogo/gald3r` — each a full clone of history
  up to whenever they forked, so each may already carry the `.gald3r_sys` commits).
- GitHub clone-traffic API reports **94 clones / 37 unique cloners** over the trailing 14 days
  (2026-07-18 through 2026-07-31) — consistent with the project's own prior finding that clone
  counts on these repos run heavily bot-dominated (a ~2.5:1 clone:unique ratio here, less
  extreme than the ~179:1 seen on `gald3r_core`, so treat this one as more plausibly
  including a real minority of human clones).
- **A history rewrite does not undo any of the above.** Anything already cloned, forked, or
  cached (including GitHub's own CDN/API caches, third-party mirrors, and search-engine
  crawlers) keeps a copy regardless of what this repo's `main` branch looks like afterward.
  Rewriting history only prevents *future* clones from receiving the content forward.

## 3. Option A — Forward-purge only (no history rewrite) — RECOMMENDED default

Keep `2d1c871` as-is. Do nothing further to history.

**Pros**: zero risk to the 4 forks, any open PRs, or anyone's existing local clone; no
force-push; no coordination burden. **Cons**: the content remains permanently retrievable by
anyone willing to `git log -p` or check out an old commit — "removed" is honest, "gone" is not.

This is almost certainly the right call if the actual sensitivity of `project_types` validation
YAML / `skill_packs` / small helper `scripts/*.py` is closer to "internal packaging detail" than
"the trade secret that makes gald3r work" — the compiled binary (`gald3r_core`) is what
performs the deterministic logic today; this was schema/script *scaffolding* around it, already
3–5 weeks stale.

## 4. Option B — History rewrite (git filter-repo)

If the owner decides the exposure window is unacceptable regardless of how mild the content is,
here is the exact, tested-pattern command. **Run this on a fresh mirror clone, never on the
working checkout in use for `reconcile/v4`** — `filter-repo` rewrites every ref and expects a
disposable clone.

```bash
# 1. Fresh bare mirror clone (never the live working checkout)
git clone --mirror https://github.com/Gald3r-Labs/gald3r.git gald3r-history-scrub.git
cd gald3r-history-scrub.git

# 2. Install git-filter-repo if not already available
#    (pip install git-filter-repo, or see https://github.com/newren/git-filter-repo)

# 3. Strip the path from every commit in every ref (branches + tags)
git filter-repo --path project_template/.gald3r_sys --invert-paths --force

# 4. Re-add the origin remote (filter-repo removes it as a safety measure)
git remote add origin https://github.com/Gald3r-Labs/gald3r.git

# 5. Force-push EVERY rewritten ref (branches and tags)
git push origin --force --all
git push origin --force --tags
```

### Consequences of running Option B (read before deciding)

1. **Every commit SHA after the earliest touched commit changes.** `f31d520`/`1f2cf2d`/
   `41a015b` and all 13 other history-touching commits, plus every commit downstream of them
   (which is effectively the entire branch, since these are some of the earliest commits) get
   new hashes. `main`'s current tip `2d1c871` becomes a different SHA post-rewrite.
2. **Force-push is mandatory** (`--force --all --tags`) — a normal push will be rejected because
   history diverged. This is exactly the class of operation `g-rl-33`'s Autonomous Push Gate and
   this task's own HARD RULES require explicit, direct owner action for; no agent should run
   the force-push.
3. **The 4 known forks are NOT automatically updated.** Each fork keeps the old history
   permanently unless its owner independently re-syncs or re-forks. If any of those forks are
   later merged back via PR, GitHub will show the full old history (including `.gald3r_sys`)
   reappearing in the merge unless that PR is explicitly rebased onto the new, rewritten history
   first.
4. **Any existing local clone (all 37 unique cloners in the last 14 days, plus anyone earlier)**
   will fail to `git pull` cleanly after the rewrite — they'll see a non-fast-forward error and
   need to re-clone or hard-reset to the new history.
5. **Open PRs, issues linking to specific commit SHAs, and any external documentation/blog posts
   citing a `Gald3r-Labs/gald3r@<sha>` permalink** break silently (the link either 404s or
   resolves to an unrelated/nonexistent commit).
6. **The content is still not "gone."** Per Section 2, anything already fetched by a fork, a
   clone, or a crawler before the rewrite keeps its copy. A history rewrite only stops the
   content from being served to *new* requests against this repo's own refs.

### Decision inputs for the owner

- Real sensitivity of the purged content vs. cost of the rewrite (four forks orphaned, all
  existing clones broken, any external links to old SHAs broken).
- Whether the four known forks are worth contacting directly (asking them to delete/re-fork)
  as a supplement to a history rewrite — a rewrite alone does not reach them.
- Whether this is worth doing now vs. bundling it with some other planned disruptive event
  (e.g., a `v5` line, if one is ever planned, is a more natural place to reset history than a
  history-only rewrite with no other visible change).

## 5. What this task did NOT do

- Did not run `git filter-repo` or any history-rewriting tool.
- Did not force-push anything, or push anything at all — see the handoff push plan in this
  session's report for the exact commands the **owner** would run.
- Did not contact any of the 4 forks.

Everything above is a plan for the owner to approve or decline; `reconcile/v4`'s own commits
only perform the forward-looking, non-destructive purge already reflected in `2d1c871` plus this
document.
