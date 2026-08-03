---
description: 'Set or verify this repo''s Valkyrie connector base URL and login token against world_tree'
argument-hint: '<world-tree-base-url>'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: orchestration
---
Point this repo's Valkyrie connector at the real gald3r_world_tree API: $ARGUMENTS

## What This Command Does

Sets or verifies this project's world_tree base URL and login token so Valkyrie (`gald3r valk`)
coordinates against the real API instead of silently falling through to the `DEFAULT_BASE_URL`
localhost fallback (BUG-238). Uses `g-skl-valk`.

## Workflow

### 1. Determine Target API
Ask (if not provided): which world_tree base URL should this repo use? Default recommendation:
the deployed API host already used by sibling repos in this ecosystem (check
`GALD3R_WORLD_TREE_URL` in a known-good repo's environment if unsure — never guess a localhost
address).

### 2. Choose Persistence Mechanism
- **Env var** (session/CI-scoped, not persisted to disk):
  ```bash
  export GALD3R_WORLD_TREE_URL=https://api.gald3r.ai
  ```
- **`gald3r login`** (persists to OS keyring / 0600 token file — never git):
  ```bash
  gald3r login --base-url https://api.gald3r.ai --token <bearer-token>
  ```
  `--token` defaults to `$GALD3R_WORLD_TREE_TOKEN` if omitted.

### 3. Verify
Run `gald3r valk status` and `gald3r workspace token-status` to confirm the new base URL and
token are active (see `@g-valk-status`).

### 4. Optionally Start the Resident Connector
```bash
gald3r valk start --detach   # spawns the resident poll loop; gald3r valk stop to end it
```

### 5. Report
Confirm the resolved base URL tier, whether a token is stored, and whether the resident
connector was started.

## Usage Examples

```
@g-valk-connect https://api.gald3r.ai
```

## Delegates To
`g-skl-valk`
