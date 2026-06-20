# g-hk-kiro-cli-tool-start.ps1 - kiro-cli `preToolUse` -> canonical `tool-start`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY: reads the kiro-cli STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here. Exit code 2
# from the core blocks the tool call (kiro-cli preToolUse semantics).
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .kiro/hooks/g-hk-on-tool-start.py
exit $LASTEXITCODE
