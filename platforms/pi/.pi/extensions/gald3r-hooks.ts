/**
 * gald3r-hooks.ts — canonical lifecycle-hook bridge for Pi (badlogic/pi-mono).
 *
 * T510-pattern port (see the Goose port at
 * gald3r_core/platforms/goose/.agents/plugins/gald3r-hooks/hooks/hooks.json for the sibling
 * implementation): Pi has NO declarative hooks.json — lifecycle hooks are registered
 * programmatically via `pi.on(event, handler)` on the ExtensionAPI object passed to this
 * extension's default export (verified 2026-07-03 against https://pi.dev/docs/latest/extensions).
 *
 * Every registered handler shells out to the SAME shared canonical Python dispatcher
 * (`g_hk_core.dispatch(<canonical-event>)`) already used by every other gald3r platform port,
 * passing the Pi event payload as JSON on stdin — the identical contract
 * `_hook_common.read_stdin_json()` already parses. This file contains NO business logic; it is a
 * thin trigger shim, exactly like `g-hk-on-<event>.py` on Goose/Claude Code.
 *
 * Native Pi event -> canonical gald3r event:
 *   session_start      -> session-start
 *   session_shutdown    -> session-end
 *   tool_call           -> tool-start
 *   tool_result         -> tool-end
 *
 * Source: https://pi.dev/docs/latest/extensions (ExtensionAPI, pi.on(), event list)
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

// ExtensionAPI is provided by the Pi host at load time; a minimal structural type keeps this
// file dependency-free (no @types/pi-coding-agent import required to lint/compile standalone).
interface ExtensionAPI {
	on(event: string, handler: (event: unknown, ctx: unknown) => Promise<void> | void): void;
}

/** Walk up from this file to find the gald3r project root (.gald3r/ or .gald3r_sys/). */
function findProjectRoot(startDir: string): string {
	let dir = startDir;
	for (let i = 0; i < 32; i++) {
		if (existsSync(join(dir, ".gald3r")) || existsSync(join(dir, ".gald3r_sys"))) {
			return dir;
		}
		const parent = dirname(dir);
		if (parent === dir) break;
		dir = parent;
	}
	return startDir;
}

/** Locate the shared canonical hook core (T1628: pi ships its own copy at .pi/hooks/). */
function locateHookCore(root: string): string | null {
	const candidates = [
		join(root, ".pi", "hooks", "g_hk_core.py"),
		join(root, ".agents", "plugins", "gald3r-hooks", "hooks", "g_hk_core.py"),
		join(root, ".gald3r_sys", "hooks", "g_hk_core.py"),
	];
	for (const c of candidates) {
		if (existsSync(c)) return c;
	}
	return null;
}

/** Run the shared dispatcher for a canonical event, piping the Pi payload as JSON on stdin. */
function dispatchCanonicalEvent(canonicalEvent: string, payload: unknown): void {
	const root = findProjectRoot(process.cwd());
	const core = locateHookCore(root);
	if (!core) return; // degrade gracefully — no gald3r hook core available, never block the session

	const entrypoint = [
		"import sys, runpy",
		`sys.argv = ["g_hk_core.py"]`,
		`mod = runpy.run_path(${JSON.stringify(core)}, run_name="__gald3r_hook_bridge__")`,
		`sys.exit(mod["dispatch"](${JSON.stringify(canonicalEvent)}))`,
	].join("\n");

	try {
		spawnSync("python", ["-c", entrypoint], {
			input: JSON.stringify(payload ?? {}),
			encoding: "utf-8",
			timeout: 30_000,
			cwd: root,
		});
	} catch {
		// Hooks must never crash the host session (same contract as _hook_common.py).
	}
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", async (event) => dispatchCanonicalEvent("session-start", event));
	pi.on("session_shutdown", async (event) => dispatchCanonicalEvent("session-end", event));
	pi.on("tool_call", async (event) => dispatchCanonicalEvent("tool-start", event));
	pi.on("tool_result", async (event) => dispatchCanonicalEvent("tool-end", event));
}
