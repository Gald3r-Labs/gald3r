---
name: algorithmic-art
description: "Generative art creation with p5.js using seeded randomness, flow fields, particle systems, and interactive parameter exploration. Use for data visualization, background generation, or in-show visual effects."
tags: [generative, art, p5js, creative-coding, visualization, procedural]
---

# Algorithmic Art -- Generative Creative Coding

Framework for creating generative art using p5.js with algorithmic philosophies and seeded randomness.

## When to Use

- Creating generative backgrounds or visual effects
- Data-driven art and visualization
- Interactive parameter exploration
- Procedural texture or pattern generation
- In-show visualizations (compression algorithms, network graphs)

## Core Philosophy

1. **Seeded Randomness**: Every artwork reproducible via seed number
2. **Parametric Variation**: Control output through adjustable parameters
3. **Emergent Behavior**: Simple rules -> complex visual results
4. **Interactive Exploration**: Real-time parameter tuning

## Quick Start

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
</head>
<body>
<script>
let seed = 42;

function setup() {
  createCanvas(800, 800);
  randomSeed(seed);
  noiseSeed(seed);
}

function draw() {
  background(20);
  // Your generative art here
}

function keyPressed() {
  if (key === 'r') { seed++; randomSeed(seed); noiseSeed(seed); redraw(); }
  if (key === 's') saveCanvas('art_' + seed, 'png');
}
</script>
</body>
</html>
```

## Common Techniques

### Flow Fields
```javascript
function drawFlowField() {
  let scale = 0.01;
  for (let x = 0; x < width; x += 10) {
    for (let y = 0; y < height; y += 10) {
      let angle = noise(x * scale, y * scale) * TWO_PI * 2;
      push();
      translate(x, y);
      rotate(angle);
      stroke(255, 50);
      line(0, 0, 10, 0);
      pop();
    }
  }
}
```

### Particle Systems
```javascript
class Particle {
  constructor(x, y) {
    this.pos = createVector(x, y);
    this.vel = p5.Vector.random2D();
    this.life = 255;
  }
  update() {
    this.pos.add(this.vel);
    this.life -= 2;
  }
  draw() {
    noStroke();
    fill(255, this.life);
    circle(this.pos.x, this.pos.y, 4);
  }
}
```

### Recursive Subdivision
```javascript
function subdivide(x, y, w, h, depth) {
  if (depth <= 0 || w < 10) {
    fill(random(200, 255), random(100, 200), random(50, 150));
    rect(x, y, w, h);
    return;
  }
  if (random() > 0.5) {
    let split = random(0.3, 0.7) * w;
    subdivide(x, y, split, h, depth - 1);
    subdivide(x + split, y, w - split, h, depth - 1);
  } else {
    let split = random(0.3, 0.7) * h;
    subdivide(x, y, w, split, depth - 1);
    subdivide(x, y + split, w, h - split, depth - 1);
  }
}
```

## Noise Functions

| Function | Use | Character |
|----------|-----|-----------|
| `noise(x)` | 1D smooth random | Gentle variation |
| `noise(x, y)` | 2D terrain-like | Landscapes, textures |
| `noise(x, y, z)` | 3D evolving | Animated patterns |
| `random()` | Pure random | Scattering, chaos |

## Parameter Controls

```javascript
// Interactive sliders
let params = {
  density: 50,
  speed: 0.01,
  colorShift: 0,
  scale: 1.0
};

function setupControls() {
  let densitySlider = createSlider(10, 200, params.density);
  densitySlider.position(10, height + 10);
  densitySlider.input(() => { params.density = densitySlider.value(); });
}
```

## Seed Navigation (Art Blocks Pattern)

```javascript
// Arrow keys to browse seeds
function keyPressed() {
  if (keyCode === RIGHT_ARROW) seed++;
  if (keyCode === LEFT_ARROW) seed--;
  if (key === 's') saveCanvas(`art_seed${seed}`, 'png');
  randomSeed(seed);
  noiseSeed(seed);
  redraw();
}
```

## Integration with Our Pipeline

- **The Forge compression viz**: Animate middle-out algorithm with flow fields
- **Sindri's screensaver**: Recursive subdivision + dark color palette
- **Network graph backgrounds**: Particle systems showing data flow
- **R3F shader textures**: Generate noise textures for 3D materials
- **Social media content**: Export generative art frames as video backgrounds
