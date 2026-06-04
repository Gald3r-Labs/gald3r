# g-recon-file

Capture a local file (PDF, DOCX, XLSX, TXT, MD, CSV, RTF) into the vault knowledge store.

Activates **g-skl-recon-file** → CAPTURE operation.

## Usage

```
@g-recon-file /path/to/document.pdf
@g-recon-file /path/to/spreadsheet.xlsx --title "Q1 Data" --topics "finance,metrics"
@g-recon-file /path/to/notes.md --deep   # capture + analysis report
```

## Supported Formats

| Format | Extraction Method |
|--------|------------------|
| `.pdf` | pdfminer.six / pypdf2 text extraction |
| `.docx` | python-docx |
| `.xlsx` / `.csv` | pandas / openpyxl |
| `.txt` / `.md` | direct read |
| `.rtf` | striprtf |

## What it does

1. Detects file type and extracts text content
2. Generates title, summary, and tags from content (or uses provided `--title` / `--topics`)
3. Writes vault note to `research/files/{date}_{slug}.md`
4. Registers in `research/files/_index.yaml`
5. Updates `vault/log.md`

## --deep flag

After capturing, runs analysis and writes a recon report to `vault/research/recon/{slug}/`.

## Clean Room Boundary

These commands support clean-room research and reverse-spec work. Capture/recon may observe and summarize source behavior, interfaces, workflows, data shapes, and architectural patterns; generated gald3r artifacts must use original wording and local architecture terms, not copied source code, docs prose, prompts, tests, or unique strings. Keep source URL, license, and capture provenance in recon notes; treat source file paths as traceability, not implementation instructions. Adoption requires human approval through `@g-res-review` / `@g-res-apply`.

## Notes

- Images and scanned PDFs (no text layer) produce a metadata-only stub with a warning
- Phase 3 (T112) adds LLM-based image/OCR extraction for scanned PDFs
- File is NOT copied to the vault — only a Markdown summary note is created

## Prerequisites

```bash
pip install pdfminer.six python-docx openpyxl pandas striprtf
```
