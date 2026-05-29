---
name: g-skl-comfyui
description: ComfyUI V5 agent integration for local GPU image/video generation. Install, launch, manage workflows, and run AnimateDiff/SDXL pipelines via the ComfyUI REST API. Local GPU path — zero cloud costs. Use for gald3r_throne theme pack animation or any offline image/video generation.
token_budget: medium
subsystem_memberships: [UI_AND_OUTPUT]
---

# g-skl-comfyui — ComfyUI V5 Agent Integration

Enables gald3r agents to install, launch, and operate ComfyUI V5 workflows on demand. This is the **local GPU path** for image/video generation (no cloud credits required). The complementary **cloud path** is `higgsfield` (Seedance 2.0, Kling, etc.).

**When to use this skill:**
- User has a local GPU and wants cost-free image/video generation
- Generating gald3r_throne animation theme pack assets locally
- Running AnimateDiff video generation from SDXL models
- Operating node-graph workflows with full control over the pipeline

**Prerequisites:** NVIDIA GPU (8GB+ VRAM recommended for SDXL), Python 3.10+

---

## Operations

### INSTALL

Check for existing ComfyUI installation and install V5 if missing.

**Steps:**
1. Check for existing ComfyUI: look for `ComfyUI/` directory in common locations:
   - `G:\ComfyUI\`, `C:\ComfyUI\`, `~/ComfyUI/`, current directory `./ComfyUI/`
   - If found: report version via `python ComfyUI/main.py --version`
2. Check GPU availability:
   ```powershell
   nvidia-smi 2>$null
   # If exit code non-zero: warn "No NVIDIA GPU detected — ComfyUI will run on CPU (very slow)"
   ```
3. If ComfyUI not found, install V5:
   ```bash
   # Option A: pip install (ComfyUI standalone package)
   pip install comfyui

   # Option B: git clone (full node-graph editor + web UI)
   git clone https://github.com/comfyanonymous/ComfyUI.git
   cd ComfyUI
   pip install -r requirements.txt
   ```
4. Verify install: `python -c "import comfy; print('ComfyUI ready')"` or check `ComfyUI/main.py` exists
5. Report: install path, GPU status, Python version

**Cost guard:** Before starting a long video generation job, surface GPU time estimate:
- SDXL image (512×512, 20 steps): ~15-30s on RTX 3090
- AnimateDiff clip (16 frames, 512×512): ~2-5 min on RTX 3090
- Wait for explicit "go" before starting multi-minute jobs

---

### LAUNCH

Start the ComfyUI server and wait for API readiness.

**Steps:**
1. Locate ComfyUI installation (same discovery as INSTALL)
2. Start server:
   ```bash
   python ComfyUI/main.py --listen 0.0.0.0 --port 8188
   # Background: python ComfyUI/main.py --port 8188 &
   ```
3. Poll for readiness: `GET http://localhost:8188/` — wait up to 30s with 2s intervals
4. Return server URL: `http://localhost:8188`
5. Report: server URL, GPU detected, available model list from `GET /object_info`

**Port conflicts:** If 8188 is occupied, try 8189, 8190. Report the actual port used.

---

### RUN_WORKFLOW

Submit a workflow and poll for completion.

**Inputs:**
- `workflow` — path to workflow JSON, or workflow name from built-in templates (see below)
- `params` — optional dict of prompt parameters to override in the workflow JSON

**Steps:**
1. Load workflow JSON from path or template
2. Apply any parameter overrides (e.g., replace prompt text, seed, resolution)
3. Submit to ComfyUI:
   ```python
   import requests, json, time

   workflow_data = json.load(open(workflow_path))
   # Apply params overrides to prompt nodes

   response = requests.post("http://localhost:8188/prompt", json={"prompt": workflow_data})
   prompt_id = response.json()["prompt_id"]
   ```
4. Poll for completion:
   ```python
   while True:
       history = requests.get(f"http://localhost:8188/history/{prompt_id}").json()
       if prompt_id in history:
           outputs = history[prompt_id]["outputs"]
           break
       time.sleep(2)
   ```
5. Extract output file paths from `outputs` dict
6. Return: list of output file paths (images/videos saved to `ComfyUI/output/`)

---

### STATUS

Check ComfyUI server status and queue.

```python
# Queue status
queue = requests.get("http://localhost:8188/queue").json()
# {"queue_running": [...], "queue_pending": [...]}

# System stats
stats = requests.get("http://localhost:8188/system_stats").json()
# {"system": {"os": ..., "python_version": ..., "embedded_python": ...}, "devices": [...]}
```

Report: running/pending jobs, GPU VRAM used/free, active model.

---

### STOP

Stop the ComfyUI server process.
```powershell
# Windows: find and kill ComfyUI process
Get-Process python | Where-Object { $_.CommandLine -like "*ComfyUI*" } | Stop-Process
```

---

## Built-In Workflow Templates

### text-to-image (SDXL)
Standard SDXL image generation workflow. Parameters:
- `prompt` — positive text prompt
- `negative_prompt` — negative prompt (default: "low quality, blurry")
- `width`, `height` — image dimensions (default: 1024×1024)
- `steps` — sampling steps (default: 20)
- `seed` — random seed (-1 for random)

Template path: call `RUN_WORKFLOW` with `workflow: "sdxl_text_to_image"`

### image-to-video (AnimateDiff)
Generate a short video clip from a still image using AnimateDiff.
- `image_path` — input image path
- `frames` — number of frames (default: 16)
- `fps` — frames per second (default: 8)
- `motion_strength` — animation intensity 0.0–1.0 (default: 0.75)

Template path: call `RUN_WORKFLOW` with `workflow: "animatediff_i2v"`

### Theme Pack Starter
Pre-configured workflow for theme pack animation assets:
- Uses SDXL for style frame generation
- AnimateDiff for character movement clips
- Output convention: save to `G:\gald3r_ecosystem\gald3r_throne\src-tauri\maestro2\comfyui_workflows\`
- Workflow JSON: store at the above path as `maestro2_theme_starter.json`

Template path: call `RUN_WORKFLOW` with `workflow: "maestro2_theme_starter"`

---

## ComfyUI REST API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prompt` | POST | Submit a workflow JSON for execution |
| `/history/{prompt_id}` | GET | Get execution history + output paths |
| `/queue` | GET | View current queue state |
| `/system_stats` | GET | GPU, VRAM, Python info |
| `/object_info` | GET | List all available nodes + parameters |
| `/view?filename={f}&type=output` | GET | Download an output file |

---

## Theme Pack Integration

Animation theme pack workflows live at:
```
G:\gald3r_ecosystem\gald3r_throne\src-tauri\maestro2\comfyui_workflows\
```

For cloud-based generation without local GPU, use `higgsfield` skill (T848).

---

## Guardrails

- **Cost guard**: surface GPU time estimate before any multi-minute job — wait for explicit "go"
- **VRAM warning**: SDXL needs ≥8GB VRAM; AnimateDiff needs ≥10GB. Check via `STATUS` before submitting
- **CPU fallback**: ComfyUI runs on CPU but is 10-50× slower — warn the user before proceeding
- **Output location**: all outputs in `ComfyUI/output/` — remind user to move files if needed
