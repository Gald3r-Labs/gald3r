---
gald3r_rel_version: "3.0.0"
schema_version: "generic-v1"
---
# AGENT_CONFIG.md — gald3r Agent Configuration

Agent harness configuration. Read by the coding/review/context-assembly agents at
session start. Full field-by-field documentation: https://docs.gald3r.ai

## Defaults

```yaml
disable_version_check: false
version_feed_url: https://api.github.com/repos/gald3r/gald3r/releases/latest
auto_triage_risk_threshold: 2.0
active_preset: preset_implementation
# g_go_default_scope: local_only   # uncomment + set to workspace_all on controller repos
context_reduction_mode:
  think_in_code: true
  graphify_b0_enabled: false
skill_capture_hook: false
```

## Presets

Override per-task via `agent_config_preset:` in task frontmatter.

```yaml
preset_implementation:
  context_budget_tokens: 800
  tool_call_order: reads_first
  max_retries: 3
  retry_backoff_seconds: 2
  temperature: 0.2
  memory_injection_timing: session_start
  include_constraints: true
  include_subsystems: true
  include_recent_memory: true
  include_active_task: true

preset_review:
  context_budget_tokens: 400
  tool_call_order: reads_first
  max_retries: 2
  retry_backoff_seconds: 1
  temperature: 0.3
  memory_injection_timing: session_start
  include_constraints: true
  include_subsystems: false
  include_recent_memory: false
  include_active_task: true

preset_planning:
  context_budget_tokens: 1200
  tool_call_order: reads_first
  max_retries: 2
  retry_backoff_seconds: 2
  temperature: 0.5
  memory_injection_timing: per_task
  include_constraints: true
  include_subsystems: true
  include_recent_memory: true
  include_active_task: false

preset_research:
  context_budget_tokens: 1200
  tool_call_order: writes_as_needed
  max_retries: 3
  retry_backoff_seconds: 3
  temperature: 0.6
  memory_injection_timing: session_start
  include_constraints: false
  include_subsystems: false
  include_recent_memory: true
  include_active_task: false
```

## Provider Fallback

```yaml
provider_fallback_chain: {}   # schema + defaults: https://docs.gald3r.ai
```

## Model Assignment

Run `@g-status` to see the current model assignment. Full schema: https://docs.gald3r.ai

## Notes

- Not committed by default (`.gald3r/` is gitignored in the source repo)
- Safe to customize per-project; upgrades will not overwrite this file
- `disable_version_check` is the authoritative override for the version-check step
