---
name: asset-optimization
description: "3D asset optimization pipeline using gltf-transform. Covers mesh compression (Draco), texture compression (WebP/KTX2), mesh merging, and LOD generation for web-ready GLB files."
tags: [3d, optimization, gltf, draco, webp, performance, assets]
---

# Asset Optimization Pipeline

Optimize 3D assets for web delivery using gltf-transform and related tools. Reduce file size, improve load times, and maintain visual quality.

## When to Use

- Preparing 3D models for web (R3F, Three.js)
- Reducing GLB file size for faster loading
- Batch processing asset libraries
- Setting up CI/CD asset pipeline

## Target Budgets

| Asset Type | Triangles | File Size | Texture Size |
|-----------|-----------|-----------|-------------|
| Character (hero) | 5-10K | 2-5 MB | 1024x1024 |
| Character (background) | 2-5K | 1-2 MB | 512x512 |
| Prop (small) | 500-2K | 100-500 KB | 256x256 |
| Furniture | 3-8K | 500KB-2MB | 512x512 |
| Environment | 10-30K | 3-8 MB | 1024x1024 |
| Full scene | 50-100K | 10-20 MB | Mixed |

## gltf-transform CLI

### Installation
```bash
npm install -g @gltf-transform/cli
```

### Compression Pipeline
```bash
# Full optimization pipeline
gltf-transform optimize input.glb output.glb \
  --compress draco \
  --texture-compress webp

# Step by step for more control:

# 1. Draco mesh compression
gltf-transform draco input.glb compressed.glb

# 2. Texture compression to WebP
gltf-transform webp compressed.glb textured.glb --quality 80

# 3. KTX2 texture compression (GPU-friendly)
gltf-transform ktx2 input.glb output.glb --slots "baseColor,normal"

# 4. Deduplicate meshes and textures
gltf-transform dedup input.glb deduped.glb

# 5. Remove unused data
gltf-transform prune input.glb pruned.glb

# 6. Merge meshes (reduce draw calls)
gltf-transform join input.glb joined.glb

# 7. Generate LOD levels
gltf-transform simplify input.glb lod.glb --ratio 0.5
```

### Batch Processing
```bash
# Process all GLB files in a directory
for f in assets/*.glb; do
  gltf-transform optimize "$f" "optimized/$(basename $f)" \
    --compress draco \
    --texture-compress webp
done
```

## Texture Compression Comparison

| Format | GPU Decode | File Size | Quality | Browser Support |
|--------|-----------|-----------|---------|----------------|
| **PNG** | No | Large | Lossless | Universal |
| **JPEG** | No | Small | Lossy | Universal |
| **WebP** | No | Smallest | Both | Modern browsers |
| **KTX2/Basis** | Yes | Small | Lossy | WebGL2+ |
| **AVIF** | No | Smallest | Lossy | Newer browsers |

**Recommendation**: WebP for textures, KTX2 for GPU-heavy scenes.

## Mesh Optimization Strategies

### Polygon Reduction
```bash
# Reduce to 50% triangles
gltf-transform simplify model.glb reduced.glb --ratio 0.5

# Target specific triangle count
gltf-transform simplify model.glb reduced.glb --error 0.01
```

### Mesh Merging (Reduce Draw Calls)
```bash
# Merge meshes sharing the same material
gltf-transform join model.glb merged.glb
```

### Remove Unused Data
```bash
# Strip unused textures, materials, meshes
gltf-transform prune model.glb clean.glb

# Remove specific extensions
gltf-transform prune model.glb clean.glb --keepExtras false
```

## LOD Strategy

| Distance from Camera | LOD Level | Triangle Ratio | Texture Size |
|---------------------|-----------|----------------|-------------|
| 0-5 units (close) | LOD0 | 100% | Full |
| 5-15 units (medium) | LOD1 | 50% | Half |
| 15-30 units (far) | LOD2 | 25% | Quarter |
| 30+ units (distant) | Billboard | Flat quad | 128x128 |

### R3F LOD Implementation
```tsx
import { LOD } from 'three';
import { useGLTF } from '@react-three/drei';

function OptimizedModel({ position }) {
  const lod0 = useGLTF('/model_lod0.glb');
  const lod1 = useGLTF('/model_lod1.glb');
  const lod2 = useGLTF('/model_lod2.glb');

  return (
    <lod position={position}>
      <primitive object={lod0.scene} distance={0} />
      <primitive object={lod1.scene} distance={10} />
      <primitive object={lod2.scene} distance={25} />
    </lod>
  );
}
```

## Validation

```bash
# Inspect GLB file stats
gltf-transform inspect model.glb

# Check file size
ls -lh model.glb

# Validate GLTF compliance
npx gltf-validator model.glb
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Ship uncompressed GLB | Always run gltf-transform optimize |
| Use PNG for all textures | Use WebP or KTX2 |
| 50K triangle props | Simplify to 2-5K for web |
| Load all LODs upfront | Use distance-based LOD switching |
| Skip deduplication | Run dedup to find shared resources |

## Integration with Our Pipeline

- Run after Blender export in sv-asset-pipeline
- Batch optimize character GLBs from sv-character-generation
- Apply LOD strategy in sv-r3f-integration scenes
- CI/CD: Auto-optimize on asset commit
