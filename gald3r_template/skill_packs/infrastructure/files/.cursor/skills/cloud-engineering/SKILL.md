---
name: cloud-engineering
description: Cloud architecture, IaC, and cost optimization across AWS, GCP, and Azure. Covers Terraform, Kubernetes, and serverless.
version: 2.0.0
---

# Cloud Engineering Skill

Cloud architecture, infrastructure as code, and cost optimization across AWS, GCP, and Azure.

## When to Use

- Choosing a cloud platform or comparing services
- Writing Terraform/IaC for infrastructure provisioning
- Optimizing cloud costs (reserved instances, right-sizing, lifecycle policies)
- Deploying Kubernetes workloads or Helm charts
- Designing serverless architectures (Lambda, Cloud Functions, Azure Functions)
- Setting up monitoring, alerting, and observability
- Planning multi-cloud or cloud-agnostic strategies

## Process

1. **Assess Requirements** — Identify workload type, compliance needs, team expertise, and budget constraints. Use `reference/platform_comparison.md` to select the right platform.
2. **Design Infrastructure** — Define architecture using cloud-native or portable services. Use `reference/terraform_patterns.md` for IaC structure and module patterns.
3. **Optimize Costs** — Apply reserved instances, spot pricing, lifecycle policies, and right-sizing. See `reference/cost_optimization.md` for strategies and checklists.
4. **Deploy & Orchestrate** — Use Kubernetes for container workloads or serverless for event-driven patterns. See `reference/kubernetes_configs.md` and `reference/serverless_patterns.md`.
5. **Monitor & Iterate** — Set up alarms, dashboards, and key metrics. See `reference/monitoring_alerting.md` for configurations and thresholds.

## Reference Index

| File | Contents |
|------|----------|
| `reference/platform_comparison.md` | AWS/GCP/Azure service tables, selection criteria, multi-cloud guidance |
| `reference/terraform_patterns.md` | Project structure, HCL examples, remote state, module patterns |
| `reference/cost_optimization.md` | Pricing tiers, reserved vs spot, S3 lifecycle, monthly checklist |
| `reference/kubernetes_configs.md` | Deployment YAMLs, Helm patterns, service configs |
| `reference/serverless_patterns.md` | Lambda/Cloud Functions patterns, API Gateway, event-driven architectures |
| `reference/monitoring_alerting.md` | CloudWatch/Stackdriver configs, key metrics, alert thresholds |

## Security Principles

1. **Least Privilege** — Grant minimum permissions; avoid IAM wildcards
2. **No Root Access** — Use IAM roles, enable MFA on root
3. **Roles Over Keys** — EC2 instance profiles, ECS task roles, Lambda execution roles
4. **Secrets in Vaults** — AWS Secrets Manager, SSM Parameter Store, or equivalent

## Integration

- **kubernetes-operations** skill — Detailed K8s cluster management and Helm operations
- **cicd-pipelines** skill — GitHub Actions, GitLab CI, Jenkins deployment pipelines
- **database-standards** skill — Database naming conventions and schema patterns

## External Resources

- [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Registry](https://registry.terraform.io)
- [AWS Pricing Calculator](https://calculator.aws)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)

---
*This skill supports: cloud-engineer agent*
