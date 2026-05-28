---
name: skl-vultr
description: Vultr Cloud ΓÇö VPS, bare metal, Kubernetes (VKE), Object Storage, private networking, Docker deployment, billing management.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Vultr Cloud

High-performance cloud with bare metal options and competitive pricing. Global datacenter network.

## Prerequisites

- `vultr-cli`: https://github.com/vultr/vultr-cli#installation
- Auth: `export VULTR_API_KEY=your_key` (from https://my.vultr.com/settings/#settingsapi)

## Operation: VPS

Virtual machine (Vultr calls them "instances") management.

```bash
# List available plans
vultr-cli plans list --type vc2 | head -20

# List OS options
vultr-cli os list | grep -i ubuntu

# Create instance
vultr-cli instance create \
  --region ewr \
  --plan vc2-1c-1gb \
  --os 1743 \
  --label my-server \
  --ssh-keys YOUR_SSH_KEY_ID

# List instances
vultr-cli instance list --output human

# SSH
vultr-cli instance ssh INSTANCE_ID

# Snapshot
vultr-cli snapshot create --instance-id INSTANCE_ID --description "pre-deploy $(date +%Y%m%d)"

# Delete
vultr-cli instance delete INSTANCE_ID
```

**VPS plans (vc2 ΓÇö shared compute):**
| Plan | vCPU | RAM | Storage | $/mo |
|------|------|-----|---------|------|
| vc2-1c-1gb | 1 | 1 GB | 25 GB | $6 |
| vc2-1c-2gb | 1 | 2 GB | 55 GB | $12 |
| vc2-2c-4gb | 2 | 4 GB | 80 GB | $24 |
| vc2-4c-8gb | 4 | 8 GB | 160 GB | $48 |

## Operation: BARE-METAL

Dedicated physical servers ΓÇö no virtualization overhead.

```bash
# List bare metal plans
vultr-cli bare-metal plans list

# Create bare metal server
vultr-cli bare-metal create \
  --region ewr \
  --plan vbm-4c-32gb \
  --os 1743 \
  --label my-bare-metal

# List bare metal
vultr-cli bare-metal list
```

## Operation: KUBERNETES

Vultr Kubernetes Engine (VKE) ΓÇö managed Kubernetes.

```bash
# Create cluster
vultr-cli kubernetes create \
  --label my-cluster \
  --region ewr \
  --version 1.30 \
  --node-pools "quantity:2,plan:vc2-2c-4gb,label:default"

# Get kubeconfig
vultr-cli kubernetes config CLUSTER_ID > ~/.kube/vultr-config
export KUBECONFIG=~/.kube/vultr-config

# List clusters
vultr-cli kubernetes list

# Delete cluster
vultr-cli kubernetes delete CLUSTER_ID
```

## Operation: STORAGE

Vultr Object Storage (S3-compatible).

```bash
# Create object storage cluster
vultr-cli object-storage create --cluster-id 2 --label my-storage

# List
vultr-cli object-storage list

# Get access keys (for S3-compatible tools)
vultr-cli object-storage get STORAGE_ID

# Use with AWS CLI (S3-compatible)
# Endpoint: https://ewr1.vultrobjects.com
aws s3 ls s3://my-bucket/ \
  --endpoint-url https://ewr1.vultrobjects.com \
  --profile vultr
```

## Operation: NETWORKING

VPC, load balancers, reserved IPs.

```bash
# Create VPC
vultr-cli vpc2 create \
  --region ewr \
  --description my-network \
  --ip-block 10.0.0.0/24

# Create load balancer
vultr-cli load-balancer create \
  --region ewr \
  --label my-lb \
  --forwarding-rules "frontend_protocol:HTTPS,frontend_port:443,backend_protocol:HTTP,backend_port:80"

# Reserve IP (keep IP across instance rebuilds)
vultr-cli reserved-ip create --region ewr --type v4 --label my-ip
```

## Operation: DOCKER

Docker deployment on Vultr instances.

```bash
# Cloud-init to install Docker on create
cat > cloud-init.yaml << 'EOF'
#cloud-config
package_update: true
packages:
  - docker.io
  - docker-compose-v2
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu
EOF

vultr-cli instance create \
  --region ewr --plan vc2-1c-2gb --os 2284 \
  --user-data "$(base64 -w0 cloud-init.yaml)"
```

## Operation: BILLING

```bash
# Current billing
vultr-cli billing history list

# Get invoices
vultr-cli billing invoice list

# Set spending limit (dashboard only)
# my.vultr.com > Billing > Spending Limit
```
