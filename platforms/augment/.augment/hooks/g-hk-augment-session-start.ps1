# g-hk-augment-session-start.ps1 - Augment `SessionStart` -> canonical `session-start`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY (Augment requires a .ps1/.sh/.cmd/.bat script path, not a
# bare `python x.py` command). Reads the Augment STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .augment/hooks/g-hk-on-session-start.py
exit $LASTEXITCODE
