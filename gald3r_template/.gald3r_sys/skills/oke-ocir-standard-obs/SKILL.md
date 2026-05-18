---
name: oke-ocir-standard-obs
description: OBS-specific OKE and OCIR manifest standard. Use when reviewing or changing Kubernetes manifests, OCIR image references, OKE deploy behavior, imagePullSecrets, Gitea Actions deployment workflows, or the Steve Reis 2026-04-28 OCIR remediation commit in the Midgard repo and related OBS Gard repos.
---

# OKE/OCIR Standard_OBS

## Purpose

Use this skill to preserve the OBS OKE/OCIR standard captured by Steve Reis's 2026-04-28 Gitea commit in Midgard and the matching 2026-04-29 Gitea remediations observed in Apigard and Atmgard:

`33bd6009ee81714cb4fd51aa71dc7eea50065567`

`fix(k8s): qualify all images with OCIR registry across midgard manifests`

Apigard companion commit:

`17d1938`

`fix(k8s): qualify all images with OCIR registry + add default SA pull-secret`

Atmgard companion commit:

`6491cf4`

`fix(k8s): qualify init container image with OCIR registry`

The goal is to keep OKE-applied manifests from resolving ambiguous short image names on Oracle Linux / CRI-O nodes.

## Core Standard

- Treat `iad.ocir.io/idi6pligu0ox/obsrepo` as the canonical OCIR prefix for OBS OKE images.
- Do not introduce unqualified short images such as `postgres:16-alpine`, `postgres:16-bookworm`, `redis:7-alpine`, `redis:7-bookworm`, `curlimages/curl:8.5.0`, `busybox:1.36`, `docker:27-dind`, `grafana/grafana`, `grafana/loki`, `grafana/promtail`, or `gitea/act_runner` into manifests that can be applied to OKE.
- Static upstream/runtime images in `k8s/base/` should be explicitly qualified to OCIR once mirrored.
- Custom Midgard/Gard app images may remain as the accepted local base names when they are intentionally remapped by the relevant base or production kustomization.
- Keep `ocir-secret` as the pull secret name for OCIR access across Midgard and Gard namespaces.
- Keep `k8s/base/serviceaccount-default.yaml` in the base kustomization so the target app namespace default ServiceAccount receives `imagePullSecrets: [{ name: ocir-secret }]`.

## Accepted Existing Patterns

These related patterns were already acceptable and should not be changed just because this skill is active:

- `.gitea/workflows/deploy-midgard-api.yml`, `.gitea/workflows/deploy-midgard-ui.yml`, and `.gitea/workflows/build-midgard-base.yml` build and push custom images to OCIR using `REGISTRY=iad.ocir.io`, `NAMESPACE=idi6pligu0ox`, and `REPO=obsrepo`.
- The deploy workflows intentionally have path filters. A `k8s/base/`-only manifest change does not automatically trigger the API/UI deploy workflows.
- `k8s/overlays/prod/kustomization.yaml` remains the accepted production overlay for remapping custom app images and adding `ocir-secret` to Deployments and StatefulSets.
- `k8s/scripts/create-ocir-secrets.ps1` remains the accepted helper for creating or refreshing `ocir-secret` across Midgard and Gard namespaces.

## Review Checklist

When reviewing OKE/OCIR changes:

1. Confirm every OKE-rendered image either starts with `iad.ocir.io/idi6pligu0ox/obsrepo/` or is intentionally remapped by the production overlay.
2. Confirm any newly referenced upstream image has been mirrored into `obsrepo` before the manifest points at it.
3. Confirm `ocir-secret` exists in the target namespace or is attached through the relevant ServiceAccount, Deployment, StatefulSet, or overlay patch.
4. Confirm `k8s/base/kustomization.yaml` includes `serviceaccount-default.yaml` when the base contains the default ServiceAccount pull-secret manifest.
5. Do not broaden deploy workflow path filters for manifest-only changes unless the user explicitly asks for that behavior.
6. Prefer source-of-truth manifests over live-only `kubectl set image` patches. Live patches are acceptable as an incident response step, but source should be updated afterward.

## Validation Commands

Use the same validation shape Steve documented:

```powershell
kubectl kustomize k8s/base
kubectl kustomize k8s/overlays/prod
```

For image review, scan rendered output for short names before applying:

```powershell
kubectl kustomize k8s/base | Select-String "image:"
kubectl kustomize k8s/overlays/prod | Select-String "image:"
```

The expected result for OKE-bound manifests is zero unqualified upstream images.
