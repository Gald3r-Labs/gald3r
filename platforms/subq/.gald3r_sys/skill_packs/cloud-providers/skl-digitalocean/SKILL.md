---
name: skl-digitalocean
description: DigitalOcean ΓÇö Droplets, App Platform, managed PostgreSQL/MySQL/Redis, Spaces object storage, Kubernetes (DOKS), networking. App spec YAML template included.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# DigitalOcean

Developer-friendly cloud platform. Simple pricing, excellent docs, strong managed services.

## Prerequisites

- `doctl` CLI: https://docs.digitalocean.com/reference/doctl/how-to/install/
- Auth: `doctl auth init` (requires API token from https://cloud.digitalocean.com/account/api/tokens)

## Operation: DROPLET

Virtual machine lifecycle.

```bash
# List available images
doctl compute image list --public --format Slug,Distribution | grep -i ubuntu

# Create Droplet
doctl compute droplet create my-server \
  --image ubuntu-24-04-x64 \
  --size s-1vcpu-1gb \
  --region nyc3 \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -1) \
  --wait

# List Droplets
doctl compute droplet list --format ID,Name,PublicIPv4,Status,Region

# SSH
doctl compute ssh my-server

# Snapshot
doctl compute droplet-action snapshot DROPLET_ID --snapshot-name "my-snap-$(date +%Y%m%d)"

# Resize Droplet (requires power off first for permanent disk resize)
doctl compute droplet-action power-off DROPLET_ID --wait
doctl compute droplet-action resize DROPLET_ID \
  --size s-2vcpu-4gb \
  --resize-disk=false \  # false = CPU/RAM only (live resize), true = disk too (irreversible)
  --wait
doctl compute droplet-action power-on DROPLET_ID

# Reserved IPs (static IPs that survive Droplet rebuilds)
doctl compute reserved-ip create --region nyc3
doctl compute reserved-ip list --format IP,Region,DropletID
doctl compute reserved-ip-action assign RESERVED_IP DROPLET_ID
doctl compute reserved-ip-action unassign RESERVED_IP

# Destroy
doctl compute droplet delete my-server --force
```

**Droplet sizes (common):**
| Slug | vCPU | RAM | Disk | $/mo |
|------|------|-----|------|------|
| s-1vcpu-1gb | 1 | 1 GB | 25 GB | $6 |
| s-1vcpu-2gb | 1 | 2 GB | 50 GB | $12 |
| s-2vcpu-2gb | 2 | 2 GB | 60 GB | $18 |
| s-2vcpu-4gb | 2 | 4 GB | 80 GB | $24 |

## Operation: APP-PLATFORM

Managed PaaS ΓÇö deploy from Git, Docker, or container registry. No server management.

**app-spec.yaml template:**
```yaml
name: my-app
region: nyc
services:
  - name: api
    github:
      repo: youruser/yourrepo
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: uvicorn main:app --host 0.0.0.0 --port 8080
    http_port: 8080
    instance_size_slug: basic-xxs
    instance_count: 1
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
        type: SECRET
databases:
  - name: db
    engine: PG
    version: "16"
    size: db-s-dev-database
```

```bash
# Deploy from spec
doctl apps create --spec app-spec.yaml

# List apps
doctl apps list --format ID,Spec.Name,DefaultIngress,Phase

# Get deployment logs
doctl apps logs APP_ID --tail

# Update app
doctl apps update APP_ID --spec app-spec.yaml

# Delete
doctl apps delete APP_ID --force
```

## Operation: DATABASE

Managed databases (PostgreSQL, MySQL, Redis, MongoDB).

```bash
# Create PostgreSQL cluster
doctl databases create my-postgres \
  --engine pg --version 16 \
  --size db-s-1vcpu-1gb --region nyc3 --num-nodes 1

# List clusters
doctl databases list --format ID,Name,Engine,Status,URI

# Get connection string
doctl databases connection my-postgres --format URI

# Create database + user
doctl databases db create CLUSTER_ID mydb
doctl databases user create CLUSTER_ID myuser

# Add trusted source (restrict access)
doctl databases firewalls append CLUSTER_ID --rule droplet:DROPLET_ID
doctl databases firewalls append CLUSTER_ID --rule ip_addr:YOUR_IP/32
```

**PgBouncer / connection pooling:**
```bash
# DigitalOcean managed PostgreSQL includes built-in PgBouncer
# Enable via dashboard: Database > Connection Pools > Create Pool

# Or via API:
doctl databases pool create CLUSTER_ID \
  --name my-pool \
  --mode transaction \        # transaction | session | statement
  --size 20 \                 # max connections from pool to database
  --db defaultdb \
  --user doadmin

# Get pool connection string
doctl databases pool get CLUSTER_ID my-pool --format Connection

# Pool modes:
# transaction ΓÇö recommended for web apps (connection freed per transaction)
# session     ΓÇö connection held until client disconnects (use for LISTEN/NOTIFY)
# statement   ΓÇö finest granularity (no multi-statement transactions)
```

## Operation: SPACES

S3-compatible object storage.

```bash
# Configure s3cmd or rclone (Spaces uses S3 API)
# Endpoint: https://REGION.digitaloceanspaces.com
# Key/Secret from: cloud.digitalocean.com/spaces ΓåÆ Manage Keys

# Using aws CLI with Spaces
aws s3 ls --endpoint-url https://nyc3.digitaloceanspaces.com s3://my-space/
aws s3 cp file.txt s3://my-space/path/ --endpoint-url https://nyc3.digitaloceanspaces.com

# Using doctl
doctl spaces create my-space --region nyc3
doctl spaces list
```

## Operation: NETWORKING

Load balancers, firewalls, VPCs.

```bash
# Create load balancer
doctl compute load-balancer create \
  --name my-lb --region nyc3 \
  --forwarding-rules entry_protocol:https,entry_port:443,target_protocol:http,target_port:80,certificate_id:CERT_ID \
  --droplet-ids DROPLET_ID1,DROPLET_ID2 \
  --health-check protocol:http,port:80,path:/health

# Create firewall
doctl compute firewall create \
  --name web-fw \
  --inbound-rules "protocol:tcp,ports:443,sources:addresses:0.0.0.0/0,0::/0 protocol:tcp,ports:80,sources:addresses:0.0.0.0/0,0::/0" \
  --outbound-rules "protocol:tcp,ports:all,destinations:addresses:0.0.0.0/0" \
  --droplet-ids DROPLET_ID
```

## Operation: KUBERNETES

DigitalOcean Kubernetes (DOKS).

```bash
# Create cluster
doctl kubernetes cluster create my-k8s \
  --region nyc3 --version 1.30 \
  --node-pool "name=default;size=s-2vcpu-2gb;count=2"

# Get kubeconfig
doctl kubernetes cluster kubeconfig save my-k8s

# List clusters
doctl kubernetes cluster list

# Upgrade
doctl kubernetes cluster upgrade my-k8s --version 1.31
```

## Operation: BILLING

Cost awareness.

```bash
# Current month usage
doctl billing balance get

# Invoice history
doctl billing history list

# Alert when bill exceeds threshold (via dashboard)
# Dashboard > Billing > Create Billing Alert
```
