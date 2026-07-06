#!/bin/bash
# setup_gald3r_project.sh - gald3r Installer launcher (T1586)
# @subsystems: PROJECT_IDENTITY_SETUP
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$DIR/setup_gald3r_project.py" "$@"
else
    exec python "$DIR/setup_gald3r_project.py" "$@"
fi
