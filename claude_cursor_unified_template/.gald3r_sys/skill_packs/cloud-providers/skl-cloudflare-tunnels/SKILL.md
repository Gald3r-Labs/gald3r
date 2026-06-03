---
name: skl-cloudflare-tunnels
description: Cloudflare Tunnels & Zero Trust ΓÇö expose local services securely, Zero Trust access policies, WARP client, Docker integration. No inbound firewall rules needed.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Cloudflare Tunnels & Zero Trust

Cloudflare Tunnel (`cloudflared`) creates outbound-only connections from your origin to Cloudflare's edge ΓÇö no open ports, no inbound firewall rules.

## Prerequisites

- Cloudflare account + zone (see `skl-cloudflare-dns`)
- `cloudflared` CLI: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
- Zero Trust account activated (free tier available): https://one.dash.cloudflare.com/

## Operation: TUNNEL

Create and manage tunnels.

```bash
# Authenticate cloudflared
cloudflared tunnel login

# Create a named tunnel
cloudflared tunnel create my-tunnel
# Note the tunnel ID from output

# List tunnels
cloudflared tunnel list

# Delete tunnel
cloudflared tunnel delete my-tunnel
```

## Operation: EXPOSE

Route traffic from a hostname to a local service.

**config.yml template:**
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: app.example.com
    service: http://localhost:3000
  - hostname: api.example.com
    service: http://localhost:8080
  - hostname: ssh.example.com
    service: ssh://localhost:22
  # Catch-all (required)
  - service: http_status:404
```

```bash
# Create DNS record pointing to tunnel
cloudflared tunnel route dns my-tunnel app.example.com

# Run tunnel
cloudflared tunnel run my-tunnel

# Run as service (Linux systemd)
cloudflared service install
systemctl start cloudflared
```

## Operation: ZERO-TRUST

Configure Zero Trust access policies (who can reach your services).

```bash
# Via Cloudflare dashboard: https://one.dash.cloudflare.com/
# Access > Applications > Add an application > Self-hosted

# Key settings:
# - Application domain: app.example.com
# - Policy: Allow email domain @yourcompany.com
#   OR: Allow specific emails
#   OR: Allow GitHub/Google OAuth with group rules
```

**Access policy types:**
| Type | Example |
|------|---------|
| Email | allow `@yourcompany.com` |
| GitHub org | require member of `your-org` |
| WARP device | require enrolled device |
| Service auth | machine-to-machine JWT |

## Operation: WARP

WARP client setup for device-level Zero Trust.

```bash
# Download WARP: https://1.1.1.1/
# Enroll device in Zero Trust org:
# WARP Settings > Account > Login with Cloudflare Zero Trust
# Enter team name from: dash.cloudflare.com > Zero Trust > Settings > Custom Pages
```

### Gateway policies (filter traffic from WARP devices)
```
# Via dashboard: Zero Trust > Gateway > Firewall Policies
# Create DNS policy (block categories):
# Rule: Block malware categories
#   Selector: Security Category = Malware, Command & Control
#   Action: Block

# Create HTTP policy (inspect HTTPS traffic):
# Rule: Block social media
#   Selector: Application = Facebook, TikTok, Instagram
#   Action: Block
# Requires WARP with TLS inspection certificate installed on device

# Create Network policy (block outbound by IP/port):
# Rule: Allow only corporate SSH
#   Selector: Destination Port = 22, Destination IP != 10.0.0.0/8
#   Action: Block
```

Key policy types:
| Type | Inspects | Common use |
|------|----------|-----------|
| DNS | DNS queries | Block malware/phishing/adult |
| HTTP | HTTP/HTTPS | App-level allow/block lists |
| Network | IP + port | Restrict outbound connections |

### Split tunneling (include/exclude mode)
```
# Via dashboard: Zero Trust > Settings > WARP Client > Device settings profile
# Split Tunnels mode:
# - Exclude: All traffic routes via WARP EXCEPT listed CIDRs/domains
#   Good for: send corporate traffic only, let personal traffic bypass
# - Include: ONLY listed CIDRs/domains route via WARP
#   Good for: route 10.x.x.x and internal.company.com through Zero Trust

# Common exclude list (personal traffic bypasses WARP):
# 192.168.0.0/16  (home LAN)
# 172.16.0.0/12   (RFC1918)
# *.netflix.com, *.youtube.com (streaming)

# Common include list (zero-trust only for corporate):
# 10.0.0.0/8      (corporate VPC)
# *.mycompany.com (internal services)
```

## Operation: DOCKER

Run `cloudflared` as a Docker container.

```yaml
# docker-compose.yml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    # OR with config file:
    # volumes:
    #   - ./cloudflared:/etc/cloudflared
    # command: tunnel --config /etc/cloudflared/config.yml run
```

```bash
# Get tunnel token (replaces config file approach)
cloudflared tunnel token my-tunnel
# Export as CLOUDFLARE_TUNNEL_TOKEN env var
```

## Common Patterns

**Expose local dev server temporarily:**
```bash
# Quick tunnel (no config needed, temp URL)
cloudflared tunnel --url http://localhost:3000
```

**SSH access without VPN:**
```bash
# Server side: add to config.yml
# hostname: ssh.example.com
# service: ssh://localhost:22

# Client side
cloudflared access ssh --hostname ssh.example.com
ssh user@ssh.example.com
```
