---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Scaffold a new gald3r MCP plugin from the `_template/` directory and stage a
matching entry in `docker/gald3r/plugin_catalog.json`.

```
@g-mcp-new <plugin_name> [--category <cat>] [--credential-source <src>]
```

Aliases: none.

## Arguments

- `<plugin_name>` — snake_case name. Must be unique across `docker/gald3r/tools/plugins/`.
- `--category <cat>` — one of: `storage | memory | search | integration | ai | database | research | ingest | monitor | video | admin | util`. Default: `util`.
- `--credential-source <src>` — one of: `none | env | per_call | vault_secret | docker_env`. Default: `none`.

## What it does

1. Validates `<plugin_name>` is unique under `docker/gald3r/tools/plugins/`.
2. Copies `docker/gald3r/tools/plugins/_template/plugin_template.py` to
   `docker/gald3r/tools/plugins/<plugin_name>.py`.
3. Replaces placeholder tokens `{plugin_name}` and `{PLUGIN_NAME}` inside
   the new file with the real name and a TITLE_CASE variant.
4. Appends a new entry to `docker/gald3r/plugin_catalog.json` under
   `plugins[]` with:
   - `name`: `<plugin_name>`
   - `description`: `"TODO: one-line description of <plugin_name>"`
   - `category`: from `--category` (default `util`)
   - `tags`: `[]` (fill in manually)
   - `path`: `tools/plugins/<plugin_name>.py`
   - `credential_source`: from `--credential-source` (default `none`)
   - `version`: `"0.1.0"`
   - `is_enabled`: `true`
   - `is_coming_soon`: `false`
5. Prints next steps:
   - Edit the `TOOL_DESCRIPTION` / `TOOL_PARAMS` constants in the plugin file
   - Fill the `execute(...)` body
   - Update the catalog entry's description and tags
   - Call the `config_reload` MCP tool, or restart the gald3r MCP container

## Validation gates

- BLOCK if `<plugin_name>` is empty or contains characters outside `[a-z0-9_]`.
- BLOCK if a file at `docker/gald3r/tools/plugins/<plugin_name>.py` already exists.
- BLOCK if a catalog entry with `name == <plugin_name>` already exists.
- WARN if `--category` is not in the canonical category list (still proceeds, but
  the plugin won't group cleanly in marketplace UIs).

## Notes

- The `_template/` directory is not loaded as a real plugin by the MCP server.
- After the file is created, run `config_reload` to hot-load it without a Docker
  rebuild. If that fails (e.g. on missing dependencies), restart the container.
- The plugin's `execute(...)` signature must match `TOOL_PARAMS` exactly —
  FastMCP introspects the signature.

## Related

- `docker/gald3r/tools/plugins/_template/README.md` — scaffold template docs
- `docker/gald3r/plugin_catalog.json` — marketplace catalog
- `docs/MCP_TOOLS.md` — current MCP tool reference
- `g-skl-platform-claude` — covers Claude MCP integration
- T972 — task that established this command and the catalog
