# Skill Packs

Skill packs are optional add-on skill collections not part of gald3r core. Users can
install none, some, or all packs simultaneously.

## Available Packs

| Pack | Tier | Skills |
|---|---|---|
| `3d-graphics` | adv | 3d-performance, algorithmic-art, animation-principles, asset-optimization, trellis2-gguf |
| `ai-media` | adv | higgsfield, stable-diffusion |
| `ai-ml-dev` | full | ai-development, ml-operations, model-training |
| `ai-video-tools` | adv | 8 video production skills |
| `blockchain` | full | web3-blockchain |
| `cloud-providers` | full | 15 cloud provider skills (AWS, Cloudflare, OCI, etc.) |
| `community` | slim | skl-discord, skl-slack, skl-telegram |
| `content-creation` | slim | explainer-video, social-media-marketing, storyboard-creation, video-ad-specs |
| `infrastructure` | full | cicd-pipelines, cloud-engineering, kubernetes-operations, mcp-builder |
| `startup-tools` | slim | business-formation, product-development, resource-access, vc-fundraising |

## Commands

```
g-skill-pack-list               List all packs and install status
g-skill-pack-add <pack> [skill] Install a full pack or single skill
g-skill-pack-del <pack> [skill] Remove a pack or single skill
g-skill-pack-save <skill>       Save evolved skill back to pack registry
```

## Architecture

Each pack stores a single canonical copy in ``:

```
<pack-name>/
  source/
    skills/        ← one subfolder per skill, same as gald3r core skills
  PACK.md          ← version, tier, skill list
  install.py       ← platform-aware installer (imports the shared _install_helper.py)
```

## Evolved Skills

If you customize a skill, rename your version to `<skill-name>_evolved/` in your IDE folder.
`g-skill-pack-del` will skip `_evolved` skills (warns instead of deleting).
`g-skill-pack-save` packages your evolved version back into the registry.
