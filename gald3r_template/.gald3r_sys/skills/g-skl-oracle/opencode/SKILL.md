---
name: g-skl-oracle
description: >
  Execute Oracle Database queries and operations via gald3r_valhalla MCP tools.
  Requires Docker backend (adv tier). Supports read-only queries (oracle_query)
  and full write operations (oracle_execute) including DDL and PL/SQL blocks.
version: 1.0.0
min_tier: adv
triggers:
  - "oracle query"
  - "oracle execute"
  - "run oracle"
  - "query the database"
  - "oracle sql"
  - "select from oracle"
  - "insert into oracle"
  - g-oracle
requires:
  - gald3r_valhalla MCP server (Docker backend)
  - oracle_query MCP tool
  - oracle_execute MCP tool
---

# g-skl-oracle

**Requires**: gald3r_valhalla Docker backend + `oracle_query` / `oracle_execute` MCP tools.

**Activate for**: Oracle SQL queries, data reads, schema inspection, inserts/updates/deletes, DDL operations, PL/SQL blocks.

---

## Operations

### QUERY — Read-only SQL

Use `oracle_query` for any SELECT, DESCRIBE, EXPLAIN, or WITH (CTE). Blocks all write operations at the tool level.

**Required parameters** (all per-call — no env defaults):
| Param | Description |
|---|---|
| `sql` | SELECT / DESCRIBE / EXPLAIN / WITH query |
| `host` | Oracle hostname |
| `port` | Oracle port (default: 1521) |
| `username` | Oracle username |
| `password` | Oracle password |
| `service_name` | Oracle service name |
| `vals` | Query parameters: list (positional `?`) or dict (named `:name`) — optional |

**Returns**: `rows`, `columns`, `column_types`, `row_count`

**Example invocation**:
```
oracle_query(
  sql="SELECT table_name FROM all_tables WHERE owner = :owner ORDER BY 1",
  host="oracle.example.com",
  username="myuser",
  password="mypass",
  service_name="ORCL",
  vals={"owner": "MYSCHEMA"}
)
```

---

### EXECUTE — Write-enabled SQL

Use `oracle_execute` for INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE, GRANT, REVOKE, and PL/SQL blocks. Also accepts SELECT (returns result set).

**Required parameters**: same as QUERY above.

**Additional capabilities**:
- **Bulk operations**: pass `vals` as a list of dicts → uses `executemany`
- **PL/SQL blocks**: wrap in `BEGIN ... END;`
- **DDL**: CREATE TABLE, ALTER TABLE, DROP TABLE, etc.

**Example — bulk insert**:
```
oracle_execute(
  sql="INSERT INTO audit_log (event, ts) VALUES (:event, SYSDATE)",
  host="oracle.example.com", username="myuser", password="mypass", service_name="ORCL",
  vals=[{"event": "login"}, {"event": "query"}, {"event": "logout"}]
)
```

**Returns**: `query_type`, `rows_affected` (DML/DDL) OR `rows`/`columns` (SELECT)

---

## Security Rules

- **Never log passwords** — connection params are per-call and ephemeral
- **Read before write** — always run `oracle_query` to inspect current state before destructive `oracle_execute`
- **Parameterize everything** — never interpolate user input directly into SQL strings
- **DDL is irreversible** — confirm DROP / TRUNCATE operations explicitly before executing
- Any data loss → **"Loki's mischief"** (see BSG/Norse personality system)

---

## Connection Pattern

Oracle credentials are **never stored in .gald3r/ or vault files**. Always:
1. Read credentials from environment variables or user-supplied context
2. Pass per-call to `oracle_query` / `oracle_execute`
3. Never commit credentials to any file

Typical env var pattern:
```powershell
$env:ORACLE_HOST     = "oracle.internal"
$env:ORACLE_USER     = "appuser"
$env:ORACLE_PASS     = "..."      # from secret store
$env:ORACLE_SERVICE  = "PROD"
```

---

## Error Categories

| Category | Meaning | Action |
|---|---|---|
| `CONNECTION` | Can't reach Oracle | Check host/port/service_name, VPN |
| `AUTHENTICATION` | Bad credentials | Verify username/password |
| `SECURITY` | Blocked write in oracle_query | Switch to oracle_execute |
| `VALIDATION` | Empty SQL or too large | Fix the query |
| `PARAMETER` | Bind variable mismatch | Check `vals` matches placeholders |
| `ORACLE_ERROR` | DB-level error (ORA-XXXXX) | Read the ORA message |

---

## Availability Check

Before using this skill, verify the backend is up:
```
gald3r_server_status()
```
If unavailable: **this skill does not work in slim or full tier installs** — Oracle access requires the gald3r_valhalla Docker backend.
