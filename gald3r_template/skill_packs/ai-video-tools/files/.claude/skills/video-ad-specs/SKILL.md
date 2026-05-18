---
name: video-ad-specs
description: Social video ad specs and AIDA—TikTok, Instagram, YouTube, Facebook, LinkedIn dimensions and timing.
tags: [video, advertising, social-media, distribution, marketing]
---

# Video Ad Platform Specifications

Platform-specific video ad creation guide with exact specs and AIDA framework.

## When to Use

- Creating video content for social media distribution
- Adapting content for multiple platforms
- Planning ad campaigns with video assets
- Ensuring correct dimensions and timing per platform

## Platform Specs Quick Reference

| Platform | Aspect Ratio | Resolution | Max Duration | Autoplay |
|----------|-------------|-----------|-------------|----------|
| **TikTok** | 9:16 | 1080x1920 | 60s (15s ideal) | Sound ON |
| **Instagram Reels** | 9:16 | 1080x1920 | 90s (15-30s ideal) | Sound ON |
| **Instagram Stories** | 9:16 | 1080x1920 | 15s per story | Sound ON |
| **YouTube Shorts** | 9:16 | 1080x1920 | 60s | Sound ON |
| **YouTube Bumper** | 16:9 | 1920x1080 | 6s | Sound OFF |
| **YouTube Pre-roll** | 16:9 | 1920x1080 | 15-30s | Skippable |
| **Facebook Feed** | 1:1 or 4:5 | 1080x1080 / 1080x1350 | 240s (15s ideal) | Sound OFF |
| **LinkedIn** | 1:1 or 16:9 | 1080x1080 / 1920x1080 | 30s ideal | Sound OFF |

## AIDA Framework for Video Ads

| Phase | Timing | Purpose | Technique |
|-------|--------|---------|-----------|
| **A**ttention | 0-3s | Stop the scroll | Bold visual, question, shock |
| **I**nterest | 3-8s | Build curiosity | Problem statement, relatable scenario |
| **D**esire | 8-20s | Show the solution | Demo, benefits, social proof |
| **A**ction | Last 3-5s | Drive CTA | Clear next step, urgency |

## Hook Techniques (First 3 Seconds)

| Technique | Example |
|-----------|---------|
| **Bold Question** | "What if your code could review itself?" |
| **Shocking Stat** | "90% of startups fail because of THIS" |
| **Pattern Interrupt** | Unexpected visual or sound |
| **Direct Address** | "Hey developers, stop doing this" |
| **Before/After** | Split screen comparison |

## Caption Requirements

**85% of Facebook videos are watched without sound.** Captions are mandatory.

| Platform | Caption Style |
|----------|--------------|
| TikTok | Built-in auto-captions or burned-in |
| Instagram | Burned-in (auto-captions unreliable) |
| YouTube | Auto-generated + manual review |
| Facebook | Burned-in (sound-off default) |
| LinkedIn | Burned-in (professional context) |

## Safe Zones

```
+----------------------+
|  +--------------+    |
|  |              |    |  <- 10% margin all sides
|  |  SAFE ZONE   |    |     for platform UI overlay
|  |              |    |
|  +--------------+    |
|         v            |
|   [Platform UI]      |  <- Bottom 20% may be covered
+----------------------+
```

## Integration with Our Pipeline

- Export R3F scenes as video clips at correct aspect ratios
- Use Remotion to compose final ads with text overlays and CTAs
- Generate platform-specific variants from single source
