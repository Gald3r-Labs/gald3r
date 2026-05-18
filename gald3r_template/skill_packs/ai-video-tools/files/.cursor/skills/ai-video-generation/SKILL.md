---
name: ai-video-generation
description: "Generate AI videos with 40+ models — text-to-video, image-to-video, lipsync, avatar, upscaling, foley. Covers Veo, Wan, Seedance, Grok, OmniHuman, and more via inference.sh CLI."
tags: [ai, video, generation, text-to-video, image-to-video, veo, wan, lipsync]
---

# AI Video Generation

Generate videos with 40+ AI models via inference.sh CLI. Covers text-to-video, image-to-video, avatar/lipsync, upscaling, and audio generation.

## When to Use

- Generating B-roll, backgrounds, establishing shots
- Converting concept art to animated sequences
- Creating talking head videos with AI avatars
- Upscaling and enhancing existing video
- Adding foley sound effects to silent video

## Model Selection

### Text-to-Video

| Model | Quality | Speed | Audio | Best For |
|-------|---------|-------|-------|----------|
| **Veo 3.1** | Highest | Slow | Optional | Hero shots, cinematic |
| **Veo 3.1 Fast** | High | Fast | Optional | Quick iteration |
| **Veo 3** | High | Medium | Yes | Audio-synced content |
| **Seedance 1.5 Pro** | High | Medium | No | Artistic, expressive |
| **Grok Video** | Good | Fast | No | General purpose |

### Image-to-Video

| Model | Best For | Motion Style |
|-------|----------|-------------|
| **Wan 2.5 I2V** | Photorealistic | Subtle, natural |
| **Seedance 1.5 Pro** | Artistic | Expressive |
| **Fabric 1.0** | Cloth physics | Physics-based |
| **Grok Imagine** | General | Versatile |

### Avatar/Lipsync

| Model | Best For |
|-------|----------|
| **OmniHuman 1.5** | Multi-character, best quality |
| **OmniHuman 1.0** | Single character |
| **Fabric 1.0** | Image talks with lipsync |
| **PixVerse** | Highly realistic lipsync |

## CLI Examples

### Text-to-Video
```bash
inference video \
  --model veo-3.1-fast \
  --prompt "A programmer typing frantically at a desk in a startup office, cinematic lighting, 4K" \
  --output establishing_shot.mp4
```

### Image-to-Video
```bash
inference video \
  --model wan-2.5-i2v \
  --image concept_art.png \
  --prompt "Gentle camera push in, subtle atmospheric particles floating" \
  --output animated_concept.mp4
```

### AI Avatar (Talking Head)
```bash
# Step 1: Generate speech
inference tts \
  --text "Welcome to The Forge" \
  --voice professional_male \
  --output speech.mp3

# Step 2: Create avatar video
inference video \
  --model omnihuman-1.5 \
  --image portrait.jpg \
  --audio speech.mp3 \
  --output talking_head.mp4
```

### Video Upscaling
```bash
inference video \
  --model topaz-upscaler \
  --input low_res.mp4 \
  --scale 4 \
  --output upscaled_4k.mp4
```

### Foley Sound Generation
```bash
inference audio \
  --model hunyuan-foley \
  --video silent_clip.mp4 \
  --output foley_audio.wav
```

### Media Merge
```bash
inference merge \
  --video clip.mp4 \
  --audio music.mp3 \
  --output final.mp4
```

## Motion Prompting Best Practices

### Golden Rule: Subtle > Dramatic

### Prompt Structure
```
[Camera movement] + [Subject motion] + [Atmospheric effects] + [Mood/pace]
```

### Camera Movements
| Movement | Prompt Phrase |
|----------|--------------|
| Push in | "Slow camera push in" |
| Pull out | "Camera slowly pulls back" |
| Pan | "Camera pans left to right" |
| Tilt | "Camera tilts upward" |
| Orbit | "Camera orbits around subject" |
| Static | "Static camera, locked off" |

### Duration Guidelines

| Duration | Quality | Use |
|----------|---------|-----|
| 2-3s | Highest | Hero shots, loops |
| 4-5s | High | Standard clips |
| 6-8s | Good | Extended scenes |
| 10+s | Degrades | Avoid for quality |

## Cinemagraph Effect

Freeze background while one element moves:
```
"Static scene, only [element] moves. Everything else perfectly still."
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| "Dramatic explosion" prompt | Use subtle motion descriptions |
| Too long duration | Keep under 5s for quality |
| Vague prompts | Be specific: lighting, angle, mood |
| Wrong model for task | Check model selection table |

## Integration with Our Pipeline

- **Establishing shots**: Generate office exterior, city skyline for scene transitions
- **B-roll**: Fill gaps between dialogue scenes with atmospheric footage
- **Dream sequences**: AI-generated surreal visuals for character fantasy scenes
- **Concept to animation**: Convert character concept art to animated previews
- **Foley**: Generate ambient sound effects for R3F scenes
