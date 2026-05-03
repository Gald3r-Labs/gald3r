---
name: g-skl-tier-setup
description: Configurable product-tier onboarding skill. SETUP creates release_profiles/, scaffolds template_{tier}/ directories, and writes .gald3r/.identity tier metadata. ENABLE annotates existing SUBSYSTEMS.md with min_tier:, infers defaults from subsystem content, and calls platform_parity_sync -TierSync. Ships in full + adv tiers only (slim installs are pre-configured).
operations: [SETUP, ENABLE]
---
# g-skl-tier-setup

**Files Owned**: `.gald3r/release_profiles/*.yaml`, `.gald3r/.identity` (tier fields), newly created `template_{tier}/` directories, `min_tier:` fields in `.gald3r/subsystems/*.md`.

**Activate for**: "tier setup", "enable tiers", "add a product tier", "free/pro/enterprise", "slim/full/adv", `@g-tier-setup`, `@g-tier-setup SETUP`, `@g-tier-setup ENABLE`.

**Tier**: Ships in `gald3r_template_full/` and `gald3r_template_adv/` only — NOT in `gald3r_template_slim/`. Slim projects are pre-configured by gald3r itself and do not manage tiers.

**Dependency**: Requires T082 sub-tasks 082-1 through 082-3 shipped (subsystem `min_tier:` schema, `release_profiles/` directory, `tier_sync.ps1`). Calls into `platform_parity_sync.ps1 -TierSync` after ENABLE.

---

## Why this skill exists

gald3r itself uses three tiers: `slim`, `full`, `adv`. That is one valid configuration, not the only one. This skill lets ANY gald3r project adopt its own tier system with its own names — for example a SaaS project might use `free`, `pro`, `enterprise`; a consulting firm might use `open-source`, `commercial`; an internal tool might use `dev`, `prod`.

The tier system is the routing table that controls:
- Which template directory receives which skills/commands/hooks at sync time (082-3)
- Which destination repo gets which tier on ship (052 release system)
- Which `min_tier:` each subsystem declares (082-1)
- Which tier badge each task displays (082-5)

`g-skl-tier-setup` is the only skill that writes the routing table itself. Everything else just reads it.

---

## Release Profile Schema (what SETUP writes)

Each tier gets one YAML file in `.gald3r/release_profiles/`:

```yaml
name: {tier_name}                       # Matches filename without .yaml
tier_prefix: {V}                        # Version prefix letter/string (e.g. "F" → "F1.2.0")
template_dir: template_{tier_name}/     # Relative path to tier's template directory
destination: {absolute/path/to/repo}    # Local sibling repo path (optional, can be {placeholder})
remote: {https://github.com/...}        # Remote URL (optional, can be empty)
included_tiers: [list_of_lower_tiers]   # What this tier includes (highest includes all)
operational_requirement: {none|api-keys|docker|custom}
description: "{one-line description}"
```

Full field reference lives in `.gald3r/release_profiles/README.md`.

---

## Operation: SETUP (interactive)

**Usage**: `@g-tier-setup SETUP` (or plain `@g-tier-setup` when no tiers are configured yet)

**Prerequisites check** (abort with clear message if any fails):
1. `.gald3r/.identity` exists (project must be initialized — run `@g-setup` first if absent)
2. `.gald3r/release_profiles/` is either absent, empty, or only contains `README.md` (otherwise offer to re-run in REPAIR mode — see below)

**Step 1 — Ask how many tiers**
```
How many product tiers? [3]
```
Default: 3. Minimum: 1. Maximum: 8 (no hard limit, but warn at 6+).

**Step 2 — Ask tier names (one per tier)**
Ask in ascending capability order — "tier 1" = lowest / baseline, "tier N" = highest.

```
Tier 1 name [slim]:
Tier 2 name [full]:
Tier 3 name [adv]:
```

Tier names must be:
- Lowercase letters, digits, hyphens only (regex: `^[a-z][a-z0-9-]*$`)
- 2–20 characters
- Unique within this project
- Not matching any reserved name: `README`, `readme`, `all`, `none`, `default`

If invalid: explain the rule and re-ask.

**Step 3 — Ask operational requirement per tier**
```
Operational requirement for 'free'? (none/api-keys/docker/custom) [none]
Operational requirement for 'pro'? (none/api-keys/docker/custom) [api-keys]
Operational requirement for 'enterprise'? (none/api-keys/docker/custom) [docker]
```

Defaults by tier position:
- Tier 1 (lowest) → `none`
- Tier 2 → `api-keys`
- Tier 3+ → `docker`

`custom` stores the literal string `custom` — the user should follow up by editing the YAML directly to describe what the requirement is.

**Step 4 — Ask version prefix per tier**
```
Version prefix for 'free'? [F]: FREE
Version prefix for 'pro'? [P]: PRO
Version prefix for 'enterprise'? [E]: ENT
```

Default: the first letter of the tier name, uppercased. User may accept or override. 1–6 characters.

**Step 5 — Ask remote repo URL per tier (optional)**
```
Remote repo for 'free' (enter to skip):
Remote repo for 'pro' (enter to skip):
Remote repo for 'enterprise' (enter to skip):
```

Empty string → `remote: ''` in YAML (explicit empty, not null).

**Optional step 5b — Ask destination path per tier**
If the user answered any remote URL, also ask destination. Otherwise default to `{LOCAL}` placeholder (matches gald3r's own pattern for projects without a sibling repo configured yet):

```
Destination path for 'free' (enter for {LOCAL}):
```

**Step 6 — Compute included_tiers**
Each tier includes itself plus all lower-numbered tiers. Example:
- `free` → `[free]`
- `pro` → `[free, pro]`
- `enterprise` → `[free, pro, enterprise]`

**Step 7 — Write files**
For each tier, write `.gald3r/release_profiles/{tier_name}.yaml` with the collected values. Write order is stable (tier 1 first). If `.gald3r/release_profiles/README.md` is missing, copy the canonical README template from this skill's `reference/release_profiles_README_template.md`.

**Step 8 — Scaffold template directories**
For each tier, create `template_{tier_name}/` at the project root if it does not exist. Each directory gets a single `.gitkeep` file. Population is out of scope — 082-3 `-TierSync` and 082-4 handle that.

**Step 9 — Update `.gald3r/.identity`**
Append (or update) two lines:
```
tier_system=enabled
tier_names=[list,of,names]
```

Format is `key=value`, same style as existing identity fields. If `tier_system=enabled` is already present, UPDATE rather than duplicate. `tier_names` is comma-separated, bracket-wrapped, no spaces.

**Step 10 — Confirmation output**
```
Created:
  .gald3r/release_profiles/free.yaml
  .gald3r/release_profiles/pro.yaml
  .gald3r/release_profiles/enterprise.yaml
  template_free/ (scaffolded, .gitkeep only)
  template_pro/ (scaffolded, .gitkeep only)
  template_enterprise/ (scaffolded, .gitkeep only)
Updated:
  .gald3r/.identity (tier_system=enabled, tier_names=[free,pro,enterprise])

Next:
  Run @g-tier-setup ENABLE to map existing subsystems to tiers,
  then run scripts/platform_parity_sync.ps1 -TierSync to populate template directories.
```

**REPAIR note**: If `.gald3r/release_profiles/` already has tier YAMLs, SETUP refuses by default and tells the user to edit the YAMLs directly, run `@g-tier-setup SETUP --force` to overwrite (destructive — warn first), or run `@g-tier-setup ENABLE` if they just need to annotate subsystems.

---

## Operation: ENABLE (annotate existing subsystems)

**Usage**: `@g-tier-setup ENABLE` — run after SETUP, or on an existing project whose `release_profiles/` already exist but whose subsystems lack `min_tier:` annotations.

**Prerequisites check**:
1. `.gald3r/release_profiles/` exists and has at least one `{tier}.yaml`
2. `.gald3r/SUBSYSTEMS.md` exists
3. At least one spec file in `.gald3r/subsystems/`

**Step 1 — Load tier list**
Read all `.gald3r/release_profiles/*.yaml` (excluding README.md). Build the ordered tier list from lowest `included_tiers:` length to highest. Store the lowest tier name as `DEFAULT_TIER` for use in inference fallback.

**Step 2 — Scan each subsystem spec**
For each `.gald3r/subsystems/{name}.md`:

1. Read the file.
2. Parse existing `min_tier:` in frontmatter.
3. If already present AND valid (value is one of the configured tier names) → skip and report `✓ {name}: already {value}`.
4. If absent OR invalid → run inference heuristics.

**Step 3 — Inference heuristics**

Apply in order; first match wins.

| Signal | Inferred `min_tier:` |
|--------|--------------------|
| Spec file text references `Docker`, `docker-compose`, container, `localhost:5433`, `OKE`, Kubernetes | highest tier whose `operational_requirement` is `docker` |
| Spec file text references API keys, `MCP`, `openai`, `anthropic`, `perplexity`, `postgres`, `pgvector`, `oracle` | highest tier whose `operational_requirement` is `api-keys` (or `docker` if no `api-keys` tier exists) |
| Spec file text references `vault`, `research/`, `ingest`, web crawl | same as api-keys tier (these need network) |
| None of the above | `DEFAULT_TIER` (lowest) |

Implementation detail: look at the subsystem spec's Responsibility, Data Flow, Architecture Rules, and Locations sections — NOT just the frontmatter. If in doubt, prefer the lower tier (so features appear in more installs, not fewer).

**Step 4 — Offer the user to override**
Present the inferences as a table and ask for overrides in one batch rather than interactively per-subsystem:

```
Inferred tier assignments:
  behavioral-rules-engine    → slim
  ai-skills-library          → slim
  vault-knowledge-store      → full     [references: vault, ingest]
  harvest-system             → full     [references: api-keys, MCP]
  backend-api                → adv      [references: Docker]
  ...

Accept all? [Y/n/edit]
  Y = write all inferred values
  n = abort without writing
  edit = edit line-by-line
```

In `edit` mode, iterate each subsystem showing the inference and asking for an override (enter = accept inference, else type one of the configured tier names).

**Step 5 — Write annotations**
For each subsystem spec with a new `min_tier:` value:
1. If the frontmatter has `min_tier:` → replace the line.
2. If absent → insert under `name:` or at the end of frontmatter before the closing `---`.
3. Do not touch any other field.

**Step 6 — Update SUBSYSTEMS.md Activity Log**
Append a row to the `tier-management` subsystem's activity log (and `onboarding-and-setup` if present):
```
| {YYYY-MM-DD} | ENABLE | g-skl-tier-setup | Annotated N subsystems with min_tier: |
```

**Step 7 — Call tier sync**
Run `scripts/platform_parity_sync.ps1 -TierSync` as a child process. This populates `template_{tier}/` directories based on subsystem mappings. If the sync script is missing (uncommon — it ships with 082-3), emit a warning but do not fail: `Tier sync skipped: scripts/platform_parity_sync.ps1 not found (expected from T082-3).`

**Step 8 — Confirmation output**
```
Annotated:
  N subsystems with min_tier:
  - slim: [list]
  - full: [list]
  - adv:  [list]
Tier sync: COMPLETE | SKIPPED (reason)
Subsystem Activity Log updated in: tier-management
```

---

## Inference Heuristics — Full Rules Reference

When ENABLE scans a subsystem spec file, apply these regexes (case-insensitive) against the full file body:

| Regex pattern | Signal | Suggested tier class |
|---------------|--------|----------------------|
| `docker|docker-compose|container|OKE|kubernetes|localhost:543[23]` | requires container runtime | `docker` tier |
| `MCP|mcp server|mcp_tool|mcp__` | requires MCP server | `docker` tier (MCP is Docker-delivered) |
| `postgres|pgvector|oracle thick|mysql` | requires managed DB | `docker` tier |
| `api[_\-]?key|API Key|OPENAI_KEY|ANTHROPIC_|PERPLEXITY_|sk-[A-Za-z0-9]` | requires external API keys | `api-keys` tier |
| `openai|anthropic|perplexity|gemini API` | cloud AI service | `api-keys` tier |
| `vault_location|research/platforms|research/github|ingest[_-]doc` | vault subsystem — needs network for crawl | `api-keys` tier |
| `crawl4ai|playwright|firecrawl` | web crawling | `api-keys` tier |
| *no match* | file-only behavior | lowest tier |

When two signals match, higher-requirement tier wins (docker > api-keys > none). If the project has no `docker` tier, a docker-class signal downshifts to the highest available tier. Likewise if no `api-keys` tier exists, api-keys-class signals downshift to the highest available.

---

## Example session — SaaS project (free / pro / enterprise)

```
@g-tier-setup SETUP

How many product tiers? [3]
Tier 1 name [slim]: free
Tier 2 name [full]: pro
Tier 3 name [adv]:  enterprise

Operational requirement for 'free'? (none/api-keys/docker/custom) [none]
Operational requirement for 'pro'? (none/api-keys/docker/custom) [api-keys]
Operational requirement for 'enterprise'? (none/api-keys/docker/custom) [docker]

Version prefix for 'free'? [F]: FREE
Version prefix for 'pro'? [P]: PRO
Version prefix for 'enterprise'? [E]: ENT

Remote repo for 'free' (enter to skip): https://github.com/acme/product-free.git
Remote repo for 'pro' (enter to skip):
Remote repo for 'enterprise' (enter to skip):

Created:
  .gald3r/release_profiles/free.yaml
  .gald3r/release_profiles/pro.yaml
  .gald3r/release_profiles/enterprise.yaml
  template_free/ (scaffolded, .gitkeep only)
  template_pro/ (scaffolded, .gitkeep only)
  template_enterprise/ (scaffolded, .gitkeep only)
Updated:
  .gald3r/.identity (tier_system=enabled, tier_names=[free,pro,enterprise])

Next:
  Run @g-tier-setup ENABLE to map existing subsystems to tiers,
  then run scripts/platform_parity_sync.ps1 -TierSync to populate template directories.
```

Then:
```
@g-tier-setup ENABLE

Inferred tier assignments:
  auth-service              → free     [no external deps]
  billing-api               → pro      [references: api-keys (Stripe)]
  analytics-worker          → enterprise  [references: Docker, postgres]
  ...

Accept all? [Y/n/edit] Y

Annotated:
  14 subsystems with min_tier:
  - free:       [5 subsystems]
  - pro:        [7 subsystems]
  - enterprise: [2 subsystems]
Tier sync: COMPLETE
Subsystem Activity Log updated in: tier-management
```

---

## Example session — gald3r itself (slim / full / adv)

This is an example source-repo tier configuration:

```yaml
# .gald3r/release_profiles/slim.yaml
name: slim
tier_prefix: S
template_dir: gald3r_template_slim/
destination: G:\gald3r_ecosystem\gald3r
remote: https://github.com/wrm3/gald3r.git
included_tiers: [slim]
operational_requirement: none
description: "Baseline gald3r — git clone only, zero dependencies."
```
```yaml
# .gald3r/release_profiles/full.yaml
name: full
tier_prefix: F
template_dir: gald3r_template_full/
destination: G:\gald3r_ecosystem\gald3r_template_full_release
remote: https://github.com/example/gald3r-template-full.git
included_tiers: [slim, full]
operational_requirement: api-keys
description: "Full-featured gald3r — requires API keys and network."
```
```yaml
# .gald3r/release_profiles/adv.yaml
name: adv
tier_prefix: A
template_dir: gald3r_template_adv/
destination: G:\gald3r_ecosystem\gald3r_adv
remote: https://github.com/wrm3/gald3r_adv.git
included_tiers: [slim, full, adv]
operational_requirement: docker
description: "Advanced gald3r — requires Docker backend and MCP."
```

If a consumer project wanted slim/full/adv too, SETUP would produce this exact shape (minus the hardcoded gald3r-specific paths).

---

## Example session — Two-tier project (community / commercial)

```
@g-tier-setup SETUP

How many product tiers? [3]: 2
Tier 1 name [slim]: community
Tier 2 name [full]: commercial

Operational requirement for 'community'? [none]
Operational requirement for 'commercial'? [api-keys] docker

Version prefix for 'community'? [C]
Version prefix for 'commercial'? [C] CE

Remote repo for 'community' (enter to skip): https://github.com/org/project-community.git
Remote repo for 'commercial' (enter to skip): https://github.com/org/project-commercial.git

Created:
  .gald3r/release_profiles/community.yaml
  .gald3r/release_profiles/commercial.yaml
  template_community/ (scaffolded, .gitkeep only)
  template_commercial/ (scaffolded, .gitkeep only)
Updated:
  .gald3r/.identity (tier_system=enabled, tier_names=[community,commercial])
```

---

## Operational Requirement Reference

| Value | Meaning | Example |
|-------|---------|---------|
| `none` | Pure file-based. No external deps. | baseline slim tier |
| `api-keys` | Needs API keys in env/config to function fully. Network required. | OpenAI/Anthropic-powered features |
| `docker` | Needs Docker + managed services (Postgres, MCP server). | backend-api, MCP plugins |
| `custom` | Special requirement — explain in the `description:` field. | on-prem integrations, bespoke hardware |

Inference defaults match this table: `docker` signals → `docker` tier; `api-keys` signals → `api-keys` tier; otherwise → lowest tier.

---

## Interplay with other skills

- **`g-skl-subsystems`** — writes `min_tier:` in new subsystem specs at CREATE. SETUP does not overwrite subsystem specs; that is ENABLE's job.
- **`g-skl-release`** — reads `release_profiles/*.yaml` for CREATE/ASSIGN/PUBLISH. Must have tiers configured first.
- **`g-skl-tasks`** — derives task tier badge from subsystem `min_tier:` (082-5). Badges only render after ENABLE runs.
- **`scripts/platform_parity_sync.ps1 -TierSync`** — the actual file mover. SETUP scaffolds empty template dirs; ENABLE populates them via the sync script.
- **`g-skl-setup`** — the first-run gald3r installer. Does NOT call this skill — it seeds a slim project. Users who want tiering run `@g-tier-setup SETUP` as a separate opt-in.

---

## What this skill does NOT do

- Does not populate `template_{tier}/` directories with actual skill/rule/command files — that is `scripts/platform_parity_sync.ps1 -TierSync`
- Does not deploy tiers to sibling repos — that is `g-skl-release` SHIP (and PUBLISH)
- Does not modify `gald3r_template_slim/` — see AC-7 in Task 083: slim installs are pre-configured by gald3r
- Does not enforce tier boundaries on new code — see C-018 tier boundary constraint (pending, Task 082-4 dependency)
- Does not run without `.gald3r/` being initialized — run `@g-setup` first

---

## Script backing

The interactive flow can run either in-chat (the agent asks and the user answers in conversation) or via the optional PowerShell script at `scripts/tier_setup.ps1` (shipped inside this skill folder for Cursor only, per D015 canonical-scripts pattern). Both paths produce identical file outputs. Agents should prefer the in-chat flow when the user is present — the script is for unattended/CI usage.

---

## File parity note

This skill ships in:
- Root: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/` (5 targets)
- `gald3r_template_full/`: all 5 IDE directories
- `gald3r_template_adv/`: all 5 IDE directories

It does NOT ship in `gald3r_template_slim/`. That is intentional — C-009 parity is tier-scoped for this skill per AC-7. The `platform_parity_sync.ps1 -TierSync` script already knows tier-scoped skills exist and will not copy this skill into the slim tree.
