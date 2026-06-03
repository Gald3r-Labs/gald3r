---
name: skl-cloudflare-workers
description: Cloudflare Workers & Pages ΓÇö scaffolding, deployment, KV/D1/R2/Durable Objects storage, debug, secrets. Depends on skl-cloudflare-dns for zone setup.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Cloudflare Workers & Pages

Serverless compute at the edge. Workers handle HTTP logic; Pages deploys static sites with Workers Functions.

## Prerequisites

- Cloudflare account + active zone (see `skl-cloudflare-dns`)
- `wrangler` CLI: `npm install -g wrangler` then `wrangler login`

## Operation: SCAFFOLD

Initialize a new Worker or Pages project.

```bash
# New Worker
wrangler init my-worker --type javascript
cd my-worker

# New Pages project (connected to git)
wrangler pages project create my-site
```

**wrangler.toml template (full bindings):**
```toml
name = "my-worker"
main = "src/index.js"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]

[vars]
ENVIRONMENT = "production"

# KV Namespace
[[kv_namespaces]]
binding = "MY_KV"
id = "YOUR_KV_NAMESPACE_ID"

# D1 SQLite database
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "YOUR_D1_DATABASE_ID"

# R2 Object Storage
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-worker-bucket"

# Durable Objects
[[durable_objects.bindings]]
name = "MY_DO"
class_name = "MyDurableObject"

# Workers AI
[ai]
binding = "AI"

# Service bindings (call another Worker)
[[services]]
binding = "AUTH_WORKER"
service = "my-auth-worker"
```

## Operation: DEPLOY

Deploy to Cloudflare's edge network.

```bash
# Deploy Worker
wrangler deploy

# Deploy to specific environment
wrangler deploy --env production

# Deploy Pages
wrangler pages deploy ./dist --project-name my-site --branch main

# Preview deploy (no traffic)
wrangler deploy --dry-run
```

**Custom domains on Workers:**
```bash
# Add a custom domain (requires zone in same Cloudflare account)
wrangler deploy --route "app.example.com/*"

# OR define in wrangler.toml
# routes = [{ pattern = "app.example.com/*", zone_name = "example.com" }]

# Custom domain via dashboard:
# Workers & Pages > your-worker > Settings > Domains & Routes > Add Custom Domain
# Enter: app.example.com ΓåÆ Cloudflare will create a CNAME record automatically

# List current routes
wrangler route list --zone-id $ZONE_ID
```

## Operation: STORAGE

Bindings for persistent storage within Workers.

### KV (Key-Value)
```bash
wrangler kv:namespace create MY_STORE
wrangler kv:key put --namespace-id=<id> "key" "value"
wrangler kv:key get --namespace-id=<id> "key"
```

### D1 (SQLite at Edge)
```bash
wrangler d1 create my-database
wrangler d1 execute my-database --command "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
wrangler d1 execute my-database --file schema.sql
```

### R2 (Object Storage)
```bash
wrangler r2 bucket create my-bucket
wrangler r2 object put my-bucket/path/file.txt --file ./local.txt
```

### Durable Objects
Add to `wrangler.toml`:
```toml
[[durable_objects.bindings]]
name = "MY_DO"
class_name = "MyDurableObject"
```

## Operation: PAGES

Pages-specific operations.

```bash
# List projects
wrangler pages project list

# View deployments
wrangler pages deployment list --project-name my-site

# Rollback
wrangler pages deployment create --project-name my-site --branch=rollback-branch
```

## Operation: DEBUG

Local development and troubleshooting.

```bash
# Local dev server with live reload
wrangler dev

# Tail production logs
wrangler tail my-worker

# View analytics
wrangler analytics my-worker
```

## Operation: SECRETS

Manage Worker secrets (environment variables not visible in code).

```bash
wrangler secret put API_KEY
wrangler secret list
wrangler secret delete API_KEY
```

## Common Patterns

**Fetch handler (Workers):**
```javascript
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/api/data") {
      const val = await env.MY_KV.get("data");
      return new Response(JSON.stringify({ val }), {
        headers: { "Content-Type": "application/json" }
      });
    }
    return new Response("Not found", { status: 404 });
  }
};
```

**Cron trigger:**
```toml
[triggers]
crons = ["0 */6 * * *"]
```
