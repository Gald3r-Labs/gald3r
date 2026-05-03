# g-hk-validate-shell.ps1 - Cursor hook for shell command validation
# Blocks dangerous destructive commands before they execute.

$inputJson = $input | Out-String

try {
    $eventData = $inputJson | ConvertFrom-Json
    $command   = $eventData.command
} catch {
    $command = ""
}

$dangerousPatterns = @(
    "rm -rf /",
    "rm -rf /*",
    "format c:",
    "del /s /q c:\*",
    ":(){:|:&};:"
)

foreach ($pattern in $dangerousPatterns) {
    if ($command -like "*$pattern*") {
        $response = @{
            permission    = "deny"
            user_message  = "Dangerous command blocked: $pattern"
            agent_message = "This command has been blocked by a security hook because it matches a dangerous pattern."
        }
        $response | ConvertTo-Json -Compress
        exit 2
    }
}

@{ permission = "allow" } | ConvertTo-Json -Compress
exit 0
