# Pack: 3d-graphics

3D performance optimization, asset pipelines, animation principles, generative art, and AI-powered 3D generation for web and game projects.

## What This Installs

- `trellis2-gguf` — Local AI image-to-3D pipeline via ComfyUI GGUF (6GB+ VRAM); characters, props, architectural exteriors; feeds Blender/game engine pipeline
- `3d-performance` — LOD strategies, frustum/occlusion culling, draw call reduction, R3F-specific optimizations
- `asset-optimization` — gltf-transform pipeline: Draco mesh compression, WebP/KTX2 textures, LOD generation
- `animation-principles` — Disney's 12 animation principles applied to 3D/game contexts, timing & frame count guidelines
- `algorithmic-art` — p5.js generative art: seeded randomness, flow fields, particle systems, interactive parameters

## Prerequisites

- For `trellis2-gguf`: Nvidia GPU 6GB+ VRAM, Windows 10/11, ComfyUI Easy Install + Trellis 2 base install; then run installer bat from `pixel-artistry.com/trellis2gguf`
- For `asset-optimization`: `npm install -g @gltf-transform/cli` + optional KTX-Software
- For `algorithmic-art`: p5.js (CDN or `npm install p5`)

## Install

```powershell
.\skill_packs\3d-graphics\install.ps1
.\skill_packs\3d-graphics\install.ps1 -ProjectRoot "C:\my-project"
```

## Uninstall

Delete these skill directories from your project's `.cursor/skills/`, `.agent/skills/`, etc.:
- `trellis2-gguf/`, `3d-performance/`, `asset-optimization/`, `animation-principles/`, `algorithmic-art/`

## FILES

- `.cursor/skills/trellis2-gguf/SKILL.md`
- `.cursor/skills/3d-performance/SKILL.md`
- `.cursor/skills/asset-optimization/SKILL.md`
- `.cursor/skills/animation-principles/SKILL.md`
- `.cursor/skills/algorithmic-art/SKILL.md`
- `.agent/skills/trellis2-gguf/SKILL.md`
- `.agent/skills/3d-performance/SKILL.md`
- `.agent/skills/asset-optimization/SKILL.md`
- `.agent/skills/animation-principles/SKILL.md`
- `.agent/skills/algorithmic-art/SKILL.md`
- `.claude/skills/trellis2-gguf/SKILL.md`
- `.claude/skills/3d-performance/SKILL.md`
- `.claude/skills/asset-optimization/SKILL.md`
- `.claude/skills/animation-principles/SKILL.md`
- `.claude/skills/algorithmic-art/SKILL.md`
- `.codex/skills/trellis2-gguf/SKILL.md`
- `.codex/skills/3d-performance/SKILL.md`
- `.codex/skills/asset-optimization/SKILL.md`
- `.codex/skills/animation-principles/SKILL.md`
- `.codex/skills/algorithmic-art/SKILL.md`
- `.opencode/skills/trellis2-gguf/SKILL.md`
- `.opencode/skills/3d-performance/SKILL.md`
- `.opencode/skills/asset-optimization/SKILL.md`
- `.opencode/skills/animation-principles/SKILL.md`
- `.opencode/skills/algorithmic-art/SKILL.md`
