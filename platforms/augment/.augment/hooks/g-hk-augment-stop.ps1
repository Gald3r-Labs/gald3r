# g-hk-augment-stop.ps1 - Augment `Stop` -> canonical `stop`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY (Augment requires a .ps1/.sh/.cmd/.bat script path, not a
# bare `python x.py` command). Reads the Augment STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .augment/hooks/g-hk-on-stop.py
exit $LASTEXITCODE
