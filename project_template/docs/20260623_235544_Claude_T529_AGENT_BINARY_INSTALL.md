# Installing the gald3r Agent (precompiled binary)

> Consumer install guide. The gald3r agent ships as a **single precompiled
> binary** — you do not clone or compile source. Distribution follows the jcode
> single-fast-binary pattern (one self-contained executable, install-once,
> persistent across updates).

## Install (install-once)

The binary IS the global `gald3r` command. "Install" = put it on `PATH` under a
stable name.

### Windows
```powershell
$dir = "$env:LOCALAPPDATA\Programs\gald3r"
New-Item -ItemType Directory -Force $dir | Out-Null
Move-Item gald3r-windows-x86_64.exe "$dir\gald3r.exe" -Force
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$dir", "User")
gald3r --version
```

### macOS / Linux
```bash
sudo install -m 0755 gald3r-<os>-<arch> /usr/local/bin/gald3r
gald3r --version
```

## Update (persistent across updates)

Download the new binary and **overwrite the same file**. No reinstall, no PATH
change. Your config and state live under the gald3r home (`~/.gald3r` /
`$GALD3R_HOME` / `%LOCALAPPDATA%\gald3r`), which is independent of the executable
location — so updates never disturb it.

```bash
sudo install -m 0755 gald3r-<os>-<arch> /usr/local/bin/gald3r   # macOS/Linux
# or overwrite %LOCALAPPDATA%\Programs\gald3r\gald3r.exe         # Windows
```

## Usage

```bash
gald3r --help            # all commands
gald3r login             # authenticate to world_tree
gald3r run --task "..."  # run a task (drives the remote agent session)
gald3r agent run spec.yaml   # run a declarative agent spec
gald3r doctor            # diagnose the local environment
```

## Contributors

If you are developing the agent itself (not just using it), use the editable
source flow instead of the binary:

```bash
git clone <repo>
cd gald3r_agent
uv sync
uv pip install -e .
```

The binary is the **consumer** path; the editable install is the **contributor**
path. The binary is produced from the source by
`packaging/pyinstaller/build_binary.py`.

## IP note

The precompiled binary is a **thin client**: server-side agent IP (the agent
loop, memory, policy/permission decisioning, personality, and orchestration) runs
server-side and is excluded from the binary. The binary contains only the local
client: login, the remote-session driver, the local tool executor, and output
rendering.
