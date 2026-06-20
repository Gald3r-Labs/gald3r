# g-hk-augment-tool-start.ps1 - Augment `PreToolUse` -> canonical `tool-start`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY (Augment requires a .ps1/.sh/.cmd/.bat script path, not a
# bare `python x.py` command). Reads the Augment STDIN-JSON payload and pipes it to
# the shared canonical event core. Exit code 2 from the core blocks the tool call
# (Augment PreToolUse semantics). NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .augment/hooks/g-hk-on-tool-start.py
exit $LASTEXITCODE
