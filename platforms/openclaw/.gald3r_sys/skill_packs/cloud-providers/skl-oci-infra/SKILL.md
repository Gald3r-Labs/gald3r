---
name: skl-oci-infra
description: Oracle Cloud Infrastructure ΓÇö compute, VCN networking, OKE Kubernetes, Object Storage, OCI CLI. gald3r production cloud target.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---
# Oracle Cloud Infrastructure

**Activate for**: "OCI", "Oracle Cloud", "OKE", "OCI compute", "VCN", "Object Storage OCI", "oci cli"

---

## COMPUTE ΓÇö OCI Compute Instances

### Create an instance
```bash
oci compute instance launch --compartment-id $COMP_ID --availability-domain "AD-1" \
  --shape "VM.Standard.A1.Flex" --shape-config '{"ocpus":2,"memoryInGBs":12}' \
  --image-id $IMG_ID --subnet-id $SUB_ID --ssh-authorized-keys-file ~/.ssh/id_rsa.pub
```

### Shapes
| Shape | Type | OCPUs | Use for |
|-------|------|-------|---------|
| VM.Standard.A1.Flex | ARM (Free) | 1ΓÇô4 | gald3r Docker, dev servers |
| VM.Standard.E4.Flex | AMD | 1ΓÇô64 | General workloads |
| BM.Standard.A1.160 | Bare Metal | 160 | High-performance |

---

## VCN ΓÇö Virtual Cloud Network

```bash
oci network vcn create --compartment-id $COMP_ID --cidr-blocks '["10.0.0.0/16"]' --display-name "gald3r-vcn"
oci network internet-gateway create --compartment-id $COMP_ID --vcn-id $VCN_ID --is-enabled true
oci network subnet create --compartment-id $COMP_ID --vcn-id $VCN_ID --cidr-block "10.0.1.0/24"
```

### gald3r port rules (NSG)
```bash
oci network nsg add-security-rules --nsg-id $NSG_ID --security-rules '[
  {"direction":"INGRESS","protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":8092,"max":8092}},"description":"MCP server"},
  {"direction":"INGRESS","protocol":"6","source":"10.0.0.0/16","tcpOptions":{"destinationPortRange":{"min":5433,"max":5433}},"description":"Postgres"},
  {"direction":"INGRESS","protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"min":22,"max":22}},"description":"SSH"}
]'
```

---

## OKE ΓÇö Oracle Kubernetes Engine

```bash
oci ce cluster create --compartment-id $COMP_ID --name "gald3r-oke" --vcn-id $VCN_ID --kubernetes-version "v1.30.1"
oci ce cluster create-kubeconfig --cluster-id $CLUSTER_ID --file ~/.kube/config --token-version 2.0.0
kubectl get nodes
```

---

## OBJECT-STORAGE

```bash
oci os ns get  # Get namespace
oci os bucket create --compartment-id $COMP_ID --name "gald3r-backups" --namespace $NS
oci os object put --bucket-name gald3r-backups --file backup.tar.gz --name "2026-04-19.tar.gz"
```

S3-compatible endpoint: `https://<namespace>.compat.objectstorage.<region>.oraclecloud.com`

**Pre-Authenticated Requests (PAR ΓÇö temporary anonymous access URLs):**
```bash
# Create PAR for object download (expires in 7 days)
oci os preauth-request create \
  --bucket-name gald3r-backups \
  --name "backup-download-link" \
  --access-type ObjectRead \
  --time-expires "$(date -u -d '+7 days' '+%Y-%m-%dT%H:%M:%SZ')" \
  --object-name "2026-04-19.tar.gz" \
  --namespace $NS

# Returns a full access URI like:
# https://objectstorage.us-ashburn-1.oraclecloud.com/p/TOKEN/n/NAMESPACE/b/BUCKET/o/OBJECT

# Create PAR for bucket-level upload (CI/CD artifact upload)
oci os preauth-request create \
  --bucket-name gald3r-backups \
  --name "ci-upload-par" \
  --access-type AnyObjectWrite \
  --time-expires "$(date -u -d '+30 days' '+%Y-%m-%dT%H:%M:%SZ')" \
  --namespace $NS

# List PARs
oci os preauth-request list --bucket-name gald3r-backups --namespace $NS

# Delete PAR
oci os preauth-request delete --bucket-name gald3r-backups --par-id PAR_ID --namespace $NS
```

**Object Storage lifecycle rules (auto-archive/delete):**
```bash
# Set lifecycle policy (archive objects after 30 days, delete after 365)
oci os object-lifecycle-policy put \
  --bucket-name gald3r-backups \
  --namespace $NS \
  --items '[
    {
      "name": "archive-old",
      "action": "ARCHIVE",
      "timeAmount": 30,
      "timeUnit": "DAYS",
      "isEnabled": true,
      "objectNameFilter": {"inclusionPrefixes": ["backups/"]}
    },
    {
      "name": "delete-expired",
      "action": "DELETE",
      "timeAmount": 365,
      "timeUnit": "DAYS",
      "isEnabled": true
    }
  ]'

# Get current lifecycle policy
oci os object-lifecycle-policy get --bucket-name gald3r-backups --namespace $NS
```

---

## CLI ΓÇö Setup

Config file: `~/.oci/config`
```ini
[DEFAULT]
user=ocid1.user.oc1..aaa...
fingerprint=xx:xx:xx:...
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaa...
region=us-ashburn-1
```

---

## DOCKER-ON-OCI ΓÇö gald3r Stack Deployment

```yaml
#cloud-config
packages: [docker.io, docker-compose-plugin, git]
runcmd:
  - systemctl enable docker && systemctl start docker
  - ufw allow 22/tcp && ufw allow 8092/tcp && ufw allow 443/tcp && ufw --force enable
```

---

## FREE-TIER ΓÇö Always Free Limits

| Resource | Limit |
|----------|-------|
| ARM Compute | 4 OCPUs + 24GB RAM |
| Block Volume | 200GB (2 volumes) |
| Object Storage | 20GB |
| Autonomous DB | 2 instances (1 OCPU + 20GB each) |
| Outbound data | 10TB/month |
