---
name: 3d-performance
description: "Performance optimization for 3D web scenes — LOD strategies, frustum/occlusion culling, draw call reduction, and R3F-specific optimizations. Use when scenes run below 60fps."
tags: [3d, performance, lod, culling, optimization, r3f, threejs, webgl]
---

# 3D Performance Optimization

Performance strategies for Three.js / React Three Fiber scenes with many objects, characters, and environments.

## When to Use

- Scene drops below 60fps target
- Adding more characters to a scene
- Loading large environments
- Profiling and fixing render bottlenecks
- Planning scene complexity budgets

## Performance Budget

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **FPS** | 60 | <45 | <30 |
| **Draw calls** | <100 | 100-200 | >200 |
| **Triangles/frame** | <500K | 500K-1M | >1M |
| **Texture memory** | <256MB | 256-512MB | >512MB |
| **JS heap** | <100MB | 100-200MB | >200MB |
| **Load time** | <3s | 3-6s | >6s |

## Rendering Pipeline

```
Vertex Processing → Rasterization → Fragment Processing → Output
     (geometry)      (pixels)         (color/light)      (screen)
```

Every optimization targets one of these stages.

## Level of Detail (LOD)

### Distance-Based LOD
| Distance | LOD | Triangles | Texture |
|----------|-----|-----------|---------|
| 0-5m | LOD0 | 100% | Full res |
| 5-15m | LOD1 | 50% | Half res |
| 15-30m | LOD2 | 25% | Quarter |
| 30m+ | Billboard | Flat quad | 128px |

### R3F Implementation
```tsx
import { Detailed } from '@react-three/drei';

function Character({ position }) {
  return (
    <Detailed distances={[0, 10, 25, 50]} position={position}>
      <HighDetailModel />   {/* LOD0: close */}
      <MediumDetailModel /> {/* LOD1: medium */}
      <LowDetailModel />    {/* LOD2: far */}
      <Billboard />          {/* LOD3: very far */}
    </Detailed>
  );
}
```

## Culling Strategies

### Frustum Culling (Automatic in Three.js)
Objects outside camera view are not rendered. Three.js does this automatically but:
- Ensure bounding boxes are correct (call `geometry.computeBoundingBox()`)
- Large objects may never be culled — split into smaller pieces

### Occlusion Culling (Manual)
Objects hidden behind other objects. Not automatic — implement manually:

```tsx
// Simple distance-based visibility
function useVisibility(ref, maxDistance = 50) {
  const camera = useThree(state => state.camera);
  useFrame(() => {
    if (ref.current) {
      const dist = camera.position.distanceTo(ref.current.position);
      ref.current.visible = dist < maxDistance;
    }
  });
}
```

### Layer-Based Rendering
```tsx
// Assign objects to layers for selective rendering
mesh.layers.set(1);        // Only render in layer 1
camera.layers.enable(1);    // Camera sees layer 1
camera.layers.disable(2);   // Camera ignores layer 2
```

## Draw Call Reduction

### Instanced Meshes (Same geometry, many positions)
```tsx
import { Instances, Instance } from '@react-three/drei';

function ManyTrees({ positions }) {
  return (
    <Instances limit={1000}>
      <boxGeometry />
      <meshStandardMaterial />
      {positions.map((pos, i) => (
        <Instance key={i} position={pos} />
      ))}
    </Instances>
  );
}
```

### Merged Meshes (Different geometry, one draw call)
```tsx
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const merged = mergeGeometries([geo1, geo2, geo3]);
// One draw call instead of three
```

### Material Sharing
```tsx
// BAD: new material per mesh (more draw calls)
meshes.forEach(m => m.material = new MeshStandardMaterial({ color: 'red' }));

// GOOD: shared material (fewer draw calls)
const sharedMat = new MeshStandardMaterial({ color: 'red' });
meshes.forEach(m => m.material = sharedMat);
```

## Shadow Optimization

| Technique | Performance | Quality |
|-----------|------------|---------|
| **No shadows** | Best | N/A |
| **Baked shadows** | Good | Static only |
| **Blob shadows** | Good | Approximate |
| **Shadow maps** | Expensive | Dynamic |
| **Cascaded shadows** | Very expensive | Best quality |

```tsx
// Blob shadow (cheap alternative)
import { ContactShadows } from '@react-three/drei';

<ContactShadows
  position={[0, -0.01, 0]}
  opacity={0.4}
  width={10}
  height={10}
  blur={2}
  far={4}
/>
```

## R3F-Specific Optimizations

### useFrame Performance
```tsx
// BAD: allocating in render loop
useFrame(() => {
  const vec = new Vector3(); // GC pressure!
  mesh.current.position.copy(vec);
});

// GOOD: reuse objects
const _vec = new Vector3();
useFrame(() => {
  mesh.current.position.copy(_vec.set(x, y, z));
});
```

### Suspense & Code Splitting
```tsx
<Suspense fallback={<LoadingIndicator />}>
  <HeavyScene />
</Suspense>
```

### Offscreen Canvas (Worker)
```tsx
<Canvas gl={{ powerPreference: 'high-performance' }}>
```

## Profiling Tools

| Tool | What It Shows |
|------|--------------|
| `stats.js` | FPS, MS, MB |
| `r3f-perf` | Detailed R3F stats |
| Chrome DevTools → Performance | Frame timeline |
| `renderer.info` | Draw calls, triangles |
| Spector.js | WebGL call inspector |

```tsx
import { Perf } from 'r3f-perf';

<Canvas>
  <Perf position="top-left" />
  <Scene />
</Canvas>
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Load all models at start | Lazy load on demand |
| Real-time shadows on mobile | Baked or blob shadows |
| New materials per object | Share materials |
| `new Vector3()` in useFrame | Pre-allocate, reuse |
| Uncompressed textures | WebP or KTX2 |
| 100K triangle props | Simplify for web |

## Integration with Our Pipeline

- Profile SV office scene with r3f-perf
- Apply LOD to background characters
- Use instanced meshes for office props (chairs, monitors)
- Blob shadows instead of shadow maps for performance
- Combine with asset-optimization skill for full pipeline
