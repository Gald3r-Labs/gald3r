---
name: skl-linode-akamai
description: Linode/Akamai Cloud ΓÇö VPS (Linodes), LKE Kubernetes, Object Storage, managed databases, private networking, Docker deployment.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Linode / Akamai Cloud

Reliable cloud infrastructure now part of Akamai. Excellent global performance via Akamai CDN integration.

## Prerequisites

- `linode-cli`: `pip install linode-cli && linode-cli configure`
- API token from: https://cloud.linode.com/profile/tokens

## Operation: LINODE

VPS (Linode instance) management.

```bash
# List available types
linode-cli linodes types --text --no-headers | head -20

# List regions
linode-cli regions list --text --no-headers

# Create Linode
linode-cli linodes create \
  --type g6-nanode-1 \
  --region us-east \
  --image linode/ubuntu24.04 \
  --label my-server \
  --root_pass $(openssl rand -base64 16) \
  --authorized_keys "$(cat ~/.ssh/id_rsa.pub)"

# List Linodes
linode-cli linodes list --text

# SSH
linode-cli linodes ssh LINODE_ID --user root

# Create snapshot
linode-cli linodes snapshot LINODE_ID --label "snap-$(date +%Y%m%d)"

# Delete
linode-cli linodes delete LINODE_ID
```

**Resize a Linode:**
```bash
# Resize to larger plan (downsize requires disk resize first)
linode-cli linodes resize LINODE_ID \
  --type g6-standard-2 \
  --allow_auto_disk_resize true
# Linode will shut down, resize, and reboot automatically
# Check status:
linode-cli linodes view LINODE_ID --text | grep status
```

**Common instance types:**
| Type | vCPU | RAM | Storage | $/mo |
|------|------|-----|---------|------|
| g6-nanode-1 | 1 | 1 GB | 25 GB | $5 |
| g6-standard-1 | 1 | 2 GB | 50 GB | $12 |
| g6-standard-2 | 2 | 4 GB | 80 GB | $24 |
| g6-standard-4 | 4 | 8 GB | 160 GB | $48 |

## Operation: LKE

Linode Kubernetes Engine ΓÇö managed Kubernetes.

```bash
# List K8s versions
linode-cli lke versions-list --text

# Create cluster
linode-cli lke cluster-create \
  --label my-cluster \
  --region us-east \
  --k8s_version 1.30 \
  --node_pools.type g6-standard-2 \
  --node_pools.count 2

# Get kubeconfig
linode-cli lke kubeconfig-view CLUSTER_ID | base64 -d > ~/.kube/linode-config
export KUBECONFIG=~/.kube/linode-config

# List clusters
linode-cli lke clusters-list

# Delete cluster
linode-cli lke cluster-delete CLUSTER_ID
```

**Linode CCM & CSI drivers:**
The Linode Cloud Controller Manager (CCM) and Container Storage Interface (CSI) driver are pre-installed in LKE clusters.

```bash
# CCM handles NodeBalancer provisioning for LoadBalancer Services automatically:
# When you apply a Service of type LoadBalancer, LKE's CCM creates a NodeBalancer
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: my-lb
  annotations:
    service.beta.kubernetes.io/linode-loadbalancer-throttle: "4"
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
EOF

# CSI driver ΓÇö provision Linode Block Storage volumes:
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
  storageClassName: linode-block-storage
EOF

# Available storage classes
kubectl get storageclass
```

## Operation: OBJECT-STORAGE

S3-compatible object storage.

```bash
# Create bucket (via dashboard or API)
# CLI requires using S3-compatible tools

# Configure s3cmd
s3cmd --configure
# Endpoint: s3.us-east-1.linodeobjects.com
# Access/Secret from: cloud.linode.com/object-storage/access-keys

# Use with AWS CLI
aws s3 ls s3://my-bucket/ \
  --endpoint-url https://us-east-1.linodeobjects.com \
  --profile linode
```

**Lifecycle policies:**
```bash
# Apply lifecycle rules via s3cmd (expiry + transition)
s3cmd setlifecycle lifecycle.xml s3://my-bucket

# lifecycle.xml example:
cat > lifecycle.xml << 'EOF'
<?xml version="1.0" ?>
<LifecycleConfiguration>
  <Rule>
    <ID>expire-old-objects</ID>
    <Filter><Prefix>archive/</Prefix></Filter>
    <Status>Enabled</Status>
    <Expiration><Days>90</Days></Expiration>
  </Rule>
</LifecycleConfiguration>
EOF

# View current lifecycle config
s3cmd getlifecycle s3://my-bucket
```

**ACLs (access control):**
```bash
# Make bucket public read
s3cmd setacl s3://my-bucket --acl-public

# Make bucket private
s3cmd setacl s3://my-bucket --acl-private

# Set ACL on individual object
s3cmd setacl s3://my-bucket/file.txt --acl-public

# Via AWS CLI with Linode endpoint
aws s3api put-bucket-acl --bucket my-bucket --acl public-read \
  --endpoint-url https://us-east-1.linodeobjects.com
```

## Operation: DATABASE

Managed PostgreSQL, MySQL, Redis.

```bash
# Create PostgreSQL cluster
linode-cli databases postgresql-create \
  --label my-postgres \
  --region us-east \
  --type g6-nanode-1 \
  --engine_id postgresql/16 \
  --cluster_size 1

# List clusters
linode-cli databases list --text

# Get connection details
linode-cli databases postgresql-view DB_ID --text

# Create database user
linode-cli databases postgresql-user-create DB_ID --username myuser
```

**Failover configuration:**
```bash
# Create HA cluster (3-node for automatic failover)
linode-cli databases postgresql-create \
  --label my-postgres-ha \
  --region us-east \
  --type g6-standard-1 \
  --engine_id postgresql/16 \
  --cluster_size 3   # 3 = primary + 2 replicas, auto-failover included

# View replication/failover status
linode-cli databases postgresql-view DB_ID

# Standby replicas are promoted automatically if primary fails
# Read replica endpoint: use the database's read-only host from:
linode-cli databases postgresql-view DB_ID --text | grep read_only_host
```

## Operation: NETWORKING

Private networking, NodeBalancers (load balancers), firewalls.

```bash
# Create private VPC
linode-cli vpcs create \
  --label my-vpc \
  --region us-east \
  --subnets.label app-subnet \
  --subnets.ipv4 10.0.0.0/24

# Create NodeBalancer (load balancer)
linode-cli nodebalancers create \
  --label my-lb \
  --region us-east

# Create firewall
linode-cli firewalls create \
  --label web-fw \
  --rules.inbound '[{"action":"ACCEPT","protocol":"TCP","ports":"443,80","addresses":{"ipv4":["0.0.0.0/0"]}}]' \
  --rules.outbound_policy ACCEPT \
  --rules.inbound_policy DROP
```

**VLANs (private layer-2 networking):**
```bash
# Create Linode with VLAN interface (private network, no internet)
linode-cli linodes create \
  --type g6-standard-1 --region us-east \
  --image linode/ubuntu24.04 \
  --label app-server \
  --interfaces '[
    {"purpose":"public"},
    {"purpose":"vlan","label":"my-vlan","ipam_address":"10.0.0.2/24"}
  ]'

# VLANs are region-scoped; Linodes in same region + same VLAN label communicate privately
# No explicit creation step needed ΓÇö first use creates the VLAN
```

**Floating IPs (reassignable IPs):**
```bash
# Linode uses "IP sharing" rather than dedicated floating IPs
# Assign an IP to multiple Linodes for failover (both can announce it):

# 1. Purchase additional IP (requires ticket/justification for most plans)
linode-cli linodes ips-list LINODE_ID

# 2. Share an IP with another Linode (for failover via keepalived/BGP)
linode-cli linodes ip-addresses-share LINODE_ID \
  --ips '["192.0.2.1"]' \
  --linode_id TARGET_LINODE_ID

# 3. For true floating IPs, use NodeBalancers (load balancer) with backend Linodes
# The NodeBalancer IP stays fixed; backends can change freely
```

## Operation: DOCKER

Docker deployment with StackScripts or cloud-init.

```bash
# Create Linode with Docker via StackScript
linode-cli linodes create \
  --type g6-standard-1 --region us-east \
  --image linode/ubuntu24.04 \
  --stackscript_id 401697 \
  --label docker-server

# OR use cloud-init (user_data)
USER_DATA=$(cat << 'EOF' | base64 -w0
#cloud-config
packages: [docker.io, docker-compose-v2]
runcmd:
  - systemctl enable --now docker
  - usermod -aG docker ubuntu
EOF
)
linode-cli linodes create ... --metadata.user_data $USER_DATA
```

**UFW + Docker setup (Docker bypasses UFW by default):**
```bash
# After Docker is installed, apply this fix to prevent Docker bypassing UFW:

# 1. Edit /etc/ufw/after.rules ΓÇö add BEFORE the COMMIT line:
# *filter
# :DOCKER-USER - [0:0]
# -A DOCKER-USER -i eth0 -j DROP
# -A DOCKER-USER -i eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT
# COMMIT

# 2. Alternatively, use the ufw-docker utility:
sudo wget -O /usr/local/bin/ufw-docker \
  https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
sudo ufw-docker install

# 3. Allow specific container ports through UFW:
sudo ufw-docker allow my-container-name 8080/tcp

# 4. Reload UFW
sudo ufw reload

# Verification: ensure your container ports are NOT exposed without UFW:
sudo iptables -L DOCKER-USER -n
```
