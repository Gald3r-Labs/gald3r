# Plugin & Skill Pack Author Guide

gald3r is designed to be extended. Third-party skill packs, agents, commands, and hooks are fully supported and encouraged.

This document covers:

- How to structure a plugin / skill pack
- Distribution options
- Licensing options for your plugin
- Naming guidelines (so your work interoperates cleanly with gald3r and respects the trademark)
- Examples and references

---

## Plugin Types

gald3r extensions come in four shapes:

| Type | Location in target project | Purpose |
|---|---|---|
| **Skill pack** | `.cursor/skills/{skill-name}/`, plus mirrors in `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/` | A new capability exposed as an @g-* skill |
| **Agent** | `.cursor/agents/{agent-name}.md` (+ mirrors) | A specialized persona with defined scope and tool set |
| **Command** | `.cursor/commands/{command-name}.md` (+ mirrors) | A thin entry point that invokes a skill or agent |
| **Hook** | `.cursor/hooks/{hook-name}.ps1` (+ mirrors) | Automation triggered on session events |

Most third-party work will be a **skill pack** — a self-contained capability you can distribute as a folder.

---

## Skill Pack Structure

Follow the pattern used by gald3r's built-in optional skill packs (see `skill_packs/` in the gald3r repo for reference):

```
my-skill-pack/
├── PACK.md                    # Pack description, skills list, install notes, license
├── install.ps1                # Installer that copies skills/agents/commands to the 6 IDE targets
├── LICENSE                    # Your license (see "Licensing" below)
├── README.md                  # User-facing documentation
└── skills/
    ├── skill-one/
    │   ├── SKILL.md           # Agent instructions
    │   └── scripts/           # (optional) Python/PowerShell helpers
    └── skill-two/
        └── SKILL.md
```

### PACK.md template

```markdown
# {Pack Name}

**Compatibility**: gald3r 1.4+
**Version**: 0.1.0
**License**: {MIT | Apache-2.0 | Proprietary | Commercial | etc.}
**Author**: {Your name / entity}

## What this pack provides

{One paragraph description.}

## Skills

| Skill | What it does |
|---|---|
| skill-one | ... |
| skill-two | ... |

## Installation

```
.\install.ps1                          # Install into current project
.\install.ps1 -ProjectRoot "C:\proj"   # Install into a specific project
```

## Uninstall

Delete the skill directories listed above from each IDE target folder.
```

### install.ps1 pattern

Your installer should copy each skill into all 6 IDE targets that gald3r supports:

```powershell
param(
    [string]$ProjectRoot = (Get-Location).Path
)

$TargetDirs = @(".cursor", ".claude", ".agent", ".codex", ".opencode", ".copilot")

foreach ($target in $TargetDirs) {
    $dest = Join-Path $ProjectRoot "$target\skills"
    if (Test-Path $dest) {
        Copy-Item -Path "skills\*" -Destination $dest -Recurse -Force
        Write-Host "Installed to $target/skills/"
    }
}
```

Match gald3r's conventions so your pack feels native.

---

## Distribution

Three realistic options:

### 1. GitHub (most common)

Publish your pack as its own repository. Users clone or download and run `install.ps1`.

- Free plugins → public repo
- Paid plugins → private repo with purchase-gated access, or public repo with license-key validation in `install.ps1`

### 2. Standalone zip / tarball

Ship a versioned archive. Users extract and run the installer. Works offline, works for air-gapped environments.

### 3. Future: gald3r plugin registry

A central registry is on the roadmap. Until then, use GitHub.

---

## Licensing Your Plugin

Your plugin is a **separate work** under gald3r's license (FSL-1.1-Apache). This means:

- **You fully own your plugin code.** gald3r's license does not extend to it.
- **You may use any license you want** — MIT, Apache 2.0, GPL, BSL, a custom proprietary license, etc.
- **You may sell your plugin** — one-time purchase, subscription, freemium, whatever model you want.
- **You may keep your plugin closed-source.**

### Recommended license patterns

| Your goal | Recommended license |
|---|---|
| Community contribution, maximum adoption | **MIT** or **Apache 2.0** |
| Build a paid plugin business | **Proprietary commercial** license (use a template from [commonly-used templates](https://opensource.stackexchange.com/questions/tagged/commercial)) |
| Source-available but protect commercial upside | **FSL-1.1-Apache** (same as gald3r) or **BSL 1.1** |
| Block competing use but allow internal commercial use | **Elastic License 2.0** |

You do not need permission from the gald3r project to publish or sell a plugin, regardless of which license you choose.

---

## Naming Guidelines

### What's allowed

Your plugin can clearly identify itself as compatible with gald3r:

- ✅ `video-tools-for-gald3r`
- ✅ `gald3r-compatible task manager`
- ✅ `ACME Skill Pack — works with gald3r`
- ✅ "A plugin for gald3r"
- ✅ "Compatible with gald3r 1.4+"

### What's not allowed

Your plugin must not present itself as gald3r or as an official gald3r product:

- ❌ `gald3r-pro`
- ❌ `gald3r-enterprise`
- ❌ `gald3r-plus`
- ❌ `official gald3r extension` (unless you have written authorization)
- ❌ Using the gald3r logo as your primary brand logo

These restrictions protect users from confusion and protect the gald3r trademark. They do **not** restrict your technical work.

---

## Skill Authoring Standards

To keep the experience consistent across built-in and third-party skills:

1. **Write SKILL.md as agent instructions, not prose documentation.** Format is declarative: "When the user asks X, do Y."
2. **Namespace your commands.** If your pack adds `@g-`-prefixed commands, consider sub-namespacing like `@g-acme-foo` to avoid collisions.
3. **Be idempotent.** install.ps1 should be safe to run repeatedly.
4. **Document file touchpoints.** If your skill reads or writes `.gald3r/` files, list which ones in PACK.md.
5. **Respect rules.** gald3r's `.cursor/rules/` always-apply rules (documentation, git workflow, error reporting, etc.) still apply to sessions using your skill.

See any built-in skill (e.g., `.cursor/skills/g-skl-tasks/SKILL.md`) as a reference.

---

## Commercial Licensing & Enterprise Support

If you want to:

- Embed gald3r in a proprietary product with terms other than FSL
- Remove FSL's Competing Use restriction for a specific commercial context
- Obtain perpetual Apache 2.0 rights before the normal 2-year conversion
- Partner on a co-branded or OEM plugin

Contact the gald3r maintainer directly to discuss commercial licensing terms. These accommodations are routinely made for enterprise users and strategic partners.

---

## Summary

- Build whatever you want on top of gald3r — skills, agents, commands, hooks, packs
- Own it fully, license it however you like, sell it if you want
- Describe your work as "for gald3r" or "gald3r-compatible" — don't call it gald3r itself
- Follow the conventions in this guide so your plugin feels native and works cleanly

Questions? Open an issue on the [gald3r repository](https://github.com/wrm3/gald3r).
