---
name: g-skl-security-scan
description: SAST-style static analysis for hardcoded secrets, injection patterns, insecure deserialization, path traversal, and other critical vulnerabilities. Severity-ranked findings with line references and remediation guidance. Includes two-phase threat-model + diff-revalidation mode (T1167) for use as the post-implementation gate in g-go-review.
token_budget: medium
subsystem_memberships: [BUG_AND_QUALITY, SECURITY_AND_COMPLIANCE]
---
# g-skl-security-scan

**Activate for**: `@g-security-scan`, "scan for secrets", "check for injection", "security analysis", "hardcoded credentials", "SAST", "find vulnerabilities", "pentest prep", "pre-deploy security check", "two-phase security scan", "threat model from diff".

Note: This skill complements `g-skl-code-review` (which has an OWASP checklist). Use `g-security-scan` when you want a **focused security-only deep scan** on specific files or after a major change.

## When to invoke

| Trigger | Mode |
|---------|------|
| `@g-skl-security-scan` (no args) on a checked-out branch with diff vs `HEAD~1` | **Two-Phase Mode (T1167)** — recommended default |
| `@g-skl-security-scan files=<glob>` or post-deploy hardening | **Single-Pass SAST Mode** — original Scan Passes 1–6 below |
| Auto-invoked from `g-go-review` post-implementation gate when changed files include anything beyond `*.md` / `docs/**` | **Two-Phase Mode (T1167)** |
| User says "scan with threat model", "phase-1 + phase-2 review", "deep security gate" | **Two-Phase Mode (T1167)** |

Both modes write to `.gald3r/reports/security/`. Two-Phase Mode produces TWO artifacts (`threat_model.md` + `security_report_*.md`); Single-Pass Mode produces ONE (`security_report_*.md`).

---

## Scope Declaration

Before scanning, confirm scope:
- Files/directories to scan (default: all modified files in current PR/commit)
- Language(s) detected
- Severity threshold (default: report Critical + High; flag Moderate)

---

## Scan Pass 1: Secret Detection

### Patterns to flag (Critical — always block)

| Pattern | Example | Action |
|---------|---------|--------|
| API keys | `OPENAI_API_KEY = "sk-..."` | Flag, redact, move to env var |
| Private keys | `-----BEGIN RSA PRIVATE KEY-----` | Flag immediately |
| AWS keys | `AKIA[0-9A-Z]{16}` | Flag, rotate |
| DB passwords | `password = "real_password"` | Flag, move to vault |
| JWT secrets | `secret = "my-jwt-secret"` | Flag |
| GitHub tokens | `ghp_[A-Za-z0-9]{36}` | Flag, rotate |

### Annotate findings
```
[CRITICAL] Hardcoded API key
  File: src/config.py:42
  Line: OPENAI_KEY = "sk-proj-abc123..."
  Fix:  Replace with: OPENAI_KEY = os.getenv("OPENAI_API_KEY")
        Remove value from git history if already committed.
```

---

## Scan Pass 2: Injection Vulnerabilities

### SQL Injection (High)
Look for: string concatenation or f-strings in SQL queries.
```python
# BAD:
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# BAD:
cursor.execute("SELECT * FROM " + table_name + " WHERE id = " + str(uid))

# GOOD (parameterized):
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Command Injection (High)
Look for: `subprocess`, `os.system`, `eval`, `exec` with user-controlled data.
```python
# BAD:
os.system(f"grep {user_input} /var/log/app.log")
subprocess.run(user_cmd, shell=True)

# GOOD:
subprocess.run(["grep", user_input, "/var/log/app.log"], shell=False)
```

### SSTI / Template Injection (High)
Look for: Jinja2/Mako `render_template_string` or `Template(user_input)`.

### XSS (Moderate for API/backend; High for SSR)
Look for: unescaped user content in HTML responses, `innerHTML =`, `dangerouslySetInnerHTML`.

---

## Scan Pass 3: Insecure Deserialization

### Python (High)
```python
# BAD:
data = pickle.loads(user_bytes)
data = yaml.load(user_str)   # without Loader=yaml.SafeLoader

# GOOD:
data = json.loads(user_str)
data = yaml.safe_load(user_str)
```

### JavaScript (High)
```javascript
// BAD:
eval(userInput)
new Function(userInput)()
JSON.parse(userInput)  // OK but validate schema after
```

---

## Scan Pass 4: Path Traversal

Look for: user-controlled values used in file path construction without sanitization.
```python
# BAD:
filepath = f"/app/uploads/{filename}"
open(filepath, "r")

# GOOD:
safe_path = os.path.join("/app/uploads", os.path.basename(filename))
open(safe_path, "r")
```

---

## Scan Pass 5: Auth & Session Issues

- [ ] Routes that modify state lack authentication decorator
- [ ] JWT decode without signature verification (`algorithms=["none"]`)
- [ ] Session cookies missing `HttpOnly`, `Secure`, `SameSite` flags
- [ ] Rate limiting absent on auth endpoints (`/login`, `/reset-password`)
- [ ] CORS `allow_origins="*"` on non-public APIs

---

## Scan Pass 6: Dependency-Level (Quick)

Run `g-skl-dependency-audit` for a full dep scan. Here, just flag:
- Any `import` of packages known to be deprecated/CVE-riddled (e.g., `pyjwt < 2.0`, `urllib3 < 1.26`)
- `requirements.txt` with unpinned `*` or `>=` without upper bound

---

## Report Format

```
## Security Scan Report
Date: YYYY-MM-DD
Files scanned: N
Language(s): Python / TypeScript / etc.
Tool: g-skl-security-scan (manual SAST pattern matching)

### Summary
| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Moderate | N     |

### Findings

#### [CRITICAL-001] Hardcoded API Key
- **File**: src/config.py:42
- **Pattern**: OPENAI_KEY = "sk-proj-..."
- **Risk**: Credential exposure in repository
- **Fix**: Move to environment variable. If committed: rotate key immediately, use `git filter-repo` to scrub.

#### [HIGH-001] SQL Injection
- **File**: api/users.py:87
- **Pattern**: f"SELECT * FROM users WHERE name = '{name}'"
- **Risk**: Database exfiltration/manipulation
- **Fix**: Use parameterized query: `cursor.execute("... WHERE name = %s", (name,))`
```

### Clean Bill
```
✓ No critical or high-severity findings in N files scanned.
  (N moderate findings — see below for details)
```

---

## False Positive Protocol

If a finding is intentional (e.g., test fixture with fake key):
- Add `# nosec: test-only fake credential` comment above the line
- Security scan will skip annotated lines in future runs

---

## Two-Phase Mode (T1167)

Two-Phase Mode is the recommended path when scanning a fresh implementation. It models Vercel's "deep-scan" gate (V34 harvest, hTpHmLFXBrc): Phase 1 derives a threat model from the diff so Phase 2 can do context-aware revalidation that catches second-order vulnerabilities the single-pass SAST scan misses.

### Activation triggers

Run Two-Phase Mode when **any** of the following applies:

- The skill is invoked from `g-go-review` Step S (post-implementation gate)
- `@g-skl-security-scan` is called on a checked-out branch and `git diff HEAD~1..HEAD` is non-empty for non-doc paths
- The active task's frontmatter declares `requires_security_scan: true`
- The user explicitly asks for "two-phase scan", "threat model", or "phase-1 + phase-2"

Skip Two-Phase Mode (fall back to Single-Pass SAST below) when:

- Changed paths are **all** `*.md`, `docs/**`, `CHANGELOG.md`, `README.md`, `LICENSE`, or whitespace-only
- The git diff against `HEAD~1` is empty (use `--cached`, `--staged`, or `HEAD~2..HEAD` as a manual override)
- The skill is called with `--single-pass` argument

### Output locations

```
.gald3r/reports/security/
├── threat_model.md                              # Phase 1 output (overwritten per run)
└── security_report_YYYYMMDD_HHMMSS.md           # Phase 2 output (timestamped, never overwritten)
```

Timestamp format: `YYYYMMDD_HHMMSS` (UTC). Get via:

```powershell
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
```

```bash
ts=$(date -u +'%Y%m%d_%H%M%S')
```

If `.gald3r/reports/security/` does not exist, create it.

### Phase 1 — Threat model from diff

**Goal**: enumerate what the diff actually changed and what attack surfaces those changes open.

**Algorithm**:

1. Resolve the diff range. Default `git diff HEAD~1..HEAD --name-status`; if the run is invoked pre-checkpoint, fall back to `git diff --cached` then `git diff HEAD`. Record which range was used.
2. For each changed file (status `A`/`M`/`R`; skip `D` deletes for Phase 2 but note them in the threat model):
   - Capture path, lines added/removed (`git diff --numstat`), language (by extension).
   - Extract changed function signatures via regex on diff hunks (do not load the whole file unless needed):
     - Python: `^(\+|-)\s*(async\s+)?def\s+([A-Za-z_]\w*)\s*\(`
     - JS/TS: `^(\+|-).*\b(function|const|let|var)\s+([A-Za-z_]\w*)\s*[=(]` plus `^(\+|-).*=>\s*\{`
     - Go: `^(\+|-)\s*func\s+(\([^)]*\)\s+)?([A-Za-z_]\w*)\s*\(`
     - Java/C#: `^(\+|-).*\b(public|private|protected|internal)\s+[\w<>\[\]]+\s+([A-Za-z_]\w*)\s*\(`
     - Rust: `^(\+|-)\s*(pub\s+)?(async\s+)?fn\s+([A-Za-z_]\w*)\s*[<(]`
     - SQL: `^(\+|-)\s*CREATE\s+(OR\s+REPLACE\s+)?(PROCEDURE|FUNCTION|TRIGGER)\s+([A-Za-z_]\w*)`
   - Classify the file by surface heuristic:

     | Surface | Signal (regex / keyword anywhere in changed hunks) |
     |---------|----------------------------------------------------|
     | `auth` | `login`, `signin`, `jwt`, `token`, `password`, `passwd`, `bcrypt`, `oauth`, `session`, `csrf` |
     | `api` | `@app.route`, `@router.`, `fastapi`, `flask`, `express`, `app.get\|post\|put\|delete`, `Controller`, `Handler` |
     | `db` | `cursor.execute`, `prisma.`, `sequelize`, `mongoose`, `sql`, `query(`, `INSERT\|UPDATE\|DELETE\|SELECT` |
     | `fs` | `open(`, `fs.read`, `pathlib`, `os.path.join`, `Path(`, `read_file`, `write_file` |
     | `exec` | `subprocess`, `os.system`, `eval`, `exec(`, `shell=True`, `child_process`, `spawn` |
     | `deser` | `pickle`, `yaml.load`, `unmarshal`, `JSON.parse(unsafe)`, `eval(`, `Function(` |
     | `crypto` | `aes`, `rsa`, `hash`, `hmac`, `random`, `Math.random`, `crypto.` |
     | `net` | `http.get`, `requests.`, `fetch(`, `axios`, `urlopen`, `socket`, `cors` |
     | `template` | `render_template_string`, `Mako`, `Jinja2`, `dangerouslySetInnerHTML`, `innerHTML`, `eval(template` |
     | `config` | filenames matching `.env`, `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `secrets.json` |

3. Produce the **top 5 attack surfaces** by aggregating per-file surfaces. Tie-break by (number of changed files) → (lines added).

4. Write `threat_model.md` overwriting any prior copy:

```markdown
# Threat Model — T{task_id|"adhoc"}
Generated: YYYY-MM-DD HH:MM UTC
Diff range: git diff HEAD~1..HEAD   (or fallback used)
Files in diff: N        (added: A, modified: M, renamed: R, deleted: D)
Lines added: +X / removed: -Y
Languages: python, typescript, ...

## Changed Files & Signatures
| File | Surface | Lines Δ | Changed Signatures |
|------|---------|---------|--------------------|
| src/auth/login.py | auth, db | +24 / -3 | login(), verify_password() |
| api/users.py     | api, db  | +12 / -0 | get_user(), search_users() |
| ...

## Top Attack Surfaces (max 5)
1. **Authentication boundary** — `src/auth/login.py` adds new password verification logic.
   Risks: timing-attack-friendly compare, weak hashing, missing rate limit.
2. **SQL data access** — `api/users.py` adds `search_users(q)` reaching the DB layer.
   Risks: SQLi via `q`, broken access control, info disclosure.
3. **File I/O** — `lib/uploads.py` accepts user-supplied filename in `save_file()`.
   Risks: path traversal, MIME confusion, symlink follow.
4. **Shell execution** — `tools/run_job.py` adds `subprocess` call with config-driven args.
   Risks: command injection if config is user-influenced.
5. **Deserialization** — `cache/load.py` calls `pickle.loads` on cache-store bytes.
   Risks: RCE if the cache is writable by lower-privileged code.

## Phase 2 Plan
Phase 2 will revalidate each changed file with this threat model as the lens.
Findings are graded Critical / High / Medium / Low / Info per the rubric in g-skl-security-scan.
```

5. If the diff is empty or doc-only, write a short `threat_model.md` saying so and EXIT (no Phase 2, no findings, exit code 0).

### Phase 2 — Per-file revalidation against the threat model

**Goal**: for each changed file, ask "given the threat model, is this file vulnerable?" and produce severity-graded findings.

**Algorithm**:

1. For each non-deleted changed file:
   - Load the **full file contents** at HEAD (not just the diff hunks). The threat model context applies to the full surface.
   - Run the **Single-Pass SAST passes (1–6)** below against the file as a baseline.
   - Apply the threat-model-aware secondary checks:

     | Surface flagged in threat model | Secondary checks applied to file |
     |---------------------------------|----------------------------------|
     | `auth` | constant-time comparison (`hmac.compare_digest` / `crypto.timingSafeEqual`); password hashing algo (bcrypt/argon2 only); JWT `algorithms=["none"]` rejection; rate-limit decorator presence; CSRF token on state-changing routes |
     | `api` | authentication decorator on every state-changing route; CORS `allow_origins` not `*` for non-public; input validation library on body parsing; rate limiting on auth/reset endpoints |
     | `db` | parameterized queries only (no f-string / concat into SQL); ORM safe-mode (no raw concat); least-privilege DB role implied; sensitive cols not logged |
     | `fs` | `os.path.basename` / `os.path.normpath` + allowlist directory; symlink resolution check; absolute-vs-relative discipline; max-upload-size check |
     | `exec` | `shell=False` and list args only; no string concat to command line; allowlist of allowed executables; arg validation |
     | `deser` | no `pickle.loads`, `yaml.load` (without `SafeLoader`), `Function()`, `eval()`; replace with `json.loads` / `yaml.safe_load` |
     | `crypto` | no MD5/SHA1 for auth or integrity; key length >= 256 for symmetric; CSPRNG (`secrets`, `crypto.randomBytes`) not `random` / `Math.random`; IV/nonce uniqueness |
     | `net` | TLS verify enabled (no `verify=False`); SSRF allowlist on outbound URL; URL whitelist for redirects; `Content-Security-Policy` on HTML responses |
     | `template` | escaping enabled by default; no `render_template_string` with user input; no `dangerouslySetInnerHTML` without sanitizer |
     | `config` | secret values not committed (cross-check with Pass 1); production defaults safe (no `DEBUG=true`, no `*` CORS) |

   - **Cross-file second-order checks** (only when Phase 1 identified ≥2 cooperating surfaces, e.g., `api` + `db`):
     - Tainted-flow heuristic: a value flowing from `request.*` / `req.body` / `params.*` into a function flagged on the `db` / `exec` / `fs` surface without going through a validator (`validate_*`, `schema.parse`, `pydantic`, `zod`, `joi`) is a **High** finding.
     - Annotate with `[XF-NNN]` (cross-file) instead of single-file `[CRITICAL/HIGH/MEDIUM/...]` prefixes.

2. **Severity grading rubric** (Phase 2 normalises every finding to this scale):

   | Severity | Definition | Examples | Blocks `[🔍] → [✅]`? |
   |----------|------------|----------|------------------------|
   | **Critical** | Direct, exploitable, no auth required | Hardcoded production credential; unsanitized `eval(user_input)`; SQLi on unauthenticated endpoint; RCE via `pickle.loads(network_bytes)` | **YES — hard block** |
   | **High** | Exploitable but requires some context (auth, specific input) | SQLi behind auth; path traversal in an authenticated upload; weak hashing (MD5) for new passwords; `algorithms=["none"]` JWT | **YES — hard block** |
   | **Medium** | Real risk but mitigated by defense-in-depth, or limited blast radius | Missing rate limit on auth route; CSRF gap on minor mutation; HTTPS-only cookie flag missing; `*` CORS on dev-only route | No — BUG entry only |
   | **Low** | Best-practice gap, hard to exploit | Outdated TLS cipher preference; verbose error message; non-constant-time string compare on a non-secret | No — note in report |
   | **Info** | Informational, no immediate action | "Endpoint is publicly readable by design"; "Logger does not redact PII but no PII observed" | No — note in report |

3. **False-positive waivers**:
   - A line annotated with `# nosec: <justification>` / `// nosec: <justification>` / `-- nosec: <justification>` is waived.
   - A line annotated with `# security-exempt: <reason>` is waived.
   - A waiver must include human-readable justification (≥ 4 words). Empty waivers are NOT honoured.

### Phase 2 report format

Write `security_report_YYYYMMDD_HHMMSS.md`:

```markdown
# Security Scan Report — T{task_id|"adhoc"}
Generated: YYYY-MM-DD HH:MM UTC
Mode: two-phase (T1167)
Threat model: .gald3r/reports/security/threat_model.md
Diff range: git diff HEAD~1..HEAD
Files analysed: N
Languages: python, typescript

## Summary
| Severity | Count |
|----------|-------|
| Critical | C     |
| High     | H     |
| Medium   | M     |
| Low      | L     |
| Info     | I     |

**Gate verdict**: BLOCK / PASS
(BLOCK when Critical > 0 OR High > 0; otherwise PASS.)

## Findings

### [CRITICAL-001] Hardcoded API key
- **File**: src/config.py:42
- **Surface**: config / auth (from threat model)
- **Pattern**: `OPENAI_KEY = "sk-proj-abc..."`
- **Risk**: Credential exposure; rotation required
- **Fix**: Read from `os.environ["OPENAI_API_KEY"]`; remove value from git history if committed.
- **Phase-1 link**: Surface #1 (Configuration secrets)

### [HIGH-001] SQL injection in search_users
- **File**: api/users.py:87
- **Surface**: api + db (cross-file, see XF-001)
- **Pattern**: `f"SELECT * FROM users WHERE name LIKE '%{q}%'"`
- **Risk**: Tainted `q` flows from `request.args.get("q")` to raw SQL.
- **Fix**: Use parameterized query: `cursor.execute("... LIKE %s", (f"%{q}%",))`.
- **Phase-1 link**: Surface #2 (SQL data access)

### [XF-001] Tainted flow: request.args → cursor.execute
- **Path**: api/users.py:75 → api/users.py:87 (no validator between)
- **Risk**: Combined with [HIGH-001]; multiple endpoints affected.

### [MEDIUM-001] ...
### [LOW-001] ...
### [INFO-001] ...

## Clean files
- src/utils/helpers.py — no findings
- lib/format.py — no findings

## Waivers honoured
- src/test/fixtures.py:12 — `# nosec: test-only fake credential`
```

### BUGS.md auto-create rule (Critical / High only)

When Phase 2 produces any **Critical** or **High** finding, the skill MUST file each one as a BUG entry via the `g-skl-bugs` `REPORT BUG` operation. Medium / Low / Info findings are NOT auto-filed (they remain in the security report; humans may file manually).

For each Critical/High finding:

1. Title: `[Security] {finding_short_title}` (e.g. `[Security] SQL injection in search_users`)
2. Severity: map Phase 2 severity → BUG severity:
   - Critical → `critical`
   - High → `high`
3. Body: copy the finding's File, Surface, Pattern, Risk, Fix lines verbatim.
4. Pass `--no-task` only when the active task's frontmatter declares `requires_security_scan: true` AND the run is from `g-go-review` Step S (the task itself will fail review, so a paired fix task is redundant). Otherwise allow `g-skl-bugs` to auto-spawn the fix task (its default behavior for high/critical).
5. Cross-link: append `bug_link: BUG-{id}` to the finding block in the security report after `g-skl-bugs` returns the new bug ID.

This rule is intentionally narrow — only Critical/High auto-file, because those are the same severities that hard-block the `[🔍] → [✅]` transition (see g-go-review Step S below). Medium and lower findings would generate BUGS.md noise without blocking.

### g-go-review post-implementation gate integration

When `g-go-review` invokes this skill at **Step S** (after Step b3 AC gate, before `[🔍]` write), the skill:

1. Runs Two-Phase Mode against the candidate review source (worktree or snapshot, as established in Step 2b).
2. Returns a structured verdict to `g-go-review`:

   ```yaml
   security_gate:
     mode: two-phase
     threat_model_path: .gald3r/reports/security/threat_model.md
     report_path: .gald3r/reports/security/security_report_20260514_213045.md
     findings:
       critical: 0
       high: 1
       medium: 2
       low: 4
       info: 1
     verdict: BLOCK    # or PASS
     blocking_findings:
       - "[HIGH-001] SQL injection in search_users — api/users.py:87"
     bugs_filed:
       - BUG-104
   ```

3. **Hard block** when `verdict: BLOCK`: `g-go-review` treats every Critical/High finding as an unmet AC and FAILs the task back to `[📋]` with a Status History row naming the finding and the report path.
4. **PASS** when no Critical/High findings: `g-go-review` continues to the docs check (Step 3f) and `[✅]` write.
5. If the changed files are doc-only (`threat_model.md` reports empty / doc-only diff), the gate is skipped with verdict `SKIPPED` and `g-go-review` continues.

### Two-Phase Mode failure modes

| Condition | Behaviour |
|-----------|-----------|
| `git diff HEAD~1..HEAD` fails (no parent commit) | Try `git diff --cached`, then `git diff HEAD`. Record fallback used. If all empty → SKIPPED. |
| `.gald3r/reports/security/` is not writable | Fall back to `.gald3r/logs/security_report_*.md` and emit a Medium finding for the missing report dir. |
| File listed in diff but missing on disk (e.g., renamed without follow) | Skip file with `Info` note; do not crash. |
| `g-skl-bugs REPORT BUG` fails for any finding | Continue scan, accumulate failed-file-bug list, emit one Medium finding documenting the bridge failure. Do NOT downgrade gate verdict. |
| Diff range exceeds 200 files | Phase 2 caps at 200; remaining files become an Info finding "diff too large — re-run with explicit file scope". |

## Integration with g-go-review

When invoked from `g-go-review`:

1. **Default**: Two-Phase Mode (T1167) — auto-scope from the candidate review source's git diff.
2. **Critical findings** → review FAIL (block `[✅]`) + BUGS.md entry via `g-skl-bugs` (severity `critical`).
3. **High findings** → review FAIL unless every High line carries a justified `# nosec:` waiver + BUGS.md entry via `g-skl-bugs` (severity `high`).
4. **Medium / Low** → report only; no automatic BUG entry (humans may file).
5. **Doc-only diff** → SKIPPED with verdict noted in the review summary.
