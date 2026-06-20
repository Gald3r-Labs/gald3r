// gald3r canonical hooks — OpenCode plugin (T512)
//
// OpenCode hooks are JS/TS plugins (NOT command hooks), auto-loaded from `.opencode/plugins/*.js`
// (project) or `~/.config/opencode/plugins/` (global). This plugin is the OpenCode "trigger layer":
// it keeps the shared Python core (`g_hk_core.py`) byte-identical across every platform and simply
// shells out to the standard `g-hk-on-<event>.py` entrypoints, mapping OpenCode's plugin events to
// the gald3r canonical event set.
//
// Event mapping (OpenCode -> canonical):
//   tool.execute.before -> tool-start  (throws to BLOCK when a concern blocks)
//   tool.execute.after  -> tool-end
//   session.created     -> session-start
//   session.deleted     -> session-end
//   session.idle        -> stop
//
// The Python core + entrypoints + concern hooks live in the sibling `gald3r-hooks/` dir (ignored by
// the OpenCode plugin loader, which only loads .js/.ts). Requires `python` on PATH.
//
// STATUS: authored against opencode.ai/docs/plugins (2026-06-18) — PENDING live-install verification
// (the exact `input`/`output` shapes for tool.execute.* and the session event payloads should be
// confirmed against the installed OpenCode SDK version). Fail-soft: any error allows (never blocks
// the host) EXCEPT an explicit concern block on tool-start.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const CORE_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "gald3r-hooks");

function runCore(event, payload) {
  const entry = path.join(CORE_DIR, `g-hk-on-${event}.py`);
  try {
    const res = spawnSync("python", [entry], {
      input: JSON.stringify(payload ?? {}),
      encoding: "utf-8",
    });
    const out = (res.stdout || "").trim();
    let parsed = {};
    if (out) {
      try {
        parsed = JSON.parse(out);
      } catch {
        parsed = { additional_context: out };
      }
    }
    if (res.status === 2) parsed.continue = false;
    return parsed;
  } catch {
    return { continue: true };
  }
}

export const Gald3rHooks = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const args = (output && output.args) || {};
      const r = runCore("tool-start", {
        tool_name: input && input.tool,
        tool_input: args,
        command: args.command,
        file_path: args.filePath || args.path,
      });
      if (r && r.continue === false) {
        throw new Error(r.reason || "gald3r hook blocked this tool call");
      }
    },
    "tool.execute.after": async (input) => {
      runCore("tool-end", { tool_name: input && input.tool });
    },
    event: async ({ event }) => {
      if (!event || !event.type) return;
      if (event.type === "session.created") runCore("session-start", {});
      else if (event.type === "session.deleted") runCore("session-end", {});
      else if (event.type === "session.idle") runCore("stop", {});
    },
  };
};
