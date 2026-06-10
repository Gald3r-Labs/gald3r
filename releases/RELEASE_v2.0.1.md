# gald3r v2.0.1

**Released:** 2026-06-10
**Type:** Patch — copyright transfer, org migration, workspace bug fix

---

## Headline

gald3r is now published under **Gald3r Labs LLC** — and workspace role detection actually works.

---

## What's in 2.0.1

- **Gald3r Labs LLC** — all repository licenses updated to reflect company formation and IP
  transfer. Nothing changes for users; gald3r stays open-source under FSL-1.1.

- **All platform repos now get release notifications** — previously only the flagship `gald3r`
  repo triggered a GitHub Release (with watcher notifications) on each publish. Now all 34+
  platform repos receive a tagged release automatically. If you watch any `gald3r_platform_*`
  repo, you'll get notified on every new version.

- **BUG-128 fixed — workspace role was always "standalone"** — a misspelled dict key
  (`pcac_relationship` instead of `wpac_relationship`) caused `workspace.py` to silently ignore
  your WPAC topology configuration. If you use parent/child/sibling project linking and
  `@g-workspace STATUS` was showing `standalone`, upgrade to 2.0.1.

---

## Why upgrade

If you use WPAC workspace coordination (`@g-workspace`, parent/child project topologies),
**you should upgrade** — workspace role detection was broken in 2.0.0 and is fixed here.

---

_See [CHANGELOG.md](../CHANGELOG.md) for the full technical list._
