#!/usr/bin/env sh
# Provision the bundled gald3r engine (POSIX shells, for macOS/Linux without pwsh).
# Ensures `uv`, then provisions + verifies. Never blocks: on failure the engine is just
# inactive and skills keep working via their SKILL.full.md fallbacks.
#
#   sh .gald3r_sys/engine/provision_engine.sh              # ensure uv + provision + verify
#   NO_INSTALL=1 sh .gald3r_sys/engine/provision_engine.sh # check only, don't install uv
DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  if [ "${NO_INSTALL:-}" = "1" ]; then
    echo "  uv not found (skipped). Engine inactive; skills use their SKILL.full.md fallback."
    exit 2
  fi
  echo "  Installing uv (one-time, no admin required)..."
  if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
    echo "  uv install failed. Engine inactive; SKILL.full.md fallback is active."
    exit 2
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "  Provisioning gald3r engine at $DIR ..."
if uv run --project "$DIR" gald3r --version; then
  echo "  Engine ready. Skills call:  uv run --project .gald3r_sys/engine gald3r <verb>"
  exit 0
else
  echo "  Provision failed — skills remain operable via their SKILL.full.md fallback."
  exit 2
fi
