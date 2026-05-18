---
name: manim-animation
description: Manim math animations—3Blue1Brown style—scenes, LaTeX, graphs, and algorithm demos in Python.
tags: [animation, python, math, educational, visualization, latex, 3blue1brown]
---

# Manim Community - Mathematical Animation Engine

Create mathematical animations using Manim Community, a Python framework popularized by 3Blue1Brown.

## When to Use

- Mathematical animations and visualizations
- Educational video content
- Geometric shapes and transformations
- LaTeX equation animations
- Graphs, charts, and coordinate systems
- Algorithmic demonstrations (sorting, graph traversal, etc.)

## Core Concepts

- **Scenes**: Canvas for animations where you orchestrate mobjects
- **Mobjects**: Mathematical objects (shapes, text, equations)
- **Animations**: Transformations (Write, Create, Transform, FadeIn)
- **LaTeX Integration**: Native mathematical notation rendering

## Quick Start

```bash
# Install
pip install manim

# Render a scene
manim -pql scene.py MyScene
```

## Scene Structure

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # Create objects
        circle = Circle(radius=2, color=BLUE)
        text = Text("Hello Manim!")

        # Animate
        self.play(Create(circle))
        self.play(Write(text))
        self.play(FadeOut(circle), FadeOut(text))
```

## Key Mobjects

| Mobject | Purpose | Example |
|---------|---------|---------|
| `Circle`, `Square`, `Triangle` | Basic shapes | `Circle(radius=1, color=RED)` |
| `Text` | Plain text | `Text("Hello", font_size=48)` |
| `MathTex` | LaTeX math | `MathTex(r"\int_0^1 x^2 dx")` |
| `Axes` | Coordinate system | `Axes(x_range=[-3,3], y_range=[-3,3])` |
| `NumberPlane` | Grid plane | `NumberPlane()` |
| `Graph` | Function plots | `axes.plot(lambda x: x**2)` |
| `Arrow`, `Line` | Connectors | `Arrow(start=LEFT, end=RIGHT)` |
| `VGroup` | Group objects | `VGroup(circle, text)` |

## Key Animations

| Animation | Purpose |
|-----------|---------|
| `Create(mob)` | Draw shape from nothing |
| `Write(mob)` | Write text/equation |
| `FadeIn(mob)` / `FadeOut(mob)` | Opacity transitions |
| `Transform(a, b)` | Morph a into b |
| `ReplacementTransform(a, b)` | Replace a with b |
| `MoveToTarget(mob)` | Move to `.target` position |
| `Indicate(mob)` | Flash highlight |
| `Circumscribe(mob)` | Draw circle around |

## Positioning

```python
# Absolute positioning
obj.move_to(UP * 2 + RIGHT * 3)
obj.to_edge(LEFT)
obj.to_corner(UL)

# Relative positioning
obj2.next_to(obj1, DOWN, buff=0.5)
obj2.align_to(obj1, LEFT)

# Direction constants: UP, DOWN, LEFT, RIGHT, ORIGIN
# Corners: UL, UR, DL, DR
```

## Color Constants

`RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, WHITE, GREY, PINK, TEAL, GOLD, MAROON`

## Render Quality Flags

| Flag | Resolution | Use |
|------|-----------|-----|
| `-pql` | 480p | Quick preview |
| `-pqm` | 720p | Medium quality |
| `-pqh` | 1080p | High quality |
| `-pqk` | 4K | Final render |

## Common Patterns

### Equation Step-by-Step
```python
eq1 = MathTex(r"x^2 + 2x + 1")
eq2 = MathTex(r"(x + 1)^2")
self.play(Write(eq1))
self.wait()
self.play(TransformMatchingTex(eq1, eq2))
```

### Graph Animation
```python
axes = Axes(x_range=[-3, 3], y_range=[-1, 9])
graph = axes.plot(lambda x: x**2, color=BLUE)
label = axes.get_graph_label(graph, label="x^2")
self.play(Create(axes), Create(graph), Write(label))
```

### Sorting Visualization
```python
bars = VGroup(*[Rectangle(height=h, width=0.5) for h in data])
bars.arrange(RIGHT, buff=0.1)
# Animate swaps with Transform
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| `self.wait(10)` for long pauses | Use `self.wait(1)` or `self.wait(2)` |
| Hardcoded pixel positions | Use relative positioning (`next_to`, `align_to`) |
| Too many objects at once | Build up gradually, remove old objects |
| Skip `self.wait()` between steps | Give viewer time to absorb |

## Integration with Our Pipeline

- **Sindri explains algorithms**: Use Manim for whiteboard algorithm visualizations
- **The Forge compression**: Visualize middle-out compression with animated data flows
- **Investor presentations**: Animated charts and growth metrics
- Export frames as PNG sequence → composite in Remotion or video editor
