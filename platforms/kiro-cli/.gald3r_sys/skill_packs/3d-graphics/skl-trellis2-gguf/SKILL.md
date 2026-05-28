---
name: trellis2-gguf
description: "Trellis 2 GGUF ΓÇö local image-to-3D pipeline in ComfyUI on 6GB+ VRAM. Generates full 3D meshes with textures + UV unwrap from a single image. Use for characters, props, hard-surface assets, and architectural exteriors. NOT for room interiors, text-to-3D, or scene composition."
tags: [3d, ai, trellis2, gguf, comfyui, image-to-3d, blender, local-ai, low-vram]
skill_group: "3d-graphics"
skill_category: "3D Graphics & Rendering"
---

# Trellis 2 GGUF ΓÇö Local Image-to-3D

Open-source image-to-3D pipeline running fully locally, free, in ComfyUI. Generates textured 3D meshes with UV unwrap from a single input image. GGUF quantization allows 6GB VRAM GPUs (RTX 3050/4060 class) to run a 4B-parameter model ΓÇö faster than the full uncompressed version.

> **Research note**: Full video analysis in `research/videos/2026-04-15_trellis2-gguf-6gb-vram-local-3d.md`

---

## When to Use

- Converting a reference image (photo, concept art, sprite) into a 3D mesh with textures
- Generating hero props, characters, or architectural exteriors for game scenes
- Rapidly prototyping 3D assets for import into Blender or game engines
- Replacing or supplementing paid cloud services like Meshy for image-to-3D tasks
- Running 3D generation locally on 6ΓÇô16GB VRAM consumer GPUs

## When NOT to Use

- Interior rooms, floor plans, or scene layouts ΓåÆ use SketchUp or manual modeling
- Text/prompt to 3D ΓåÆ use Meshy, Tripo3D, or 3DAIStudio (cloud)
- Rigging or animation ΓåÆ downstream Blender/Maya step, not this tool
- Production-ready topology ΓåÆ always retopo output in ZBrush, 3DA Studio, or Blender

---

## VRAM & Quantization Guide

| Quantization | VRAM Peak | Generation Time | Recommended For |
|---|---|---|---|
| **Q4** (most compressed) | ~6.1 GB | ~8 min | RTX 3050, 4060 (6 GB cards) |
| Q5 | ~7ΓÇô8 GB | ~7ΓÇô8 min | 8 GB cards |
| Q6 | ~8ΓÇô9 GB | ~7 min | 8ΓÇô10 GB cards |
| **Q8** (best quality/speed) | ~8.9 GB | ~7 min 9s | 8ΓÇô16 GB cards |
| Full safetensor | ~10ΓÇô11 GB | ~10 min 8s | 16+ GB only |

**Key fact**: GGUF Q4 uses ~half the VRAM of the full model and runs ~2 minutes faster.

---

## Prerequisites

```
- Nvidia GPU with 6+ GB VRAM (CUDA required)
- Windows 10 or 11
- ComfyUI Easy Install (installed first)
- Trellis 2 default installation (prerequisite for the GGUF fork)
```

---

## Installation

### Step 1 ΓÇö Install GGUF Fork

1. Download `install_trellis2_gguf.bat` from `pixel-artistry.com/trellis2gguf`
2. Drop into your ComfyUI add-ons folder
3. Double-click ΓÇö installs the ArrowX GGUF ComfyUI fork + all dependencies
4. Wait for completion (internet speed dependent, ~5ΓÇô10 min)

### Step 2 ΓÇö Download GGUF Model Weights

1. Download `download_trellis2_gguf.bat` from the same link
2. Drop into the add-ons folder and run
3. Auto-downloads all quantized model files, encoders, decoders, configs
4. Grab a coffee ΓÇö model download takes time

### Step 3 ΓÇö Load ComfyUI Workflow

1. Launch ComfyUI ΓÇö ignore any red errors at startup (model path resolution, non-fatal)
2. Load the GGUF workflow from `pixel-artistry.com/trellis2gguf`
3. **Do NOT reuse old Trellis 2 workflows** ΓÇö GGUF uses different nodes

---

## ComfyUI Workflow Structure

The GGUF workflow replaces the standard `Trellis 2 Model Loader` with the `GGUF Load Model` node:

```
[Image Input] ΓåÆ [GGUF Load Model (Q4/Q5/Q6/Q8)]
     Γåô
[Mesh Generation] ΓåÆ [Mesh Refinement]
     Γåô
[Texturing (4K)] ΓåÆ [UV Unwrap]
     Γåô
[Export: GLB / OBJ]
```

### Key Node: GGUF Load Model

- Dropdown for quantization level: Q4 / Q5 / Q6 / Q8 / safetensor
- **For 6 GB VRAM**: select `Q4_K_M`
- Models must be pre-downloaded (Step 2)

---

## Output Quality by Asset Type

| Asset Type | Quality | Notes |
|---|---|---|
| Organic characters | Excellent | Primary use case ΓÇö fine detail (claws, spikes) preserved at Q4 |
| Hard surface / mechanical | Good | Dense topology, geometry correct; may need retopo |
| Architectural exterior | Good | Windows, balconies, overhangs hold up |
| Interior rooms | Not supported | Image-to-object only; no spatial reconstruction |
| Vegetation / foliage | Moderate | Complex silhouettes can struggle |

---

## Post-Processing Pipeline

Trellis 2 output is a **draft mesh** ΓÇö production use requires downstream steps:

```
Trellis 2 Output (GLB)
    Γåô
Retopologize in:
  - 3DA Studio (cloud retopo)
  - ZBrush (manual or ZRemesher)
  - Blender (Remesh modifier or manual)
    Γåô
Rig in Blender / Maya / Mixamo
    Γåô
Export to game engine
```

**Why retopo is needed**: Trellis 2 outputs dense, unstructured topology. Fine for static background assets or further sculpting. Needs clean edge loops for rigging.

---

## Low VRAM Troubleshooting (6 GB cards)

If you hit OOM errors during generation:

1. **Lower resolution**: Change generation nodes from `1024` ΓåÆ `512`
2. **Reduce token count**: Fewer tokens = less VRAM during inference
3. **Lower texture resolution**: In the texturing node (slightly less detail, mesh unchanged)
4. **Close everything**: Chrome, Discord, games ΓÇö every MB counts on 6 GB
5. **Add startup flag**: `--disable-pinned-memory` to ComfyUI startup args (frees held GPU memory)
6. **Combine above**: All three options stack ΓÇö use together if needed

---

## Multi-View Generation

For better accuracy when you have multiple reference angles:

- Same GGUF loader node
- Feed multiple reference images into the workflow
- Multi-view workflow available at `pixel-artistry.com/trellis2gguf`
- Reduces shape ambiguity on complex assets

---

## Integration with Other 3D Skills

| Workflow | Skills to Combine |
|---|---|
| **Web/R3F pipeline** | `trellis2-gguf` ΓåÆ `asset-optimization` (Draco compression, KTX2 textures) ΓåÆ `3d-performance` (LOD, instancing) |
| **Game engine pipeline** | `trellis2-gguf` ΓåÆ retopo (external) ΓåÆ `animation-principles` |
| **Background assets** | `trellis2-gguf` ΓåÆ `asset-optimization` (LOD generation) |

---

## vs. Cloud 3D Tools

| Tool | vs. Trellis 2 GGUF |
|---|---|
| **Meshy AI** | Trellis 2 wins: free, local, private. Meshy wins: text-to-3D, possibly cleaner topo, no setup. Partial replacement. |
| **TripoAI / Tripo3D** | Cloud service ΓÇö Trellis 2 is the local equivalent. No text-to-3D. |
| **SketchUp** | No overlap ΓÇö SketchUp is parametric/architectural, Trellis 2 is object-from-image. Use together. |
| **Blender** | Blender is the downstream host, not a competitor. Trellis 2 feeds INTO Blender. |
| **Hitem3D / 3DAIStudio** | Cloud services for retopo/texturing. Complement Trellis 2 output. |

---

## Common Mistakes

| Don't | Do |
|---|---|
| Load old Trellis 2 workflow with GGUF | Use the GGUF-specific workflow from the download link |
| Max out resolution on 6 GB card | Stick to default settings (pre-optimized for low VRAM) |
| Skip retopo for rigged characters | Always retopo before rigging |
| Use for room/interior design | This is object-only; use SketchUp for spaces |
| Mix GGUF nodes with non-GGUF Trellis 2 nodes | Use the complete GGUF node set from ArrowX fork |

---

## Resources

- **Installer + Workflows**: `pixel-artistry.com/trellis2gguf`
- **ComfyUI GGUF Fork**: ArrowX fork (linked from installer page)
- **Trellis 2 base repo**: Visual Bruno / Microsoft (GitHub)
- **Retopo tools**: 3DA Studio (`3daistudio.com`), ZBrush, Blender Remesh
- **Vault analysis**: `research/videos/2026-04-15_trellis2-gguf-6gb-vram-local-3d.md`
