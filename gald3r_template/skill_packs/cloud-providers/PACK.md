# Pack: cloud-providers

Cloud infrastructure management — AWS, Cloudflare, Hetzner, Oracle Cloud, DigitalOcean, Vultr, Linode/Akamai, and Google Cloud.

## What This Installs

**Cloudflare:**
- `skl-cloudflare-dns` — DNS zones, records, SSL/TLS, wrangler CLI, bulk operations
- `skl-cloudflare-workers` — Workers, Pages, KV/D1/R2/Durable Objects, Cron triggers
- `skl-cloudflare-tunnels` — Tunnels, Zero Trust access policies, WARP, Docker integration

**AWS:**
- `skl-aws-iam` — IAM users/roles/policies, STS, Secrets Manager, 5 policy templates
- `skl-aws-compute` — EC2, Lambda, ECS, App Runner, CDK patterns
- `skl-aws-storage` — S3 (with bucket policy templates), RDS, DynamoDB, EFS, Backup
- `skl-aws-networking` — VPC (3-tier template), Route 53, CloudFront, ALB, VPN, peering

**Other Vendors:**
- `skl-hetzner` — VPS, dedicated, Object Storage, hcloud CLI, Docker cloud-init
- `skl-digitalocean` — Droplets, App Platform (app spec template), managed DBs, DOKS, Spaces
- `skl-vultr` — VPS, bare metal, VKE Kubernetes, Object Storage, Docker
- `skl-linode-akamai` — Linodes, LKE Kubernetes, Object Storage, managed DBs, NodeBalancer
- `skl-gemini-cloud` — Gemini API, Vertex AI, Cloud Run, GCP setup, grounding, cost mgmt
- `skl-vercel-gaps` — gald3r install on Vercel, MCP URL wiring, secrets, monorepo, deploy hooks

**Oracle Cloud:**
- `skl-oci-infra` — Compute, VCN networking, OKE Kubernetes, Object Storage, OCI CLI
- `skl-oracle-db` — Autonomous DB, SQL/PLSQL patterns, Thick mode, ORDS REST, MCP tools

## Prerequisites

Install only the provider CLIs you need:
- AWS: `pip install awscli && aws configure`
- Cloudflare: `npm install -g wrangler && wrangler login`
- DigitalOcean: `snap install doctl` or https://docs.digitalocean.com/reference/doctl/
- Hetzner: `brew install hcloud` or https://github.com/hetznercloud/cli
- GCP: https://cloud.google.com/sdk/docs/install
- OCI: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
- Vultr: https://github.com/vultr/vultr-cli#installation
- Linode: `pip install linode-cli && linode-cli configure`

## Install

```powershell
.\skill_packs\cloud-providers\install.ps1
.\skill_packs\cloud-providers\install.ps1 -ProjectRoot "C:\my-project"
.\skill_packs\cloud-providers\install.ps1 -List
```

## Uninstall

Delete the skill directories listed above from your project's `.cursor/skills/`, `.claude/skills/`, etc.

## FILES

15 skills × 5 IDE targets = 75 files. Run `.\install.ps1 -List` for the full list.
