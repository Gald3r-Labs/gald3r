---
name: ai-avatar-lipsync
description: "Create AI avatars and talking head videos with audio-driven animation. Covers OmniHuman, Fabric, PixVerse models and dubbing workflows."
tags: [ai, avatar, lipsync, talking-head, video, dubbing]
---

# AI Avatar & Lipsync

Create AI-powered talking head videos with audio-driven animation and lipsync.

## When to Use

- Creating talking head videos from portrait photos
- Audio-driven facial animation
- Dubbing existing video in different languages
- Virtual presenter/influencer content
- Quick character dialogue previews before full 3D render

## Available Models

| Model | Multi-Character | Quality | Speed | Best For |
|-------|----------------|---------|-------|----------|
| **OmniHuman 1.5** | Yes | Highest | Slow | Final quality output |
| **OmniHuman 1.0** | No | High | Medium | Single character |
| **Fabric 1.0** | No | Good | Fast | Quick iterations |
| **PixVerse** | No | High | Medium | Realistic lipsync |

## Workflows

### Basic: Portrait + Audio -> Video
```bash
# Generate speech
inference tts \
  --text "This is the decentralized internet" \
  --voice confident_male \
  --output speech.mp3

# Create talking head
inference video \
  --model omnihuman-1.5 \
  --image richard_hendricks.jpg \
  --audio speech.mp3 \
  --output richard_talking.mp4
```

### Advanced: Dub Video in Another Language
```bash
# Step 1: Transcribe original
inference stt \
  --audio original_english.mp3 \
  --output transcript.json

# Step 2: Translate transcript
# (Use translation API or manual)

# Step 3: Generate TTS in target language
inference tts \
  --text "Esta es la internet descentralizada" \
  --voice spanish_male \
  --output spanish_speech.mp3

# Step 4: Lipsync with new audio
inference video \
  --model pixverse-lipsync \
  --video original_video.mp4 \
  --audio spanish_speech.mp3 \
  --output dubbed_spanish.mp4
```

## Portrait Photo Requirements

| Requirement | Specification |
|-------------|--------------|
| **Facing** | Front-facing (slight angle OK) |
| **Lighting** | Even, well-lit (no harsh shadows) |
| **Resolution** | 512x512 minimum, 1024x1024 ideal |
| **Background** | Clean, uncluttered |
| **Expression** | Neutral or slight smile |
| **Framing** | Head and shoulders |

## Audio Requirements

| Requirement | Specification |
|-------------|--------------|
| **Format** | MP3 or WAV |
| **Quality** | Clear, minimal background noise |
| **Sample rate** | 16kHz minimum, 44.1kHz ideal |
| **Duration** | Match desired output length |

## Use Cases

| Use Case | Model | Workflow |
|----------|-------|----------|
| Product demo presenter | OmniHuman 1.5 | TTS -> Avatar |
| Course/tutorial | OmniHuman 1.0 | Script -> TTS -> Avatar |
| Multi-language dub | PixVerse | Transcribe -> Translate -> TTS -> Lipsync |
| Social media | Fabric 1.0 | Quick TTS -> Avatar |
| Character preview | Any | Script -> TTS -> Portrait -> Avatar |

## Tips

- **OmniHuman 1.5** supports multiple people in one image
- **Fabric** is fastest for quick iteration during development
- **PixVerse** produces the most realistic mouth movements
- Use high-quality TTS (ElevenLabs) for best lipsync results
- Test with short clips (5-10s) before rendering long videos

## Comparison with Our 3D Lipsync Pipeline

| Aspect | AI Avatar (This Skill) | sv-voice-lipsync (Our Pipeline) |
|--------|----------------------|-------------------------------|
| **Input** | 2D portrait photo | 3D GLB model with morph targets |
| **Output** | Flat video (MP4) | Real-time 3D animation |
| **Quality** | Very realistic | Stylized (toon shader) |
| **Speed** | Minutes | Real-time |
| **Interactivity** | None (pre-rendered) | Full (R3F scene) |
| **Best for** | Quick previews, social content | In-show animation |

## Integration with Our Pipeline

- **Quick dialogue preview**: Test character dialogue with AI avatar before full 3D render
- **Social media content**: Generate talking head clips for marketing
- **Storyboard validation**: Verify dialogue timing with AI-generated preview
- **B-roll presenter**: AI presenter for tutorial/explainer content about the show
