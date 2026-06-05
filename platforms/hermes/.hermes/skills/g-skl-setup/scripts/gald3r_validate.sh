#!/usr/bin/env bash
# gald3r_validate.sh — Zero-dependency gald3r structure integrity check (T1012)
# Exit 0 = PASS, Exit 1 = FAIL (violations listed)
# Usage: bash gald3r_validate.sh [--fix] [--json] [--project-root <path>] [--report]

set -euo pipefail

FIX=0
JSON=0
REPORT=0
PROJECT_ROOT=""
VIOLATIONS=()
WARNINGS=()

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fix) FIX=1 ;;
        --json) JSON=1 ;;
        --report) REPORT=1 ;;
        --project-root) PROJECT_ROOT="$2"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

# Auto-discover project root
find_gald_root() {
    local current="${1:-$(pwd)}"
    for i in {1..8}; do
        if [[ -d "$current/.gald3r" ]]; then
            echo "$current"
            return 0
        fi
        local parent
        parent=$(dirname "$current")
        if [[ "$parent" == "$current" ]]; then break; fi
        current="$parent"
    done
    return 1
}

if [[ -z "$PROJECT_ROOT" ]]; then
    if ! PROJECT_ROOT=$(find_gald_root); then
        echo "gald3r validate: FAIL — .gald3r/ not found in current dir or any parent"
        exit 1
    fi
fi

GALD_DIR="$PROJECT_ROOT/.gald3r"
TASKS_DIR="$GALD_DIR/tasks"

# ── CHECK 1: .gald3r/ exists ──────────────────────────────────────────────────
if [[ ! -d "$GALD_DIR" ]]; then
    VIOLATIONS+=("MISSING: .gald3r/ directory")
    if [[ $FIX -eq 1 ]]; then
        mkdir -p "$GALD_DIR"
        VIOLATIONS[-1]="${VIOLATIONS[-1]} [FIXED: created]"
    fi
fi

# ── CHECK 2: Required root files ─────────────────────────────────────────────
for file in TASKS.md PROJECT.md CONSTRAINTS.md BUGS.md SUBSYSTEMS.md; do
    if [[ ! -f "$GALD_DIR/$file" ]]; then
        VIOLATIONS+=("MISSING: .gald3r/$file")
    fi
done

# ── CHECK 3: tasks/ directory ────────────────────────────────────────────────
if [[ ! -d "$TASKS_DIR" ]]; then
    VIOLATIONS+=("MISSING: .gald3r/tasks/ directory")
    if [[ $FIX -eq 1 ]]; then
        mkdir -p "$TASKS_DIR"/{open,in-progress,awaiting-verification,completed}
        VIOLATIONS[-1]="${VIOLATIONS[-1]} [FIXED: created with subdirs]"
    fi
fi

# ── CHECK 4: Task file YAML frontmatter ──────────────────────────────────────
if [[ -d "$TASKS_DIR" ]]; then
    while IFS= read -r -d '' taskfile; do
        filename=$(basename "$taskfile")
        for field in "id:" "title:" "status:" "type:"; do
            if ! grep -qP "^$field|\\n$field" "$taskfile" 2>/dev/null; then
                VIOLATIONS+=("MISSING_FIELD: $filename missing '$field'")
            fi
        done
    done < <(find "$TASKS_DIR" -name "*.md" -print0)
fi

# ── CHECK 5: Phantom detection ───────────────────────────────────────────────
TASKS_INDEX="$GALD_DIR/TASKS.md"
if [[ -f "$TASKS_INDEX" ]]; then
    while IFS= read -r ref; do
        refpath="$GALD_DIR/$ref"
        if [[ ! -f "$refpath" ]]; then
            VIOLATIONS+=("PHANTOM: TASKS.md references missing file: $ref")
        fi
    done < <(grep -oP 'tasks/[^)]+\.md' "$TASKS_INDEX" 2>/dev/null || true)
fi

# ── CHECK 6: Orphan detection ────────────────────────────────────────────────
if [[ -d "$TASKS_DIR" && -f "$TASKS_INDEX" ]]; then
    while IFS= read -r -d '' taskfile; do
        basename_no_ext=$(basename "$taskfile" .md)
        if ! grep -qF "$basename_no_ext" "$TASKS_INDEX" 2>/dev/null; then
            relpath="${taskfile#$GALD_DIR/}"
            WARNINGS+=("ORPHAN: $relpath not referenced in TASKS.md")
        fi
    done < <(find "$TASKS_DIR" -name "task*.md" -print0)
fi

# ── CHECK 7: Subsystem spec files have locations: ────────────────────────────
SUBSYSTEMS_DIR="$GALD_DIR/subsystems"
if [[ -d "$SUBSYSTEMS_DIR" ]]; then
    for spec in "$SUBSYSTEMS_DIR"/*.md; do
        [[ -f "$spec" ]] || continue
        if ! grep -q "locations:" "$spec" 2>/dev/null; then
            WARNINGS+=("INCOMPLETE: subsystems/$(basename "$spec") missing 'locations:' in frontmatter")
        fi
    done
fi

# ── REPORT ────────────────────────────────────────────────────────────────────
total_violations=${#VIOLATIONS[@]}
total_warnings=${#WARNINGS[@]}

if [[ $JSON -eq 1 ]]; then
    echo "{"
    echo "  \"pass\": $([ $total_violations -eq 0 ] && echo 'true' || echo 'false'),"
    echo "  \"violations\": ["
    for i in "${!VIOLATIONS[@]}"; do
        sep=","
        [[ $i -eq $((${#VIOLATIONS[@]}-1)) ]] && sep=""
        echo "    \"${VIOLATIONS[$i]}\"$sep"
    done
    echo "  ],"
    echo "  \"warnings\": ["
    for i in "${!WARNINGS[@]}"; do
        sep=","
        [[ $i -eq $((${#WARNINGS[@]}-1)) ]] && sep=""
        echo "    \"${WARNINGS[$i]}\"$sep"
    done
    echo "  ],"
    echo "  \"project_root\": \"$PROJECT_ROOT\""
    echo "}"
else
    if [[ $total_violations -eq 0 ]]; then
        echo "gald3r validate: PASS"
    else
        echo "gald3r validate: FAIL ($total_violations violations)"
        for v in "${VIOLATIONS[@]}"; do echo "  $v"; done
    fi
    if [[ $REPORT -eq 1 && $total_warnings -gt 0 ]]; then
        for w in "${WARNINGS[@]}"; do echo "  WARN: $w"; done
    fi
fi

[[ $total_violations -eq 0 ]]
