# g-test

Manage test plans (fast / comprehensive / regression) for gald3r systems and features.

## When to use

Use `@g-test` to create, audit, run, or check test plans. Enforces constraints C-013, C-014, and C-015.

## Operations

| Subcommand | Purpose |
|---|---|
| `@g-test create <scope>` | Generate all 3 test plan files for a subsystem/feature |
| `@g-test audit` | Check all active subsystems for missing test plans; create tasks for gaps |
| `@g-test run <scope> <L1|L2|L3>` | Execute test plan for a scope at specified level |
| `@g-test verify-gate <scope>` | L1 fast gate — must pass before submitting for `[🔍]` |
| `@g-test release-gate` | L2+L3 gate — must pass before any release/version bump |
| `@g-test status` | Show test plan coverage across all active subsystems |

## Steps

1. Read `g-skl-test` skill
2. Run the corresponding operation based on subcommand

## Usage

```
@g-test create auth
@g-test audit
@g-test run auth L1
@g-test verify-gate api
@g-test release-gate
@g-test status
```

Or with just `@g-test` (no subcommand) — defaults to **audit** mode: checks all active subsystems and creates tasks for any missing test plans.

## Files managed

- `.gald3r/test-plans/{scope}_L1_fast.md`
- `.gald3r/test-plans/{scope}_L2_comprehensive.md`
- `.gald3r/test-plans/{scope}_L3_regression.md`
- `.gald3r/TEST_PLANS.md` (index)
