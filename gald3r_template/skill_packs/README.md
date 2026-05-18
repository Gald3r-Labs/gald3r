# skill_packs/ — Optional Installable Skill Collections

Domain-specific skills that are not part of the default gald3r install.
Browse the packs, pick what you need, run `install.ps1`.

## Available Packs

| Pack | Skills | Install |
|------|--------|---------|
| [ai-video-tools](./ai-video-tools/PACK.md) | AI video generation, Remotion, explainer videos, ad specs | `.\skill_packs\ai-video-tools\install.ps1` |
| [ai-media](./ai-media/PACK.md) | Seedance 2.0 text/image-to-video, Higgsfield DoP cinematic video | `.\skill_packs\ai-media\install.ps1` |
| [3d-graphics](./3d-graphics/PACK.md) | 3D performance, animation principles, asset optimization | `.\skill_packs\3d-graphics\install.ps1` |
| [content-creation](./content-creation/PACK.md) | Social media marketing, storyboards, explainer videos, ad specs | `.\skill_packs\content-creation\install.ps1` |
| [ai-ml-dev](./ai-ml-dev/PACK.md) | ML development, cloud GPU training, Manim animations | `.\skill_packs\ai-ml-dev\install.ps1` |
| [startup-tools](./startup-tools/PACK.md) | VC fundraising, business formation, product dev, resource access | `.\skill_packs\startup-tools\install.ps1` |
| [blockchain](./blockchain/PACK.md) | Web3 and blockchain development | `.\skill_packs\blockchain\install.ps1` |
| [infrastructure](./infrastructure/PACK.md) | Cloud engineering, Kubernetes, CI/CD, MCP builder | `.\skill_packs\infrastructure\install.ps1` |
| [cloud-providers](./cloud-providers/PACK.md) | AWS IAM, Cloudflare DNS, Hetzner Cloud, Oracle Cloud (OCI) | `.\skill_packs\cloud-providers\install.ps1` |
| [community](./community/PACK.md) | Discord server management, Telegram bots & channels | `.\skill_packs\community\install.ps1` |

## How to Install

```powershell
# Install a pack into the current project
.\skill_packs\infrastructure\install.ps1

# Install into a specific project
.\skill_packs\infrastructure\install.ps1 -ProjectRoot "C:\my-project"
```

After install, restart your IDE to load the new skills.

## How to Uninstall

Delete the skill directories listed in the pack's `PACK.md` under **FILES**.

## Design Principles

- **Inert at rest** — skill_packs/ does not auto-load. Skills deploy only when you run `install.ps1`.
- **No loader hacks** — files copy into standard IDE skill paths (`.cursor/skills/`, `.claude/skills/`, etc.)
- **5 IDE targets** — each pack deploys to `.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`
- **No default gald3r pollution** — none of these are included in the base install

## Adding a New Pack

1. Create `skill_packs/{pack-name}/` with `PACK.md`, `install.ps1`, and `files/`
2. Populate `files/` with the 5 IDE target directories and SKILL.md files
3. Add a row to this README
