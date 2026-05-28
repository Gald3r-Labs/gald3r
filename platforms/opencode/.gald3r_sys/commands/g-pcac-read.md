Review and action the cross-project INBOX: $ARGUMENTS

## What This Command Does

Opens `.gald3r/linking/INBOX.md`, triages items by type, and routes each to the appropriate response action. CONFLICTs are surfaced first and block all other work until resolved. Uses `g-skl-pcac-read`.

## Workflow

### 1. Read INBOX
Open `.gald3r/linking/INBOX.md`.

If no INBOX exists → output: "INBOX not configured. Run task007 to set up the linking/ directory."
If INBOX is empty → output: "INBOX: clear"

### 2. Classify Items
Sort by priority:
```
1. [CONFLICT]  → ⚠️ BLOCK all other work until resolved
2. [REQUEST]   → child needs parent action
3. [BROADCAST] → parent sent work (verify task exists)
4. [SYNC]      → sibling contract update
```

### 3. Handle CONFLICTs First
For each CONFLICT:
- Show both conflicting instructions side by side
- Identify affected subsystem
- Ask user: "Follow A / Follow B / Follow both / Ignore both / Custom?"
- Record resolution in the CONFLICT entry
- Mark `[DONE]` before proceeding

**No other work proceeds until all CONFLICTs are resolved.**

### 4. Handle Remaining Items
- **REQUEST**: Action or escalate — create task or reply
- **BROADCAST**: Verify the referenced task exists in TASKS.md; if not, create it
- **SYNC**: Update `linking/peers/{sender_name}.md` with new contract data; mark `[DONE]`

### 5. Mark Processed Items
Append `[DONE] — {date} — {action taken}` to each processed item.

## Usage Examples

```
@g-pcac-read
```

## Delegates To
`g-skl-pcac-read`
