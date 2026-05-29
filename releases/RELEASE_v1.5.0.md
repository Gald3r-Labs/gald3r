**Released:** 2026-05-10
**Version:** 1.5.0 (Maestro Harvest)
**Type:** Minor -- new features, no breaking changes
**Previous release:** [v1.4.0](RELEASE_v1.4.0.md)

---

## Highlights

### New security and quality skills
- **`g-skl-security-scan`** -- a two-phase SAST scanner. A fast, free regex pass surfaces
  candidates across 12 vulnerability categories (hardcoded credentials, SQL injection,
  eval/exec, weak crypto, path traversal, CORS wildcards, and more), then a focused LLM
  pass analyzes only the flagged batches. Complements `g-skl-code-review`.
- **`g-skl-context-builder`** -- assembles a token-budgeted context block on the fly from
  live `.gald3r/` state (active tasks, constraints, relevant subsystems, recent memory),
  so agents start work with the right context and nothing more.
- **`g-skl-delegate`** -- an engineering-team delegation workflow: task-brief templates,
  code-review request templates, quality-gate checklists, and clean handoff protocols.

### Recon and research suite
A unified research family replaces the older one-off ingest skills: capture a GitHub
repo, a URL, a docs site, a YouTube transcript, or a local file into your vault, then run
deep analysis and apply the findings as gald3r artifacts. Includes a similarity-risk
field so harvested patterns carry IP provenance from capture through apply.

### More coding-agent runtimes
- **`g-skl-cli-jcode`** -- documents the jcode Rust agent as a low-overhead local runtime
  (millisecond startup, local embeddings via Ollama) alongside the existing CLI packs.
- **`g-skl-comfyui`** -- local GPU image and video generation via ComfyUI (SDXL,
  AnimateDiff) with zero cloud cost.

### Pipeline and workflow improvements
- `g-go-code` context-prep can now query a code graph (`g-skl-graphify`) for far cheaper
  architecture lookups, with graceful fallback to grep-based prep.
- `g-go --swarm` gains file-lock manifests so parallel agents never edit the same files.
- Mid-flight `@g-steer` and `@g-queue` for in-progress worktree sessions, plus
  `@g-go-code --resume` crash recovery via checkpoint artifacts.
- New `@g-triage` command turns unstructured input (emails, Slack, meeting notes) into
  routed gald3r items behind a hard human-approval gate.
- `AGENT_CONFIG.md` harness tuning guide (context budgets, temperature presets, retries).

---

## Install / Upgrade

Pick your platform folder and copy its contents to your project root:

```bash
# Example for Cursor
cp -r cursor/ /your/project/
```

For a fresh install see [instructions_new_project.md](../instructions_new_project.md).
For upgrading an existing install see [instructions_existing_project.md](../instructions_existing_project.md).
