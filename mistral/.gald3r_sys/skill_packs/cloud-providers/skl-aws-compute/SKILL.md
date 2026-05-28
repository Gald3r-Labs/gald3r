---
name: skl-aws-compute
description: AWS compute and deployment ΓÇö EC2, Lambda, ECS, App Runner, CLI essentials, CDK patterns. Requires skl-aws-iam for permission setup.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# AWS Compute & Deployment

Core compute services: EC2 (VMs), Lambda (serverless), ECS (containers), App Runner (managed containers).

## Prerequisites

- AWS account + CLI configured: `aws configure` or `aws sso login`
- IAM permissions (see `skl-aws-iam` for least-privilege templates)
- CDK: `npm install -g aws-cdk && cdk bootstrap`

## Operation: EC2

Virtual machine lifecycle management.

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \  # Amazon Linux 2023
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=my-server}]'

# List running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].[InstanceId,InstanceType,PublicIpAddress,Tags[?Key=='Name'].Value|[0]]" \
  --output table

# SSH access
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-xxxxx --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub

# Stop/terminate
aws ec2 stop-instances --instance-ids i-xxxxx
aws ec2 terminate-instances --instance-ids i-xxxxx
```

**Spot vs on-demand cost guidance:**
| Mode | When to use | Interruption risk | Savings |
|------|-------------|------------------|---------|
| On-demand | Prod, stateful | None | Baseline |
| Spot | Batch, CI, stateless | ~5-15% | Up to 90% |
| Reserved (1yr) | Stable baseline | None | ~30-40% |

```bash
# Launch Spot instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type c6i.large \
  --instance-market-options '{"MarketType":"spot","SpotOptions":{"MaxPrice":"0.05","SpotInstanceType":"one-time"}}'

# --user-data: bootstrap script run on first boot (cloud-init)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-xxxxxxxx \
  --user-data file://bootstrap.sh
# bootstrap.sh example:
# #!/bin/bash
# apt-get update -y && apt-get install -y docker.io git
# systemctl enable docker && systemctl start docker
```

**Useful instance types:**
| Use Case | Type | vCPU | RAM |
|----------|------|------|-----|
| Dev/test | t3.micro | 2 | 1 GB |
| Web server | t3.small | 2 | 2 GB |
| App server | t3.medium | 2 | 4 GB |
| Compute | c6i.large | 2 | 4 GB |
| Memory | r6i.large | 2 | 16 GB |

## Operation: LAMBDA

Serverless function management.

```bash
# Create function (Python)
aws lambda create-function \
  --function-name my-function \
  --runtime python3.12 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler index.handler \
  --zip-file fileb://function.zip

# Update code
zip -r function.zip . && aws lambda update-function-code \
  --function-name my-function --zip-file fileb://function.zip

# Invoke
aws lambda invoke --function-name my-function \
  --payload '{"key":"value"}' --cli-binary-format raw-in-base64-out output.json

# View logs
aws logs tail /aws/lambda/my-function --follow

# Set env vars
aws lambda update-function-configuration \
  --function-name my-function \
  --environment "Variables={DB_URL=postgres://...,API_KEY=secret}"
```

**Lambda Layers (shared dependencies):**
```bash
# Build layer package
mkdir -p layer/python && pip install requests -t layer/python/
cd layer && zip -r ../my-layer.zip python/

# Publish layer
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name my-dependencies \
  --zip-file fileb://my-layer.zip \
  --compatible-runtimes python3.12 \
  --query "LayerVersionArn" --output text)

# Attach layer to function
aws lambda update-function-configuration \
  --function-name my-function --layers $LAYER_ARN
```

**Cold start mitigation:**
| Technique | Effect | Implementation |
|-----------|--------|----------------|
| Provisioned Concurrency | Eliminates cold starts | `--provisioned-concurrency 5` on alias/version |
| Smaller package | Faster init | Use Layers for deps; only app code in .zip |
| SnapStart (Java) | Sub-100ms | `--snap-start ApplyOn=PublishedVersions` |
| Ping warmers | Reduces frequency | CloudWatch cron every 5min invoking function |
| Avoid VPC unless needed | ~500ms saving | VPC adds ENI attachment latency |

## Operation: ECS

Containerized workloads with Fargate (serverless) or EC2 launch type.

```bash
# Create cluster
aws ecs create-cluster --cluster-name my-cluster

# Register task definition (fargate)
aws ecs register-task-definition --cli-input-json file://task-def.json

# Run task
aws ecs run-task \
  --cluster my-cluster \
  --task-definition my-task:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

# Create service (persistent)
aws ecs create-service \
  --cluster my-cluster --service-name my-service \
  --task-definition my-task:1 --desired-count 2 \
  --launch-type FARGATE

# View service status
aws ecs describe-services --cluster my-cluster --services my-service
```

**ECS log driver config (awslogs):**
Add to your task definition JSON under `logConfiguration`:
```json
{
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/my-task",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "ecs",
      "awslogs-create-group": "true"
    }
  }
}
```
```bash
# Create the log group first (or use awslogs-create-group=true)
aws logs create-log-group --log-group-name /ecs/my-task

# Tail ECS task logs
aws logs tail /ecs/my-task --follow
```

## Operation: APP-RUNNER

Fully managed container service ΓÇö simplest path from Docker image to URL.

```bash
# Create service from ECR image
aws apprunner create-service \
  --service-name my-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/my-app:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8080"}
    },
    "AutoDeploymentsEnabled": true
  }'

# List services
aws apprunner list-services

# Pause/resume (billing stops when paused)
aws apprunner pause-service --service-arn arn:...
aws apprunner resume-service --service-arn arn:...
```

## Operation: CLI

Common utility commands.

```bash
# Get current account/identity
aws sts get-caller-identity

# Set default region
export AWS_DEFAULT_REGION=us-east-1

# Use named profile
aws --profile production ec2 describe-instances

# Enable CLI pager (avoids interactive less)
export AWS_PAGER=""
```

## Operation: CDK

Infrastructure as Code with AWS CDK (TypeScript).

```bash
# Init new CDK app
cdk init app --language typescript

# List stacks
cdk ls

# Deploy
cdk deploy --require-approval never

# Diff (preview changes)
cdk diff

# Destroy
cdk destroy
```

**Lambda CDK pattern:**
```typescript
import * as lambda from 'aws-cdk-lib/aws-lambda';
const fn = new lambda.Function(this, 'MyFn', {
  runtime: lambda.Runtime.PYTHON_3_12,
  handler: 'index.handler',
  code: lambda.Code.fromAsset('lambda'),
  environment: { DB_URL: process.env.DB_URL! }
});
```

**EC2 CDK pattern:**
```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2';
const vpc = ec2.Vpc.fromLookup(this, 'VPC', { isDefault: true });
const instance = new ec2.Instance(this, 'MyServer', {
  vpc,
  instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
  machineImage: ec2.MachineImage.latestAmazonLinux2023(),
  userData: ec2.UserData.custom('#!/bin/bash\napt-get update -y\napt-get install -y docker.io')
});
instance.connections.allowFromAnyIpv4(ec2.Port.tcp(22));
```

**ECS CDK pattern (Fargate):**
```typescript
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';

const cluster = new ecs.Cluster(this, 'MyCluster', { vpc });

const service = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'MyService', {
  cluster,
  cpu: 256, memoryLimitMiB: 512,
  desiredCount: 2,
  taskImageOptions: {
    image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
    containerPort: 8080,
    logDriver: ecs.LogDrivers.awsLogs({ streamPrefix: 'ecs', logRetention: 14 })
  }
});
```
