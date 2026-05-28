---
name: skl-cloudflare-dns
description: Cloudflare DNS & domain management ΓÇö zones, records, SSL/TLS, page rules, wrangler CLI, bulk operations. Foundation for Workers and Tunnels skills.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---
# Cloudflare DNS & Domains

**Activate for**: "Cloudflare DNS", "DNS record", "Cloudflare zone", "SSL certificate", "wrangler DNS", "CF API", "nameserver"

---

## ZONE ΓÇö Zone Management

### Add a zone
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"name":"example.com","type":"full"}'
```

Zone types: `full` (CF authoritative), `partial` (CNAME setup), `secondary` (mirror). After creating, update registrar nameservers to the assigned pair.

---

## RECORDS ΓÇö DNS Record CRUD

### Record types
| Type | Use | Proxy? |
|------|-----|--------|
| A/AAAA | IPv4/IPv6 address | Yes (orange cloud) |
| CNAME | Alias | Yes |
| MX | Mail server | Never |
| TXT | SPF, DKIM, verification | Never |
| SRV | Service discovery | Never |
| CAA | Certificate authority auth | Never |

### Create a record
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  --data '{"type":"A","name":"@","content":"93.184.216.34","ttl":1,"proxied":true}'
```

### Proxy toggle (orange vs grey cloud)
- **Proxied (orange)**: DDoS protection, WAF, caching, hides origin IP
- **DNS-only (grey)**: Direct resolution, needed for MX, SRV, non-HTTP

### TTL guidance
| Scenario | TTL |
|----------|-----|
| Proxied records | Auto (300s) |
| Stable DNS-only | 3600ΓÇô86400 |
| Pre-migration | 300 (lower first) |

---

## SSL ΓÇö SSL/TLS Configuration

| Mode | Origin requirement | Security |
|------|-------------------|----------|
| Full (Strict) | Valid cert | **Recommended** |
| Full | Self-signed cert | Encrypted, no validation |
| Flexible | None | BrowserΓåÆCF only |

Always use **Full (Strict)** with Cloudflare Origin CA or Let's Encrypt.

### HSTS (HTTP Strict Transport Security)
```bash
# Enable HSTS via Cloudflare API (Zone Settings)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/strict_transport_security" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  --data '{"value":{"enabled":true,"max_age":31536000,"include_subdomains":true,"preload":true}}'
```
| Setting | Value | Notes |
|---------|-------|-------|
| max_age | 31536000 | 1 year ΓÇö required for preload |
| include_subdomains | true | All subdomains enforced |
| preload | true | Submit to HSTS preload list |

**Certificate management:**
```bash
# Order Cloudflare-issued Advanced Certificate (custom hostnames)
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/ssl/certificate_packs" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  --data '{"type":"advanced","hosts":["example.com","*.example.com"],"validation_method":"txt","validity_days":365,"certificate_authority":"google","cloudflare_branding":false}'

# List certificate packs
curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/ssl/certificate_packs" \
  -H "Authorization: Bearer $CF_API_TOKEN"

# Check SSL status
curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/ssl/verification" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

---

## PAGE-RULES ΓÇö URL-Based Overrides (Legacy)

**Note**: Page Rules are deprecated. Use **Rules** (Transform, Redirect, Cache) for new setups.

| Page Rule | New Rule Type |
|-----------|--------------|
| Always Use HTTPS | Configuration Rule |
| Forwarding URL | Redirect Rule |
| Cache Level | Cache Rule |

---

## WRANGLER ΓÇö CLI & API Auth

### Token scopes
| Scope | What it allows |
|-------|---------------|
| `Zone:DNS:Edit` | Create/update/delete records |
| `Zone:Zone:Read` | List zones |
| `Zone:Zone Settings:Edit` | SSL, caching settings |

### Auth methods
| Method | Header | Recommendation |
|--------|--------|----------------|
| API Token | `Authorization: Bearer $CF_API_TOKEN` | **Preferred** ΓÇö scoped |
| API Key (legacy) | `X-Auth-Email` + `X-Auth-Key` | Avoid ΓÇö full access |

### Wrangler DNS CLI commands
```bash
# Install wrangler
npm install -g wrangler && wrangler login

# List DNS records for a zone
wrangler dns record list --zone-id $ZONE_ID

# Create DNS record
wrangler dns record create \
  --zone-id $ZONE_ID \
  --type A \
  --name app \
  --content 93.184.216.34 \
  --proxied \
  --ttl 1

# Update a DNS record (need record ID first)
wrangler dns record update RECORD_ID \
  --zone-id $ZONE_ID \
  --content 93.184.216.35

# Delete a DNS record
wrangler dns record delete RECORD_ID --zone-id $ZONE_ID

# Get zone ID from domain name
wrangler zones list
# OR
wrangler zones inspect example.com
```

---

## BULK ΓÇö Bulk Operations

```bash
# Export all records
curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/export" \
  -H "Authorization: Bearer $CF_API_TOKEN" > dns_backup.txt

# Import from BIND
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/import" \
  -H "Authorization: Bearer $CF_API_TOKEN" --form "file=@dns_records.txt"
```

---

## Notes

- API rate limit: 1200 requests per 5 minutes per user
- Cross-reference: skl-cloudflare-workers for Workers routing, skl-cloudflare-tunnels for Tunnel DNS
