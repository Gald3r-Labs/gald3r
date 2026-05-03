---
name: g-skl-recon-file
description: Capture a local file (PDF, DOCX, XLSX, TXT, MD, CSV, RTF) into the vault knowledge store. Extracts text content, generates Obsidian-compatible vault notes in research/files/.
---
# g-recon-file

**Activate for**: "capture this file", "add this PDF to the vault", "ingest this document", "save this file to knowledge base", "recon file", `@g-recon-file`

---

## Purpose

Capture local files into the vault knowledge store. Extracts text, generates a summary, and writes an Obsidian-compatible note to `research/files/`. Supports PDF, DOCX, XLSX, TXT, MD, CSV, RTF.

---

## Operation: CAPTURE

```
@g-recon-file /path/to/document.pdf
@g-recon-file /path/to/spreadsheet.xlsx --title "Q1 Data" --topics "finance,metrics"
@g-recon-file /path/to/notes.md --deep
```

### Supported Formats

| Format | Extraction Library | Notes |
|--------|-------------------|-------|
| `.pdf` | pdfminer.six | Text-layer PDFs only; scanned PDFs produce metadata stub |
| `.docx` | python-docx | Full text + heading structure |
| `.xlsx` / `.csv` | pandas / openpyxl | Sheet names, column headers, row sample |
| `.txt` / `.md` | built-in | Direct read |
| `.rtf` | striprtf | Basic text extraction |

### Steps

1. **Detect format** from file extension
2. **Extract text** using the appropriate library (see table above)
3. **Generate metadata**: title (from `--title` or filename), summary (first 500 chars + AI summary), tags
4. **Write vault note** to `research/files/{date}_{slug}.md` with Obsidian frontmatter:
   ```yaml
   ---
   title: "{title}"
   date: YYYY-MM-DD
   type: file_capture
   ingestion_type: manual
   source: file://{original_path}
   file_format: pdf / docx / xlsx / etc
   topics: [inferred or user-provided]
   tags: [file, {format}]
   ---
   ```
5. **Register** in `research/files/_index.yaml`
6. **Append** to `vault/log.md` per C-006
7. **If --deep**: activate `g-skl-res-deep` analysis on the captured content

### Edge Cases

| Situation | Behavior |
|-----------|----------|
| Scanned PDF (no text layer) | Write metadata-only stub with `analysis_depth: image_only`; body has "Text extraction not available — OCR required (Phase 3 T112)" |
| Password-protected file | Error: "File is encrypted. Decrypt before capture." |
| Unsupported format | Error with list of supported formats |
| File > 10MB | Warn; cap extraction at first 500KB; note truncation in frontmatter |
| `--title` not provided | Derive from filename (strip extension, replace underscores with spaces) |

---

## Output Path

`{vault_location}/research/files/{YYYY-MM-DD}_{slug}.md`
(vault_location from `.gald3r/.identity`)

---

## Prerequisites

```bash
pip install pdfminer.six python-docx openpyxl pandas striprtf
```

---

## See Also

- `@g-recon-url` — Capture web URLs
- `@g-recon-docs` — Capture documentation with revisit scheduling
- `@g-vault-ingest` — Manual vault note creation (no extraction)
