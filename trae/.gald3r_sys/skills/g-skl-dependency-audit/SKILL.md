---
name: g-skl-dependency-audit
description: Scan package files for outdated or vulnerable dependencies. Generates a severity-ranked report with CVE references and upgrade commands. Supports Python (requirements.txt/pyproject.toml), JavaScript/Node (package.json/package-lock.json), and Rust (Cargo.toml/Cargo.lock).
token_budget: medium
subsystem_memberships: [SECURITY_AND_COMPLIANCE, BUG_AND_QUALITY]
---
# g-skl-dependency-audit

**Activate for**: `@g-dependency-audit`, "audit deps", "check for vulnerable packages", "outdated dependencies", "CVE scan", "is this package safe", "npm audit", "pip audit", "cargo audit".

---

## Backends by Ecosystem

| Ecosystem | Primary Tool | Fallback |
|-----------|-------------|----------|
| Python | `pip-audit` | `safety check` |
| JavaScript / Node | `npm audit` / `pnpm audit` | `yarn audit` |
| Rust | `cargo audit` | Manual advisory check |
| Multi | Run all applicable backends | — |

---

## Step 1: Detect Project Ecosystems

```
Find package files in the working directory:
  Python:  requirements.txt, requirements*.txt, pyproject.toml, setup.cfg
  Node:    package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
  Rust:    Cargo.toml, Cargo.lock
```

For each detected ecosystem, run Step 2. Skip ecosystems with no lock file
(advisory scans on non-locked deps are unreliable).

---

## Step 2: Run Audit Commands

### Python
```bash
# Primary: pip-audit (fast, OSV + PyPI Advisory DB)
pip-audit --output=json 2>/dev/null
# or for pyproject.toml:
pip-audit -r requirements.txt --output=json
# Fallback if pip-audit unavailable:
safety check --output=json 2>/dev/null
```

### JavaScript
```bash
# npm
npm audit --json 2>/dev/null
# yarn
yarn audit --json 2>/dev/null
# pnpm
pnpm audit --json 2>/dev/null
```

### Rust
```bash
# Requires: cargo install cargo-audit
cargo audit --json 2>/dev/null
```

**If tools are unavailable**: report which tools are missing and provide install commands. Do not silently skip.

---

## Step 3: Parse and Rank Findings

Severity order (highest first): **Critical → High → Moderate/Medium → Low → Info**

For each vulnerability found:
- Package name and affected version range
- CVE ID(s) or advisory ID (GHSA-*, PYSEC-*, RUSTSEC-*)
- Severity rating (CVSS score if available)
- Fixed version (the exact version to upgrade to)
- Upgrade command

---

## Step 4: Generate Report

### Header
```
## Dependency Audit Report
Date: YYYY-MM-DD
Project: <name>
Ecosystems scanned: Python / Node / Rust (list those found)
Tool(s): pip-audit 2.x / npm audit / cargo audit
```

### Summary Table
```
| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Moderate | N     |
| Low      | N     |
| Total    | N     |
```

### Findings (ordered by severity)
```
### VULN-001 [Critical] — <package>@<version>
- CVE: CVE-YYYY-NNNNN
- Advisory: GHSA-xxxx-xxxx-xxxx
- Issue: <one-line description>
- Affected: <package>@<bad_range>
- Fixed in: <package>@<fixed_version>
- Upgrade: pip install "<package>>=<fixed_version>"
```

### Clean Bill
If zero vulnerabilities found:
```
✓ No known vulnerabilities found in <N> packages scanned.
```

---

## Step 5: Offer Actions

- Generate `pip install -U package1 package2 ...` bulk upgrade command
- Flag packages with no fixed version available (user must decide: remove, replace, accept risk)
- For packages where upgrade is a major version bump: note breaking changes risk

---

## Integration with g-go-review

When invoked as part of `g-go-review`:
1. Run dependency audit on any new `requirements.txt`, `package.json`, or `Cargo.toml` added in the change set.
2. If any **High** or **Critical** CVEs are found in NEW deps: flag as review FAIL.
3. Pre-existing vulnerabilities → report but do not fail (those belong in a separate BUG entry).

---

## Tool Install Commands

```bash
# Python
pip install pip-audit
# or: pip install safety

# Node (built-in to npm >= 6)
npm install -g npm  # update to latest

# Rust
cargo install cargo-audit
```
