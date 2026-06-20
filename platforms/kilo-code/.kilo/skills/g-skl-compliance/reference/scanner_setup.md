---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
# Scanner Setup — g-skl-compliance

Per-scanner installation and authentication instructions for g-skl-compliance.

---

## 1. ORT (OSS Review Toolkit) — Priority 1 ✅ Preferred

**What it does**: Full SCA scan — dependency graph, license detection, vulnerability detection, copyright notices.

**Requires**: Java 11+ on PATH.

### Install

```bash
# macOS (Homebrew)
brew install ort

# Linux / Windows — download binary release
# https://github.com/oss-review-toolkit/ort/releases
# Extract and add bin/ to PATH

# Verify
ort --version
```

### Usage

```bash
ort analyze -i /path/to/repo -o /path/to/output-dir
ort report -i /path/to/output-dir/analyzer-result.json -o /path/to/report-dir -f StaticHtml
```

### Notes

- No API key required for open-source use
- Results written to output directory; g-skl-compliance reads the JSON analyzer result
- Supports: npm, pip, Maven, Gradle, Cargo, Go modules, Bundler, Composer, and more

---

## 2. FOSSA CLI — Priority 2

**What it does**: Commercial SCA platform — license compliance, vulnerability management, policy enforcement.

**Requires**: `FOSSA_API_KEY` environment variable (free tier available).

### Install

```bash
# macOS / Linux
curl -H 'Cache-Control: no-cache' \
  https://raw.githubusercontent.com/fossas/fossa-cli/master/install-latest.sh | bash

# Windows (PowerShell)
iex ((New-Object System.Net.WebClient).DownloadString(
  'https://raw.githubusercontent.com/fossas/fossa-cli/master/install-latest.ps1'))

# Verify
fossa --version
```

### Authentication

1. Sign up at https://app.fossa.com (free tier available)
2. Go to Account Settings → API Tokens → Create token
3. Set environment variable:

```powershell
$env:FOSSA_API_KEY = "your-api-key-here"
# Or add to your shell profile / .env file
```

### Usage

```bash
fossa analyze      # Run dependency analysis
fossa test         # Check against policy (non-zero exit on violations)
fossa report attribution  # Generate attribution report
```

---

## 3. Snyk CLI — Priority 3

**What it does**: Vulnerability scanning + license compliance. Integrates with GitHub, GitLab, Bitbucket.

**Requires**: Snyk account (free tier available) + `snyk auth`.

### Install

```bash
npm install -g snyk
snyk --version
```

### Authentication

```bash
snyk auth
# Opens browser → authenticate → token stored in ~/.config/configstore/snyk.json
```

### Usage

```bash
snyk test                     # Vulnerability scan
snyk test --json              # JSON output for parsing
snyk license                  # License compliance check (paid plan)
```

### Notes

- License compliance (`snyk license`) requires a paid plan
- Free tier covers vulnerability scanning only
- g-skl-compliance uses `snyk test --json` and parses vulnerability output

---

## 4. PMD / PMD CPD — Priority 4

**What it does**: Copy-Paste Detection (clone detection) — identifies duplicate code blocks. **Does NOT perform license scanning.**

**Requires**: Java 11+ on PATH.

### Install

```bash
# Download from https://pmd.github.io/#downloads
# Extract and add pmd/bin/ to PATH

# Verify (command name is 'pmd' or 'pmdc' depending on version)
pmd --version
# or
pmdc --version
```

### Usage

```bash
# Copy-Paste Detection
pmd cpd --minimum-tokens 50 --dir ./src --format xml > cpd-report.xml

# or with newer pmdc wrapper
pmdc cpd --minimum-tokens 50 --dir . --format xml
```

### Notes

- PMD CPD only detects code duplication — no license or vulnerability scanning
- Useful as a code quality gate; g-skl-compliance reports CPD results separately from license verdicts
- COMPLIANCE verdict from PMD-only is based on code quality (clone ratio), not license risk

---

## 5. Fallback Mode — Always Available

**What it does**: Parses package manifest files directly to extract declared licenses. No external tools, no network, fully offline.

**Requires**: Nothing — always available.

### Supported manifests

| File | Tool | License extraction |
|------|------|-------------------|
| `package.json` | npm/Node.js | `.license` or `.licenses[]` field |
| `pyproject.toml` | Python/UV | `[project].license.text` or `classifiers` |
| `setup.py` / `setup.cfg` | Python | `license=` argument |
| `Cargo.toml` | Rust | `[package].license` field |
| `go.mod` | Go | No standard field — flags package as `unknown` |
| `pom.xml` | Java/Maven | `<licenses><license><name>` block |
| `*.gemspec` | Ruby | `.license` attribute |
| `composer.json` | PHP | `.license` field |
| `Package.swift` | Swift | No standard field — flags as `unknown` |

### Limitations

- Only reads declared licenses in manifests — does not detect actual license files in dependencies
- Transitive dependencies not analyzed (only direct manifest entries)
- Go modules and some other ecosystems have no standard license declaration field
- Use ORT or FOSSA for production-grade compliance in CI/CD

---

## Choosing the Right Scanner

| Scenario | Recommended |
|----------|-------------|
| Open source project, full compliance | ORT |
| Commercial project, license policy enforcement | FOSSA |
| Vulnerability-focused, fast feedback | Snyk |
| Code quality / clone detection only | PMD CPD |
| Offline / air-gapped / quick check | Fallback |
| No tools available | Fallback (always works) |
