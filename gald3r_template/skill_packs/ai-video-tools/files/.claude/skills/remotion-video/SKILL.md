---
name: remotion-video
description: Remotion React video—compositions, audio, captions, 3D, transitions, cloud render from code.
tags: [video, react, remotion, animation, rendering, production]
---

# Remotion — Programmatic Video in React

Create videos programmatically using React components. Remotion treats video as a function of time — every frame is a React component render.

## When to Use

- Creating trailers, recaps, social clips from 3D scenes
- Automated video generation (product demos, marketing)
- Data-driven video (charts, dashboards, reports)
- Compositing text overlays, transitions, captions
- Exporting R3F scenes as distributable MP4

## Core Concepts

```
Frame (number) → React Component → Image → Video
```

- **Composition**: A video with defined dimensions, FPS, and duration
- **Sequence**: A time-shifted section within a composition
- **useCurrentFrame()**: Returns the current frame number (0-based)
- **useVideoConfig()**: Returns { fps, width, height, durationInFrames }
- **interpolate()**: Maps frame ranges to output values
- **spring()**: Physics-based easing

## Quick Start

```bash
npx create-video@latest my-video
cd my-video
npm start        # Preview at localhost:3000
npx remotion render src/index.ts MyComp out.mp4
```

## Basic Composition

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from 'remotion';

export const MyVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(frame, [0, 30], [0.5, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#111', justifyContent: 'center', alignItems: 'center' }}>
      <h1 style={{ color: 'white', opacity, transform: `scale(${scale})`, fontSize: 80 }}>
        Hello Remotion
      </h1>
    </AbsoluteFill>
  );
};
```

## Key APIs

### interpolate()
```tsx
// Map frame 0-30 to opacity 0-1
const opacity = interpolate(frame, [0, 30], [0, 1]);

// With easing
import { Easing } from 'remotion';
const value = interpolate(frame, [0, 60], [0, 100], {
  easing: Easing.bezier(0.25, 0.1, 0.25, 1),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

### spring()
```tsx
import { spring } from 'remotion';
const scale = spring({
  frame,
  fps,
  config: { damping: 10, stiffness: 100, mass: 0.5 },
});
```

### Sequence
```tsx
import { Sequence } from 'remotion';

<Sequence from={0} durationInFrames={60}>
  <IntroScene />
</Sequence>
<Sequence from={60} durationInFrames={90}>
  <MainScene />
</Sequence>
<Sequence from={150} durationInFrames={60}>
  <OutroScene />
</Sequence>
```

### Audio
```tsx
import { Audio, staticFile } from 'remotion';

<Audio src={staticFile('music.mp3')} volume={0.5} />

// Volume automation
<Audio src={staticFile('vo.mp3')} volume={(f) =>
  interpolate(f, [0, 15], [0, 1], { extrapolateRight: 'clamp' })
} />
```

### Media
```tsx
import { Img, Video, staticFile } from 'remotion';

<Img src={staticFile('photo.png')} style={{ width: '100%' }} />
<Video src={staticFile('clip.mp4')} startFrom={30} endAt={120} />
```

## Transition Patterns

```tsx
// Fade transition between scenes
const fadeOut = interpolate(frame, [55, 60], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
const fadeIn = interpolate(frame, [60, 65], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

// Slide transition
const slideX = interpolate(frame, [58, 63], [0, -1920], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
```

## Rendering

```bash
# Local render
npx remotion render src/index.ts MyComp output.mp4

# With options
npx remotion render src/index.ts MyComp output.mp4 \
  --codec h264 \
  --image-format jpeg \
  --quality 80

# Cloud render via inference.sh (no local GPU needed)
inference video \
  --model remotion \
  --code "$(cat MyComp.tsx)" \
  --width 1920 --height 1080 --fps 30 \
  --duration_seconds 10
```

## Production Workflow (Multi-Agent)

1. **Define Video Spec**: audience, goal, duration, aspect ratio, tone
2. **Outline Scenes**: visual, audio, text, transitions per scene
3. **Prepare Assets**: logos, screenshots, audio, fonts
4. **Implement Compositions**: React TSX components
5. **Render and QA**: preview, validation, final render

### Validation Gates
- Spec completeness check (all fields defined)
- Narrative consistency check (scene flow makes sense)
- Render-readiness check (all assets available, no missing imports)

## Common Patterns

| Pattern | Technique |
|---------|-----------|
| Text reveal | `interpolate` opacity + translateY |
| Logo animation | `spring` scale from 0 to 1 |
| Progress bar | `interpolate` width from 0% to 100% |
| Typewriter | Substring with frame-based index |
| Parallax | Different `interpolate` speeds per layer |
| Ken Burns | Slow zoom + pan on static image |

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Use `setTimeout`/`setInterval` | Use `useCurrentFrame()` for all timing |
| Mutate state in render | Derive everything from frame number |
| Import large assets inline | Use `staticFile()` and preload |
| Hardcode dimensions | Use `useVideoConfig()` |

## Integration with Our Pipeline

- **R3F to Video**: Render React Three Fiber scenes as Remotion compositions
- **Episode export**: Compose final episode videos with title cards, transitions, credits
- **Social clips**: Generate platform-specific clips (TikTok 9:16, YouTube 16:9)
- **Automated recaps**: Data-driven recap videos from episode metadata
- **Captions**: Burn in subtitles from voice-lipsync transcript data

## Reference

For deep Remotion knowledge, see: `research/selected_skills/remotion-best-practices--remotion-dev/rules/`
(28+ detailed rule files covering every Remotion API)
