"""Helper for single-file systems whose state is a markdown table (ideas, vocab,
constraints). Finds a table by a unique header fragment, parses its data rows,
and rewrites them in place — preserving the rest of the document.
"""
from __future__ import annotations

from typing import List, Optional, Tuple


def _is_row(line: str) -> bool:
    return line.strip().startswith("|")


def parse_rows(text: str, header_fragment: str) -> Optional[Tuple[int, int, List[List[str]]]]:
    """Return (header_line_idx, data_end_idx, rows) for the table whose header line
    contains `header_fragment`. rows = list of cell lists (separator row excluded)."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if _is_row(ln) and header_fragment in ln:
            j = i + 2  # skip header + |---| separator
            rows: List[List[str]] = []
            while j < len(lines) and _is_row(lines[j]):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            return i, j, rows
    return None


def replace_rows(text: str, header_fragment: str, row_lines: List[str]) -> str:
    """Replace the data rows of the matching table with `row_lines` (full `| a | b |`
    strings). If the table isn't found, the text is returned unchanged."""
    found = parse_rows(text, header_fragment)
    if not found:
        return text
    lines = text.splitlines()
    hi, end, _ = found
    new = lines[: hi + 2] + row_lines + lines[end:]
    out = "\n".join(new)
    return out + "\n" if text.endswith("\n") else out
