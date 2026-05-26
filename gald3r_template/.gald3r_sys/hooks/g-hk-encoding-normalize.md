# Hook: g-hk-encoding-normalize

## Fires On

The **`stop`** event (end of each agent turn) for every IDE target, and as a git
**`pre-commit`** hook (`-PreCommit`). Also runs as a report-only verification scan
(`-Scan`) for CI / pre-flight gates.

## What It Does

Normalizes git-dirty (or staged, or named) text files to the encoding that is
**correct for their file type** and to **LF line endings**, after every agent turn.
This is the systemic fix for the recurring Windows / PowerShell 5.1 corruption
class (BUG-073 em-dash mangling, BUG-094 mojibake, and CRLF churn in parity sync).

**Encoding policy (the T1428 distinction):**

| File type | Target encoding | Why |
|-----------|-----------------|-----|
| `.ps1`, `.psm1`, `.psd1` (PowerShell) | **UTF-8 WITH BOM** | PS5.1 parses a BOM-less UTF-8 script as Windows-1252 and mangles every non-ASCII byte (em-dash, emoji). The BOM is REQUIRED for PS5.1 correctness (BUG-073). |
| Everything else (`.md`, `.yaml`, `.json`, `.ts`, `.py`, task/bug files, ...) | **UTF-8 no-BOM** | A BOM in markdown / JSON / source is itself the corruption that produces mojibake when other tools read the file. |

All processed files are normalized to **LF** regardless of type.

**Encodings detected and corrected:**
- UTF-8 with BOM (EF BB BF) -- stripped for non-PowerShell; preserved/added for PowerShell
- UTF-16 LE (FF FE) -- converted to the correct UTF-8 variant for the extension
- UTF-16 BE (FE FF) -- converted to the correct UTF-8 variant for the extension
- CRLF / bare CR -- normalized to LF

**File types processed:** `.md`, `.mdc`, `.yaml`, `.yml`, `.json`, `.ps1`, `.psm1`,
`.psd1`, `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.txt`, `.sh`, `.bash`, `.html`,
`.htm`, `.css`, `.scss`, `.sql`, `.toml`, `.ini`, `.cfg`, `.gitattributes`,
`.gitignore`, `.env`, plus extensionless files under `.gald3r/`.

**Binary files are skipped** two ways: (1) by extension — only the text extensions above are
considered; and (2) by content (T1447) — any file the BOM sniff reads as UTF-8/UTF-8-BOM that
contains a NUL byte (`0x00`) is treated as binary/invalid-UTF-8 and left byte-identical, so a
mislabeled binary with a text extension is never lossily rewritten. (UTF-16 files legitimately
contain NULs and are detected by their BOM, so they still normalize correctly.)

## Side Effects

- Rewrites dirty text files in-place (correct UTF-8 BOM state + LF endings).
- In `-PreCommit` mode, re-stages normalized files with `git add` so the fix lands
  in the commit.
- In `-Scan` mode, writes nothing; exits 1 if drift is found (clean = 0).
- Prints a one-line summary per file changed (suppressed with `-Quiet`). Never
  blocks the turn.

## Related Tasks

- T1428: Encoding Intercept Hook -- UTF-8 no-BOM + LF normalization (this hook).
- BUG-073: PS5.1 em-dash / Unicode mangling (drives the `.ps1` BOM exception).
- BUG-094: mojibake / encoding corruption in framework files.
