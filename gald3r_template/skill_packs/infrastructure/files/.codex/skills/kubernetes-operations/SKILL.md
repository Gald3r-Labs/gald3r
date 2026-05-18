---
name: kubernetes-operations
description: Kubernetes clusters, kubectl, workloads, networking, Helm, RBAC, and cloud-native ops.
---

# Kubernetes Operations Skill

Comprehensive Kubernetes cluster management, workload orchestration, and cloud-native application deployment.

## Overview

This skill provides:
- **Cluster Management**: Node management, namespace organization, resource quotas
- **Workload Orchestration**: Deployments, StatefulSets, DaemonSets, Jobs
- **Networking**: Services, Ingress, Network Policies, Service Mesh
- **Storage**: PersistentVolumes, StorageClasses, Volume management
- **Security**: RBAC, Pod Security Standards, Secrets management
- **Helm**: Chart development, repository management, releases
- **Troubleshooting**: Debugging pods, analyzing events, log analysis

## When to Use This Skill

Activate when the user needs to:
- Deploy applications to Kubernetes
- Create or modify Kubernetes manifests
- Set up Helm charts
- Configure ingress and services
- Manage cluster resources
- Troubleshoot pod issues
- Set up autoscaling
- Configure security policies

## Prerequisites

### Required Tools
```bash
# Check kubectl installation
kubectl version --client

# Check Helm installation
helm version

# Verify cluster connection
kubectl cluster-info
```

### Installation (if needed)

**Windows:**
```powershell
# kubectl
winget install -e --id Kubernetes.kubectl

# Helm
winget install -e --id Helm.Helm
```

**macOS:**
```bash
brew install kubectl helm
```

**Linux:**
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

## Core Workflows

### 1. Deploy Application

**Workflow:**
1. Create namespace (if needed)
2. Create ConfigMap/Secret for configuration
3. Create Deployment manifest
4. Create Service manifest
5. Create Ingress (if external access needed)
6. Apply manifests
7. Verify deployment

**Example:**
```bash
# Create namespace
kubectl create namespace myapp

# Apply manifests
kubectl apply -f manifests/ -n myapp

# Verify deployment
kubectl get pods -n myapp
kubectl rollout status deployment/myapp -n myapp
```

### 2. Create Helm Chart

**Workflow:**
1. Create chart structure
2. Define Chart.yaml
3. Create values.yaml
4. Create templates
5. Test chart locally
6. Package and deploy

**Example:**
```bash
# Create chart
helm create myapp

# Lint chart
helm lint myapp/

# Template locally
helm template myapp myapp/ -f values-dev.yaml

# Install
helm install myapp myapp/ -n myapp --create-namespace

# Upgrade
helm upgrade myapp myapp/ -n myapp -f values-prod.yaml
```

### 3. Troubleshoot Pods

**Workflow:**
1. Check pod status
2. View pod events
3. Check logs
4. Exec into container
5. Analyze resource usage
6. Check network connectivity

**Example:**
```bash
# Get pod status
kubectl get pods -n myapp -o wide

# Describe pod (shows events)
kubectl describe pod myapp-xxx -n myapp

# View logs
kubectl logs myapp-xxx -n myapp -f
kubectl logs myapp-xxx -n myapp --previous  # Previous container

# Exec into pod
kubectl exec -it myapp-xxx -n myapp -- /bin/sh

# Check resources
kubectl top pod myapp-xxx -n myapp
```

### 4. Scale Application

**Workflow:**
1. Analyze current resource usage
2. Configure HPA/VPA
3. Set resource requests/limits
4. Test autoscaling
5. Monitor behavior

**Example:**
```bash
# Manual scale
kubectl scale deployment/myapp --replicas=5 -n myapp

# Create HPA
kubectl autoscale deployment/myapp --cpu-percent=70 --min=3 --max=10 -n myapp

# Check HPA status
kubectl get hpa -n myapp
```

## Quick Reference

### Essential kubectl Commands

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes -o wide
kubectl top nodes

# Namespace operations
kubectl get namespaces
kubectl create namespace <name>
kubectl config set-context --current --namespace=<name>

# Pod operations
kubectl get pods -n <namespace>
kubectl describe pod <name> -n <namespace>
kubectl logs <pod> -n <namespace> -f
kubectl exec -it <pod> -n <namespace> -- /bin/sh
kubectl delete pod <pod> -n <namespace>

# Deployment operations
kubectl get deployments -n <namespace>
kubectl rollout status deployment/<name> -n <namespace>
kubectl rollout history deployment/<name> -n <namespace>
kubectl rollout undo deployment/<name> -n <namespace>
kubectl scale deployment/<name> --replicas=<count> -n <namespace>

# Service operations
kubectl get services -n <namespace>
kubectl port-forward svc/<name> <local>:<remote> -n <namespace>

# ConfigMap/Secret
kubectl get configmaps -n <namespace>
kubectl get secrets -n <namespace>
kubectl create secret generic <name> --from-literal=key=value -n <namespace>

# Events and debugging
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
kubectl describe node <node-name>
```

### Essential Helm Commands

```bash
# Repository management
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo <keyword>

# Chart operations
helm create <chart-name>
helm lint <chart-path>
helm template <release> <chart> -f values.yaml

# Release management
helm install <release> <chart> -n <namespace> --create-namespace
helm upgrade <release> <chart> -n <namespace> -f values.yaml
helm rollback <release> <revision> -n <namespace>
helm uninstall <release> -n <namespace>

# Release info
helm list -n <namespace>
helm history <release> -n <namespace>
helm get values <release> -n <namespace>
helm get manifest <release> -n <namespace>
```

## Manifest Templates

### Deployment Template
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .name }}
  namespace: {{ .namespace }}
  labels:
    app: {{ .name }}
spec:
  replicas: {{ .replicas | default 3 }}
  selector:
    matchLabels:
      app: {{ .name }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: {{ .name }}
    spec:
      containers:
        - name: {{ .name }}
          image: {{ .image }}
          ports:
            - containerPort: {{ .port }}
          resources:
            requests:
              cpu: {{ .cpu_request | default "100m" }}
              memory: {{ .memory_request | default "128Mi" }}
            limits:
              cpu: {{ .cpu_limit | default "500m" }}
              memory: {{ .memory_limit | default "512Mi" }}
          livenessProbe:
            httpGet:
              path: /healthz
              port: {{ .port }}
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: {{ .port }}
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Service Template
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .name }}
  namespace: {{ .namespace }}
spec:
  type: {{ .type | default "ClusterIP" }}
  ports:
    - port: {{ .port }}
      targetPort: {{ .targetPort }}
      protocol: TCP
  selector:
    app: {{ .name }}
```

### Ingress Template
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .name }}
  namespace: {{ .namespace }}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - {{ .host }}
      secretName: {{ .name }}-tls
  rules:
    - host: {{ .host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .name }}
                port:
                  number: {{ .port }}
```

## Best Practices Checklist

### Deployment
- [ ] Use specific image tags (not `latest`)
- [ ] Set resource requests and limits
- [ ] Configure health probes
- [ ] Set pod disruption budgets
- [ ] Use pod anti-affinity for HA
- [ ] Configure update strategy

### Security
- [ ] Run as non-root user
- [ ] Apply pod security standards
- [ ] Use RBAC with least privilege
- [ ] Store secrets in Secret resources
- [ ] Apply network policies
- [ ] Enable audit logging

### Operations
- [ ] Set up monitoring (Prometheus)
- [ ] Configure logging (ELK/Loki)
- [ ] Enable tracing (Jaeger/Zipkin)
- [ ] Document runbooks
- [ ] Test disaster recovery

## Troubleshooting Guide

### Pod Issues

| Issue | Command | Solution |
|-------|---------|----------|
| CrashLoopBackOff | `kubectl logs <pod> --previous` | Check application logs |
| ImagePullBackOff | `kubectl describe pod <pod>` | Verify image name/registry auth |
| Pending | `kubectl describe pod <pod>` | Check resources/node affinity |
| OOMKilled | `kubectl describe pod <pod>` | Increase memory limits |

### Common Fixes

```bash
# Pod stuck in Terminating
kubectl delete pod <pod> --force --grace-period=0 -n <namespace>

# Fix stuck namespace deletion
kubectl get namespace <ns> -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/<ns>/finalize" -f -

# Debug network issues
kubectl run debug --rm -it --image=nicolaka/netshoot -- /bin/bash

# Check DNS
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default
```

## Related Skills
- **docker-specialist**: Container image management
- **cicd-pipelines**: Deployment automation
- **portainer-management**: Container UI management
- **devops-engineer**: Infrastructure automation

## Related Agents
- `kubernetes-specialist`: Full K8s expertise
- `devops-engineer`: Infrastructure and deployment
- `cicd-specialist`: Pipeline automation
- `security-auditor`: Security review

---

**Note:** Always test changes in a non-production environment first. Use `kubectl diff -f manifest.yaml` to preview changes before applying.
