---
name: skl-aws-iam
description: AWS IAM & security reference ΓÇö users, roles, policies, STS, Secrets Manager, audit. 5 copy-paste least-privilege policy templates. Foundation for all AWS skills.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---
# AWS IAM & Security

**Activate for**: "AWS IAM", "IAM policy", "IAM role", "assume role", "access key", "STS", "Secrets Manager", "SSM Parameter", "CloudTrail", "GuardDuty"

---

## USERS ΓÇö IAM User Management

### Create a user (programmatic only)
```bash
aws iam create-user --user-name deploy-bot
aws iam create-access-key --user-name deploy-bot
# Store AccessKeyId + SecretAccessKey in Secrets Manager immediately
```

### Create a user (console + MFA)
```bash
aws iam create-user --user-name alice
aws iam create-login-profile --user-name alice --password 'TempP@ss1!' --password-reset-required
aws iam enable-mfa-device --user-name alice --serial-number arn:aws:iam::mfa/alice \
  --authentication-code1 123456 --authentication-code2 789012
```

### MFA enforcement policy
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyAllExceptMFASetup",
    "Effect": "Deny",
    "NotAction": ["iam:CreateVirtualMFADevice","iam:EnableMFADevice","iam:GetUser","iam:ListMFADevices","iam:ResyncMFADevice","sts:GetSessionToken"],
    "Resource": "*",
    "Condition": {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}
  }]
}
```

### Access key rotation
```bash
aws iam list-access-keys --user-name deploy-bot
aws iam create-access-key --user-name deploy-bot
aws iam update-access-key --user-name deploy-bot --access-key-id AKIA... --status Inactive
aws iam delete-access-key --user-name deploy-bot --access-key-id AKIA...
```

---

## ROLES ΓÇö IAM Role Patterns

### EC2 instance profile
```bash
aws iam create-role --role-name EC2-App-Role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name EC2-App-Role --policy-arn arn:aws:iam::policy/S3ReadOnly
aws iam create-instance-profile --instance-profile-name EC2-App-Profile
aws iam add-role-to-instance-profile --instance-profile-name EC2-App-Profile --role-name EC2-App-Role
```

### Lambda execution role trust policy
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}
```
Attach `AWSLambdaBasicExecutionRole` + your custom policies.

### ECS task role vs execution role
| Role | Purpose | Trust Principal |
|------|---------|-----------------|
| Task role | App-level AWS calls (S3, DynamoDB) | `ecs-tasks.amazonaws.com` |
| Execution role | Pull images, write logs | `ecs-tasks.amazonaws.com` |

### Cross-account assume-role
```bash
# Account B: create role trusting Account A
aws iam create-role --role-name CrossAccountReader \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::111111111111:root"},"Action":"sts:AssumeRole"}]}'
# Account A: assume it
aws sts assume-role --role-arn arn:aws:iam::222222222222:role/CrossAccountReader --role-session-name session1
```

---

## POLICIES ΓÇö IAM Policy Design

### Managed vs inline
| Type | When to use | Limit |
|------|-------------|-------|
| AWS managed | Standard permissions (ReadOnly, PowerUser) | N/A |
| Customer managed | Shared across roles/users | 5120 chars |
| Inline | One-off, tightly scoped to a single entity | 2048 chars |

### Condition keys
```json
"Condition": {
  "StringEquals": {"aws:RequestedRegion": "us-east-1"},
  "IpAddress": {"aws:SourceIp": "203.0.113.0/24"},
  "Bool": {"aws:SecureTransport": "true"}
}
```

### Policy simulator
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/alice \
  --action-names s3:GetObject s3:PutObject \
  --resource-arns arn:aws:s3:::my-bucket/*
```

### Never-use patterns
- `"Resource": "*"` on `iam:*`, `s3:DeleteBucket`, `ec2:TerminateInstances`
- Inline policies for roles shared across services
- Long-lived access keys without rotation
- `AdministratorAccess` on anything except break-glass roles

---

## STS ΓÇö Temporary Credentials

```bash
CREDS=$(aws sts assume-role --role-arn arn:aws:iam::123456789012:role/DeployRole \
  --role-session-name deploy --duration-seconds 3600 \
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text)
export AWS_ACCESS_KEY_ID=$(echo $CREDS | cut -f1)
export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | cut -f2)
export AWS_SESSION_TOKEN=$(echo $CREDS | cut -f3)
```

---

## SECRETS ΓÇö Secrets Manager & SSM Parameter Store

| Feature | Secrets Manager | SSM Parameter Store |
|---------|----------------|-------------------|
| Auto-rotation | Yes (Lambda) | No |
| Cost | $0.40/secret/month | Free (standard) |
| Use for | DB passwords, API keys | Config values, feature flags |

```bash
# Secrets Manager
aws secretsmanager create-secret --name prod/db/password --secret-string 'MyP@ss!'
aws secretsmanager get-secret-value --secret-id prod/db/password --query SecretString --output text

# SSM Parameter Store
aws ssm put-parameter --name /app/api-url --value 'https://api.example.com' --type SecureString
aws ssm get-parameter --name /app/api-url --with-decryption --query Parameter.Value --output text
```

---

## AUDIT ΓÇö Security Monitoring

```bash
# CloudTrail
aws cloudtrail create-trail --name org-trail --s3-bucket-name audit-logs --is-multi-region-trail
# IAM Access Analyzer
aws accessanalyzer create-analyzer --analyzer-name org-analyzer --type ACCOUNT
# GuardDuty
aws guardduty create-detector --enable
```

---

## Copy-Paste Policy Templates

### 1. S3 Read-Only
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject","s3:ListBucket"],"Resource":["arn:aws:s3:::BUCKET","arn:aws:s3:::BUCKET/*"]}]}
```

### 2. Lambda Invoke
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"lambda:InvokeFunction","Resource":"arn:aws:lambda:REGION:ACCOUNT:function:FUNC"}]}
```

### 3. EC2 Describe
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ec2:Describe*"],"Resource":"*"}]}
```

### 4. RDS Connect (IAM auth)
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:REGION:ACCOUNT:dbuser:RESOURCE_ID/USER"}]}
```

### 5. Read-Only Audit
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["iam:Get*","iam:List*","s3:GetBucket*","s3:ListBucket","ec2:Describe*","rds:Describe*","lambda:List*","cloudtrail:LookupEvents"],"Resource":"*"}]}
```
