# Shared patterns/helpers for gald3r git sanity (pre-commit + push gate). Dot-source from hooks/scripts.
# Repository root is resolved by caller (git rev-parse).

function Get-Gald3rSecretPatterns {
    return @(
        "sk-[a-zA-Z0-9]{20,}",
        "Bearer\s+[a-zA-Z0-9._\-]{20,}",
        "AKIA[A-Z0-9]{16}",
        "password\s*=\s*\S+",
        "api_key\s*=\s*\S+",
        "secret_key\s*=\s*\S+",
        "private_key\s*=\s*\S+",
        "-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
}
