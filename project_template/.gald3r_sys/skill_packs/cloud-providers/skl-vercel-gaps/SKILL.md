---
name: skl-vercel-gaps
description: Vercel integration gaps for gald3r projects ΓÇö covers areas the Cursor Vercel plugin doesn't handle. gald3r install on Vercel projects, MCP server deployment, secrets management, monorepo support.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Vercel Integration Gaps for gald3r

> **For general Vercel usage (deploying Next.js/React, env vars UI, preview deployments, routing middleware, AI SDK, storage, etc.), use the Vercel plugin skills in Cursor.**
> Activate those skills via `@vercel` commands or the Vercel Cursor plugin.
> **This skill only covers the gald3r-specific gaps** that the Vercel plugin does not handle ΓÇö see the coverage map below.

The Cursor Vercel plugin covers frontend deployment well. This skill fills the remaining gaps for gald3r-powered projects deployed on Vercel.

## Operation: COVERAGE-MAP

What the Vercel Cursor plugin handles vs what this skill fills.

| Area | Cursor Plugin | This Skill |
|------|--------------|-----------|
| Deploy Next.js/React | Γ£à | ΓÇö |
| Environment variables (UI) | Γ£à | ΓÇö |
| Preview deployments | Γ£à | ΓÇö |
| gald3r install on Vercel project | Γ¥î | Γ£à |
| MCP server URL wiring | Γ¥î | Γ£à |
| Secret injection for gald3r services | Γ¥î | Γ£à |
| Monorepo config (nx/turborepo) | Partial | Γ£à |
| Edge function debugging | Partial | Γ£à |
| Deploy hooks (build triggers) | Γ¥î | Γ£à |

## Operation: GALD3R-INSTALL

Install gald3r task management into a Vercel-deployed project.

```bash
# Install Vercel CLI
npm i -g vercel

# Link project
vercel link

# Pull env vars to local .env
vercel env pull .env.local

# Install gald3r into the project
# From <gald3r_source> repo:
#   gald3r_install(project_path="path/to/vercel-project", project_name="my-site")
# OR manual: copy <ECOSYSTEM_ROOT>/<template_full>/.gald3r/ to your project

# Add .gald3r/ to .gitignore (gald3r task data is local)
echo ".gald3r/" >> .gitignore
```

## Operation: MCP-SERVER

Wire gald3r MCP server URL into a Vercel project.

```bash
# Add MCP URL as Vercel environment variable
vercel env add GALD3R_MCP_URL production
# Enter: https://your-gald3r-server.example.com

vercel env add GALD3R_MCP_URL preview
# Can use same or staging URL

# Pull to local for testing
vercel env pull .env.local
# .env.local will contain GALD3R_MCP_URL=...

# Add to .mcp.json in project root (for Cursor MCP integration)
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "gald3r": {
      "url": "${GALD3R_MCP_URL}/mcp",
      "transport": "http"
    }
  }
}
EOF
```

## Operation: ENV-SECRETS

Manage secrets needed by gald3r tools and skills deployed on Vercel.

```bash
# Add secrets (encrypted at rest, injected at runtime)
vercel env add ANTHROPIC_API_KEY production
vercel env add OPENAI_API_KEY production
vercel env add DATABASE_URL production

# List env vars
vercel env ls

# Remove
vercel env rm ANTHROPIC_API_KEY production

# Promote from preview to production
vercel env pull --environment=preview .env.preview
# Edit .env.preview, then push to production
vercel env add KEY production < .env.preview
```

**Security rules for gald3r secrets on Vercel:**
- Never put secrets in `vercel.json` (it's committed to git)
- Use Vercel environment variables for all API keys
- Scope secrets to the minimum environment needed (preview vs production)
- Rotate secrets via `vercel env rm` ΓåÆ `vercel env add`

## Operation: MONOREPO

gald3r in a Turborepo or Nx monorepo deployed on Vercel.

**vercel.json for monorepo:**
```json
{
  "buildCommand": "cd ../.. && npx turbo run build --filter=web",
  "installCommand": "cd ../.. && npm install",
  "outputDirectory": "apps/web/.next",
  "framework": "nextjs"
}
```

```bash
# Override root directory
vercel --cwd apps/web

# Build specific workspace
vercel build --yes

# Turborepo remote cache with Vercel
# Set TURBO_TOKEN and TURBO_TEAM in env vars
# turborepo.json: { "remoteCache": { "enabled": true } }
```

## Vercel Deploy Hooks (Build Triggers)

Trigger Vercel deployments from gald3r tasks or CI.

```bash
# Create deploy hook (Vercel dashboard: Settings > Git > Deploy Hooks)
# Returns URL like: https://api.vercel.com/v1/integrations/deploy/prj_xxx/xxx

# Trigger deploy
curl -X POST https://api.vercel.com/v1/integrations/deploy/prj_xxx/xxx

# Trigger from PowerShell (gald3r hook)
Invoke-RestMethod -Method POST -Uri $env:VERCEL_DEPLOY_HOOK_URL
```
