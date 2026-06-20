# g-hk-kiro-cli-user-prompt-submit.ps1 - kiro-cli `userPromptSubmit` -> canonical `user-prompt-submit`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY: reads the kiro-cli STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .kiro/hooks/g-hk-on-user-prompt-submit.py
exit $LASTEXITCODE
