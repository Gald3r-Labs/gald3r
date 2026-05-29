---
name: skl-oracle-db
description: Oracle Database ΓÇö Autonomous Database, SQL/PLSQL patterns, Thick mode client, ORDS REST API, gald3r MCP tools integration, migration from other databases.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Oracle Database

Enterprise-grade relational database. Autonomous Database (ADB) on OCI is the primary gald3r deployment target.

## Prerequisites

- Oracle Cloud account (see `skl-oci-infra` for OCI setup)
- Python: `pip install oracledb` (for Thick mode: Oracle Instant Client required)
- SQL*Plus: bundled with Instant Client or ORDS

## Operation: ADB

Autonomous Database ΓÇö Oracle's fully managed, self-tuning database.

```bash
# Create Autonomous Database (ATP ΓÇö Transaction Processing)
oci db autonomous-database create \
  --compartment-id $OCI_COMPARTMENT_ID \
  --display-name my-adb \
  --db-name myadb \
  --admin-password "SecurePass123#" \
  --cpu-core-count 1 \
  --data-storage-size-in-tbs 1 \
  --db-workload ATP \
  --is-free-tier true

# Get connection details
oci db autonomous-database get --autonomous-database-id $ADB_ID

# Download wallet (credentials package)
oci db autonomous-database generate-wallet \
  --autonomous-database-id $ADB_ID \
  --password WalletPass123# \
  --file wallet.zip
unzip wallet.zip -d ~/wallet

# Configure tnsnames.ora (set TNS_ADMIN)
export TNS_ADMIN=~/wallet
```

## Operation: CONNECT

Connection patterns for different clients.

**Python (oracledb ΓÇö thin mode, no Instant Client needed):**
```python
import oracledb

# DSN format
conn = oracledb.connect(
    user="admin",
    password=os.environ["ORACLE_PASSWORD"],
    dsn="adb-hostname:1521/myadb_tp"
)

# With wallet (ADB)
conn = oracledb.connect(
    user="admin",
    password=os.environ["ORACLE_PASSWORD"],
    dsn="myadb_tp",
    config_dir=os.environ["TNS_ADMIN"],
    wallet_location=os.environ["TNS_ADMIN"],
    wallet_password=os.environ["WALLET_PASSWORD"]
)
```

**Thick mode (for advanced features: sharding, Oracle objects):**
```python
import oracledb
oracledb.init_oracle_client()  # Uses ORACLE_HOME or LD_LIBRARY_PATH
conn = oracledb.connect(user="admin", password="...", dsn="...")
```

**Connection pool pattern (recommended for web apps and APIs):**
```python
import oracledb
import os

# Create pool at application startup (not per-request)
pool = oracledb.create_pool(
    user=os.environ["ORACLE_USER"],
    password=os.environ["ORACLE_PASSWORD"],
    dsn=os.environ["ORACLE_DSN"],
    config_dir=os.environ.get("TNS_ADMIN"),
    wallet_location=os.environ.get("TNS_ADMIN"),
    wallet_password=os.environ.get("WALLET_PASSWORD"),
    min=2,       # minimum open connections
    max=10,      # maximum connections in pool
    increment=1  # connections opened when pool exhausted
)

# Acquire connection from pool (auto-released on context exit)
def query_users(status: str):
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username FROM users WHERE status = :status",
                status=status
            )
            return cur.fetchall()

# FastAPI / Flask lifecycle example:
# @app.on_event("startup") ΓåÆ create pool
# @app.on_event("shutdown") ΓåÆ pool.close()

# Graceful shutdown
def shutdown():
    pool.close(force=False)   # wait for active connections to finish
    # pool.close(force=True)  # immediate (drop all connections)
```

**SQL*Plus:**
```bash
sqlplus admin@myadb_tp  # Prompts for password
# OR
sqlplus admin/"password"@myadb_tp
```

## Operation: SQL

Oracle SQL patterns and differences from PostgreSQL/MySQL.

```sql
-- String concatenation (Oracle uses || not CONCAT for portability)
SELECT first_name || ' ' || last_name AS full_name FROM employees;

-- Dual table (Oracle-specific dummy table)
SELECT SYSDATE FROM DUAL;
SELECT 1+1 FROM DUAL;

-- Pagination (Oracle 12c+ FETCH FIRST)
SELECT * FROM employees ORDER BY salary DESC FETCH FIRST 10 ROWS ONLY;
SELECT * FROM employees ORDER BY salary DESC OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY;

-- Auto-increment (Oracle 12c+ IDENTITY columns)
CREATE TABLE users (
  id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR2(100) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- MERGE (upsert)
MERGE INTO users dst USING (SELECT 'alice' username FROM DUAL) src
ON (dst.username = src.username)
WHEN NOT MATCHED THEN INSERT (username) VALUES (src.username);

-- JSON support
SELECT j.data.name.string_value FROM json_table_data j WHERE j.id = 1;
```

## Operation: PLSQL

Stored procedures, functions, triggers.

```sql
-- Stored procedure
CREATE OR REPLACE PROCEDURE update_user_status(
  p_user_id IN NUMBER,
  p_status  IN VARCHAR2
) AS
BEGIN
  UPDATE users SET status = p_status WHERE id = p_user_id;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('Updated user ' || p_user_id);
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RAISE_APPLICATION_ERROR(-20001, 'User not found: ' || p_user_id);
END update_user_status;
/

-- Function
CREATE OR REPLACE FUNCTION get_user_name(p_id IN NUMBER) RETURN VARCHAR2 AS
  v_name VARCHAR2(200);
BEGIN
  SELECT first_name || ' ' || last_name INTO v_name FROM users WHERE id = p_id;
  RETURN v_name;
EXCEPTION WHEN NO_DATA_FOUND THEN RETURN NULL;
END;
/

-- Execute
EXEC update_user_status(42, 'ACTIVE');
SELECT get_user_name(42) FROM DUAL;
```

## Operation: ORDS

Oracle REST Data Services ΓÇö automatic REST APIs from database tables.

```bash
# Enable ORDS on ADB (via OCI console or SQL)
-- Enable REST for a schema
BEGIN
  ORDS.ENABLE_SCHEMA(p_enabled => TRUE, p_schema => 'ADMIN',
    p_url_mapping_type => 'BASE_PATH', p_url_mapping_pattern => 'admin');
END;
/

-- AutoREST on a table (generates GET/POST/PUT/DELETE automatically)
BEGIN
  ORDS.ENABLE_OBJECT(p_enabled => TRUE, p_schema => 'ADMIN',
    p_object => 'USERS', p_object_type => 'TABLE',
    p_object_alias => 'users');
END;
/
```

ORDS endpoints follow: `https://your-adb-host/ords/admin/users/`

## Operation: MCP-TOOLS

Using gald3r's oracle_query and oracle_execute MCP tools.

```python
# gald3r MCP tools connect via connection string from environment
# oracle_query: SELECT only (safe for reporting agents)
result = oracle_query(
    sql="SELECT id, username, status FROM users WHERE status = :status",
    params={"status": "ACTIVE"}
)

# oracle_execute: DML + DDL (requires explicit agent permission)
oracle_execute(
    sql="UPDATE users SET status = :status WHERE id = :id",
    params={"status": "INACTIVE", "id": 42}
)
```

Connection configured via `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD` in gald3r MCP server config.

## Operation: MIGRATION

Migrate from PostgreSQL or MySQL to Oracle.

**Key differences:**
| Feature | PostgreSQL | Oracle |
|---------|-----------|--------|
| Auto-increment | SERIAL / IDENTITY | GENERATED AS IDENTITY |
| String type | VARCHAR / TEXT | VARCHAR2(n) |
| Boolean | BOOLEAN | NUMBER(1) or CHAR(1) |
| NOW() | NOW() | SYSDATE |
| LIMIT/OFFSET | LIMIT n OFFSET m | FETCH FIRST n ROWS / OFFSET m ROWS |
| Schema | Public schema | User = schema |
| Transactions | Auto-commit off | Auto-commit ON by default |

```bash
# AWS Schema Conversion Tool (SCT) for automated schema migration
# https://docs.aws.amazon.com/SchemaConversionTool/

# Oracle SQL Developer Data Pump for data migration
expdp admin/pass@myadb_tp FULL=y DUMPFILE=export.dmp
impdp admin/pass@target FULL=y DUMPFILE=export.dmp
```
