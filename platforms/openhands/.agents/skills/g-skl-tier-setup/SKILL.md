---
name: g-skl-tier-setup
description: Configurable product-tier onboarding skill. SETUP creates release_profiles/, scaffolds template_{tier}/ directories, and writes .gald3r/.identity tier metadata. ENABLE annotates existing SUBSYSTEMS.md with min_tier:, infers defaults from subsystem content, and calls platform_parity_sync -TierSync. Ships in full + adv tiers only (slim installs are pre-configured).
operations: [SETUP, ENABLE]
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
