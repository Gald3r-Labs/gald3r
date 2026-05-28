---
name: skl-hetzner
description: Hetzner Cloud ΓÇö VPS, dedicated servers, Object Storage, networking, hcloud CLI, Docker deployment with cloud-init templates.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---
# Hetzner Cloud

**Activate for**: "Hetzner", "hcloud", "Hetzner VPS", "Hetzner dedicated", "Hetzner Object Storage"

---

## SERVER ΓÇö Cloud Servers

```bash
hcloud server create --name gald3r-mcp --type cpx21 --image ubuntu-24.04 \
  --ssh-key my-key --location fsn1 --user-data-from-file cloud-init.yaml
```

### Types
| Type | vCPUs | RAM | EUR/mo | Line |
|------|-------|-----|--------|------|
| CX22 | 2 shared | 4GB | ~4 | Intel |
| CPX21 | 3 AMD | 4GB | ~5 | AMD |
| CAX21 | 4 ARM | 8GB | ~5 | Ampere |
| CCX23 | 2 dedicated | 8GB | ~15 | Dedicated |

---

## NETWORK ΓÇö Private Networks & Firewalls

```bash
hcloud network create --name gald3r-net --ip-range 10.0.0.0/16
hcloud firewall create --name gald3r-fw
hcloud firewall add-rule gald3r-fw --direction in --protocol tcp --port 22 --source-ips 0.0.0.0/0
hcloud firewall add-rule gald3r-fw --direction in --protocol tcp --port 8092 --source-ips 0.0.0.0/0
hcloud firewall apply-to-resource gald3r-fw --type server --server gald3r-mcp
```

---

## STORAGE ΓÇö Object Storage & Volumes

### Object Storage (S3-compatible)
Endpoint: `https://<bucket>.fsn1.your-objectstorage.com`
```bash
aws s3 --profile hetzner --endpoint-url https://fsn1.your-objectstorage.com mb s3://gald3r-backups
```

### Block volumes
```bash
hcloud volume create --name gald3r-data --size 50 --server gald3r-mcp --format ext4
```

---

## DOCKER ΓÇö Deployment Workflow

### Cloud-init template
```yaml
#cloud-config
packages: [docker.io, docker-compose-plugin, git, ufw]
runcmd:
  - systemctl enable docker && systemctl start docker
  - ufw default deny incoming && ufw allow 22/tcp && ufw allow 8092/tcp && ufw allow 443/tcp && ufw --force enable
```

**UFW + Docker caveat**: Docker bypasses UFW by default. Add `DOCKER-USER` chain rules to `/etc/ufw/after.rules`.

---

## DNS ΓÇö Hetzner DNS

```bash
hcloud server set-rdns gald3r-mcp --ip <IP> --hostname mcp.gald3r.dev
```
Zone management via `https://dns.hetzner.com/` or API with `Auth-API-Token`.

---

## DEDICATED ΓÇö Robot Servers

Manage at `robot.hetzner.com`. Use `installimage` in rescue mode for OS install with software RAID.

### KVM remote console access
KVM (Keyboard-Video-Mouse) gives you direct console access to a dedicated server ΓÇö useful when SSH is broken or during OS install.

```bash
# 1. Order KVM console from robot.hetzner.com:
#    Server > KVM Console > Enable KVM (costs ~Γé¼5 one-time or by request)

# 2. Alternatively, use Rescue System for emergency access:
#    robot.hetzner.com > Server > Rescue > Activate Linux rescue
#    Then reboot server ΓÇö it boots into a minimal Linux environment accessible via SSH

# 3. Use hcloud Serial Console (cloud servers ΓÇö not dedicated):
hcloud server console <server-name>
# Opens a WebSocket-based serial console directly in the CLI
# Ctrl+] to exit

# 4. Access via Robot API (dedicated):
curl -u "$ROBOT_USER:$ROBOT_PASS" \
  "https://robot-ws.your-server.de/server/$SERVER_IP"
# Returns server status, IP, location, and hardware info
```

| Method | Use case | Cost |
|--------|----------|------|
| hcloud console (cloud) | Debug unbootable cloud server | Free |
| Robot KVM (dedicated) | Full BIOS/GRUB access | ~Γé¼5/request |
| Robot Rescue (dedicated) | SSH into emergency Linux | Free |

---

## BILLING

- Hourly billing with monthly cap
- **Powered off = still billed** ΓÇö delete to stop charges
- Snapshots: free to create, billed per GB stored
- Backups: ~20% of server price/month
