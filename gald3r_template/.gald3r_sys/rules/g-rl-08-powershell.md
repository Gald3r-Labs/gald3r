# PowerShell on Windows 10/11

## Critical Rules
- Use `;` as command separator (NOT `&&`)
- `curl` is aliased to `Invoke-WebRequest` — use `curl.exe` or `Invoke-WebRequest -Uri "URL" -UseBasicParsing`
- NEVER use multi-line `python -c` commands — they cause parsing errors
- Set UTF-8 before Python: `$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8`
- Run Flask/web servers as background tasks to avoid hanging
- Get UTC time: `powershell -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`

## HTTP Requests
```powershell
# Use these (NOT bare curl):
curl.exe -s http://localhost:5000/api/status
Invoke-WebRequest -Uri "http://localhost:5000/api/status" -UseBasicParsing
```

## curl Flag → PowerShell Mapping
| curl | PowerShell |
|------|-----------|
| `-s` | `-UseBasicParsing` |
| `-o file` | `-OutFile "file"` |
| `-X POST` | `-Method POST` |
| `-H "K: V"` | `-Headers @{"K"="V"}` |
| `-d "data"` | `-Body "data"` |

## Python Execution
```powershell
# Single-line only:
python -c "import sys; print(sys.version)"

# For multi-line, use a script file or pipe:
$pythonCode = @"
from some_module import something
print(something())
"@
$pythonCode | python
```

## If Commands Hang or Parse Errors Occur
1. Stop — don't retry the same command
2. Reset encoding (UTF-8 commands above)
3. Use `cmd /c "python script.py"` as fallback
4. Redirect output to file: `python script.py > output.log 2>&1; Get-Content output.log`
