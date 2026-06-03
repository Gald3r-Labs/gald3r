---
name: cloud-gpu-training
description: >
  Run PyTorch / ML training on rented cloud GPUs (RunPod, Lambda, Vast.ai) when local training
  is too slow. Covers security rules for uploads, SCP workflow, batch sizing, and cost estimates.
skill_group: "ai-ml-dev"
skill_category: "AI & Machine Learning Development"
---

# Cloud GPU Training

Run ML training jobs on rented cloud GPUs when local hardware is too slow or would block the developer's machine for too long.

## When to Use

- Training run would take >24 hours locally
- User wants to keep local GPU free for other work
- Model fits in cloud GPU memory (A100 80GB or H100 80GB)
- The data being uploaded is not highly sensitive IP

## Quick Reference

### Providers (March 2026 pricing)

| Provider | A100 80GB | H100 SXM | Best For |
|----------|-----------|----------|----------|
| Lambda Labs | $1.29/hr | $2.89/hr | ML-focused, simple |
| RunPod | $1.39/hr | $2.69/hr | Good UI, reliable |
| Vast.ai | $1.89/hr | $1.87/hr | Cheapest H100 |

### Security Rules

1. NEVER upload .env, API keys, credentials, or secrets
2. NEVER upload patent-protected algorithms or proprietary encoding schemes
3. Use SCP (SSH) for all file transfers ΓÇö never plain HTTP
4. Delete instances immediately after downloading results
5. Review all files before upload ΓÇö check for hardcoded secrets in comments

### Batch Size Scaling Guide

| GPU | VRAM | Typical batch_size | gradient_accumulation |
|-----|------|-------------------|----------------------|
| RTX 4090 | 24 GB | 4-16 | 16-4 |
| A100 80GB | 80 GB | 64-128 | 1 |
| H100 80GB | 80 GB | 64-128 | 1 |

Effective batch = batch_size ├ù gradient_accumulation. Keep effective batch ~64.

### Workflow

1. Prepare upload bundle (training script + data + model code)
2. Create cloud instance (PyTorch template)
3. Upload via SCP
4. SSH in, verify files, launch training in tmux/screen
5. Monitor progress via logs
6. Download results (checkpoints + logs)
7. Terminate instance immediately
8. Log cost in `.gald3r/logs/cloud_costs.json`

### Estimating Cost

```
cost = (local_epoch_hours / speedup_factor) ├ù num_epochs ├ù provider_rate
```

- A100 speedup vs RTX 4090: ~6-8x (mainly from larger batch size)
- H100 speedup vs RTX 4090: ~10-12x

### Tips

- Always use `tmux` or `screen` on the remote instance so training survives SSH disconnects
- Download checkpoints incrementally (don't wait until the end)
- Set up monitoring early ΓÇö `nvidia-smi -l 5` in a separate tmux pane
