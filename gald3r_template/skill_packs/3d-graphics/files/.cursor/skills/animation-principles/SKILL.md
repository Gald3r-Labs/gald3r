---
name: animation-principles
description: "The 12 animation principles (Disney) applied to interactive 3D and game contexts. Covers squash/stretch, anticipation, follow-through, timing, and frame count guidelines for character animation."
tags: [animation, principles, disney, character, timing, interactive]
---

# Animation Principles for Interactive Media

The 12 Disney animation principles adapted for interactive 3D characters, games, and web experiences.

## When to Use

- Improving character animation quality
- Planning animation state machines
- Setting frame counts and timing
- Reviewing animation for natural feel
- Training new animators on fundamentals

## The 12 Principles Applied to Interactive Media

### 1. Squash & Stretch
**Classic**: Object deforms to show weight and flexibility
**Interactive**: Jump arcs (stretch on rise, squash on land), impact reactions, bouncy UI elements

```
Landing:  ████████  (wide, flat = squash)
Idle:     ██████    (normal)
Jumping:  ████      (tall, thin = stretch)
          ██
```

**Implementation**: Scale Y down + scale X up on landing; reverse on jump. Preserve volume (area stays constant).

### 2. Anticipation
**Classic**: Preparation before main action
**Interactive**: Wind-up before attack, crouch before jump, pull-back before throw

```
Timeline: [anticipation 3-5f] → [action 2-4f] → [follow-through 3-6f]
```

**Critical for games**: Without anticipation, attacks feel instant and unreadable. Players need visual telegraphing.

### 3. Staging
**Classic**: Present idea clearly
**Interactive**: Clear character silhouettes, readable poses at gameplay distance, distinct animation states

**Test**: Silhouette test — can you identify the action from a black silhouette alone?

### 4. Straight Ahead vs Pose-to-Pose
**Straight Ahead**: Animate frame by frame (organic, fluid — fire, smoke, hair)
**Pose-to-Pose**: Define key poses, fill in between (controlled — character actions)

**For our pipeline**: Use pose-to-pose for character states (Idle, Walk, Talk), straight ahead for particle effects.

### 5. Follow-Through & Overlapping Action
**Classic**: Parts continue moving after main body stops
**Interactive**: Hair sways after character stops, cape settles, accessories jiggle

```
Character stops walking → body stops → hair swings forward → settles back
```

**R3F implementation**: Secondary bones with spring physics (drei `useSpring` or custom damped oscillation).

### 6. Slow In / Slow Out (Easing)
**Classic**: Acceleration and deceleration
**Interactive**: Ease-in on start, ease-out on stop. Never use linear motion for organic movement.

| Movement | Easing |
|----------|--------|
| Character walk start | Ease-in (accelerate) |
| Character walk stop | Ease-out (decelerate) |
| UI panel appear | Ease-out (fast start, soft land) |
| Camera transition | Ease-in-out (smooth both ends) |

### 7. Arcs
**Classic**: Natural movement follows curved paths
**Interactive**: Jump arcs (parabolic), arm swings (circular), head turns (curved)

**Never**: Move a character in a straight line unless they're a robot.

### 8. Secondary Action
**Classic**: Supporting actions that reinforce the main action
**Interactive**: Breathing idle animation, blinking, clothing physics, environmental particles

```
Main: Character typing at desk
Secondary: Subtle breathing, occasional blink, screen glow reflection
```

### 9. Timing
**Classic**: Number of frames = perceived weight and mood
**Interactive**: Fast = light/snappy, Slow = heavy/dramatic

| Action | Frame Count | Seconds (24fps) | Feel |
|--------|------------|-----------------|------|
| Blink | 2-4 | 0.08-0.17s | Natural |
| Head turn | 6-10 | 0.25-0.42s | Casual |
| Walk cycle | 12-24 | 0.5-1.0s | Normal |
| Run cycle | 8-16 | 0.33-0.67s | Energetic |
| Idle breathing | 48-96 | 2-4s | Relaxed |
| Attack (fast) | 4-8 | 0.17-0.33s | Snappy |
| Attack (heavy) | 12-20 | 0.5-0.83s | Powerful |
| Death/fall | 16-32 | 0.67-1.33s | Dramatic |
| Sit down | 20-30 | 0.83-1.25s | Deliberate |
| Stand up | 16-24 | 0.67-1.0s | Natural |

### 10. Exaggeration
**Classic**: Push actions beyond realism for clarity
**Interactive**: More important at distance. Gameplay animations need more exaggeration than cutscene animations.

**Our toon-shaded style**: Already exaggerated visuals → match with exaggerated animation. Subtle realism would look wrong.

### 11. Solid Drawing (3D equivalent: Good Topology)
**Classic**: Volume, weight, and balance in drawings
**Interactive**: Clean mesh topology, proper edge flow for deformation, weight painting

### 12. Appeal
**Classic**: Character should be interesting to watch
**Interactive**: Distinctive silhouettes, memorable idle animations, personality in movement

**Our SV characters**: Each character should move differently:
- Richard: Nervous fidgeting, hunched
- Sindri: Minimal movement, deliberate
- Brokkr: Exaggerated reactions
- Odin: Grand gestures, takes up space
- Jared: Precise, careful movements

## Crossfade Blending

When transitioning between animation states:

```
Blend time guidelines:
  Idle → Walk:     0.2-0.3s
  Walk → Run:      0.2s
  Walk → Idle:     0.3-0.4s
  Any → Sit:       0.5s (longer = more natural)
  Sit → Stand:     0.4s
  Any → Talk:      0.2s
  Talk → Idle:     0.3s
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Linear interpolation for organic motion | Use easing curves |
| Same walk cycle for all characters | Vary speed, stride, bounce per personality |
| Instant state changes | Use crossfade blending |
| Skip idle animation | Always have breathing/subtle movement |
| Identical animation speed for all sizes | Heavier = slower, lighter = faster |

## Integration with Our Pipeline

- Apply to sv-animation-pipeline Mixamo retargeting (adjust curves post-import)
- Guide animation state machine in sv-r3f-integration (crossfade timings)
- Character personality through motion in sv-character-roster
- Quality checklist for animation review
