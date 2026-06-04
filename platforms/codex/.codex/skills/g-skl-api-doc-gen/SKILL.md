---
name: g-skl-api-doc-gen
description: Auto-generate OpenAPI 3.1 specs from FastAPI/Express/Flask routes; fill docstring gaps for undocumented functions; update README API tables. Covers Python FastAPI, Express.js, and Flask. Also generates MCP tool descriptions for FastMCP plugins.
token_budget: medium
subsystem_memberships: [BUG_AND_QUALITY, PLATFORM_INTEGRATION]
---
# g-skl-api-doc-gen

**Activate for**: `@g-api-doc-gen`, "generate API docs", "write OpenAPI spec", "document this endpoint", "add docstrings", "update README API table", "FastAPI docs", "FastMCP tool descriptions".

---

## Step 1: Detect API Framework

```
Scan entry points and imports for:
  FastAPI:   from fastapi import FastAPI  /  app = FastAPI()
  Flask:     from flask import Flask      /  @app.route(...)
  Express:   express = require('express') /  app.get(...) / router.post(...)
  FastMCP:   from fastmcp import FastMCP  /  @mcp.tool()  (gald3r_valhalla)
```

---

## Step 2: Extract Route Signatures

### FastAPI
```python
# Parse @router.get / @router.post / @app.get / @app.post decorators
# Extract: path, method, response_model, tags, summary if present
# Extract function signature: parameter names, types, defaults
# Extract existing docstring (if any)
```

### Flask
```python
# Parse @app.route / @blueprint.route decorators
# Extract: path, methods=[...], function signature
```

### Express.js
```javascript
// Parse router.get / router.post / app.get / app.post / router.use
// Extract: path, handler function params
```

### FastMCP plugins (gald3r_valhalla)
```python
# Parse TOOL_NAME, TOOL_DESCRIPTION, TOOL_PARAMS dicts
# Extract execute() function signature and return type
```

---

## Step 3: Generate Missing Docstrings

For each route or function without a docstring (or with a single-line placeholder):

```python
# Template for FastAPI endpoint:
async def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user account.

    Args:
        user: User creation payload with email, password, and display name.

    Returns:
        UserResponse: The newly created user with generated ID and timestamps.

    Raises:
        HTTPException 409: If email already registered.
        HTTPException 422: If input validation fails.
    """
    ...
```

Rules:
- Use existing parameter type hints; infer semantics from name + context
- Flag parameters with no type hint (`# TODO: add type hint`)
- For `Optional[X]` parameters: add "Optional." to description

---

## Step 4: Generate OpenAPI 3.1 Spec

### Output format
```yaml
openapi: 3.1.0
info:
  title: <project_name> API
  version: <version_from_pyproject_or_package_json>
  description: <first paragraph of README if available>
paths:
  /endpoint:
    post:
      summary: Short one-line summary
      description: Full docstring body
      tags: [tag1, tag2]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InputModel'
      responses:
        '200':
          description: Success response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OutputModel'
        '422':
          description: Validation error
components:
  schemas:
    InputModel:
      type: object
      properties:
        field_name:
          type: string
          description: ...
```

### FastAPI auto-export shortcut
If FastAPI is running or accessible:
```python
# In Python console or test:
import json
from app.main import app
print(json.dumps(app.openapi(), indent=2))
```

Use this as the base and augment with missing descriptions.

---

## Step 5: Update README API Table

Find the `## API` or `## Endpoints` section in README.md.
If it doesn't exist, offer to create one.

Format:
```markdown
## API Reference

### POST /users
Create a new user account.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | Minimum 8 characters |
| display_name | string | No | Public display name |

**Response** `200`:
```json
{"id": "uuid", "email": "...", "created_at": "..."}
```
```

---

## Step 6: FastMCP Plugin Documentation

For gald3r_valhalla plugins, generate a standardized doc block:

```python
"""
<TOOL_NAME> MCP Tool

<one-paragraph description from TOOL_DESCRIPTION>

Parameters:
    param1 (str): Description from TOOL_PARAMS["param1"]
    param2 (int, optional): Description from TOOL_PARAMS["param2"]. Defaults to N.

Returns:
    dict: {
        "success": bool,
        "result": ...,   # on success
        "error": str,    # on failure
    }

Example:
    tool_name(param1="value", param2=42)
"""
```

---

## Step 7: Output Artifacts

Generate (as appropriate for the project):

1. `docs/openapi.yaml` — full OpenAPI 3.1 spec
2. `docs/openapi.json` — JSON format (for tools that prefer JSON)
3. Inline docstring patches — show diffs for each file
4. README.md API section update

Offer to write files directly or show diffs for review.

---

## Quality Checks

Before finalizing:
- [ ] All endpoints have a `summary` field
- [ ] All request bodies have example values
- [ ] Error responses (4xx/5xx) documented
- [ ] No undocumented path parameters
- [ ] Consistent tag taxonomy

---

## Integration Notes

- Invoke after completing any endpoint addition task
- Works well after `g-skl-code-review` identifies undocumented routes
- Pair with `g-skl-dependency-audit` for a full pre-release quality pass
