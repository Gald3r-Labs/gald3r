---
name: animated-gif-creator
description: "Create optimized animated GIFs with composable animation primitives. Covers Slack constraints (2MB messages, 64KB emoji), easing functions, and optimization strategies."
tags: [animation, gif, slack, social-media, composable, primitives]
---

# Animated GIF Creator

Toolkit for creating optimized animated GIFs with composable animation primitives and platform-specific validators.

## When to Use

- Creating reaction GIFs for Slack/Discord
- Building animated emoji (64KB constraint)
- Composing animation sequences from primitives
- Optimizing GIF file size for platform constraints

## Platform Constraints

| Platform | Max Size | Dimensions | Notes |
|----------|----------|-----------|-------|
| **Slack message** | 2 MB | Any reasonable | Auto-plays inline |
| **Slack emoji** | 64 KB | 128x128 max | Must be tiny |
| **Discord** | 8 MB | Any | Nitro: 50MB |
| **Twitter/X** | 15 MB | 1280x1080 max | Converts to video |
| **GitHub** | 10 MB | Any | README, issues |

## Composable Animation Primitives

| Primitive | Parameters | Effect |
|-----------|-----------|--------|
| `shake` | intensity, frequency | Rapid back-and-forth |
| `bounce` | height, gravity | Vertical bounce |
| `spin` | speed, direction | Rotation |
| `pulse` | scale_min, scale_max | Size oscillation |
| `fade` | start_opacity, end_opacity | Transparency change |
| `zoom` | start_scale, end_scale | Scale in/out |
| `explode` | particle_count | Burst apart |
| `wiggle` | amplitude, frequency | Wobble |
| `slide` | direction, distance | Linear movement |
| `flip` | axis | Mirror flip |
| `morph` | target_shape | Shape transition |
| `move` | path_points | Follow path |
| `kaleidoscope` | segments | Mirror pattern |

## Composition Patterns

### Reaction GIF (< 2MB)
```
[bounce] + [pulse] -> "excited reaction"
[shake] + [zoom_in] -> "shock reaction"
[spin] + [fade_out] -> "dramatic exit"
```

### Emoji GIF (< 64KB)
```
Constraints: 128x128, 4-8 frames, 8-16 colors
[pulse] at low intensity -> "breathing" effect
[bounce] with 4 frames -> "hopping" emoji
```

## Optimization Strategies

| Strategy | Size Reduction | Quality Impact |
|----------|---------------|----------------|
| Reduce colors (256->32) | ~50% | Low-Medium |
| Reduce frame count | ~30-60% | Medium |
| Reduce dimensions | ~40-70% | Depends |
| Optimize frame disposal | ~10-20% | None |
| Use lossy compression | ~30-50% | Low |
| Dithering: none vs Floyd | Varies | Visual style |

## Easing Functions

| Easing | Feel | Use For |
|--------|------|---------|
| `linear` | Mechanical | Progress bars |
| `ease-in` | Accelerating | Starting motion |
| `ease-out` | Decelerating | Landing, settling |
| `ease-in-out` | Natural | Most animations |
| `bounce` | Playful | Fun reactions |
| `elastic` | Springy | Overshoot effects |

## Color Palette Tips

- **Less is more**: 16-32 colors for small GIFs
- **Dithering**: Floyd-Steinberg for gradients, none for flat colors
- **Transparency**: Single transparent color saves bytes
- **Consistent palette**: Reuse same palette across frames

## Integration with Our Pipeline

- Create SV character reaction GIFs for social media
- Export R3F scene snapshots as GIF sequences
- Build Slack emoji set with character expressions
- Use primitives as building blocks for UI animations
