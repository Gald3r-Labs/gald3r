---
name: skl-aws-storage
description: AWS storage ΓÇö S3 object storage, RDS relational databases, DynamoDB NoSQL, EFS/EBS block/file storage, Glacier archival. Bucket policy templates included.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# AWS Storage (S3 / RDS / DynamoDB / EFS)

Core AWS storage services for application data, files, and databases.

## Prerequisites

- AWS CLI configured (`aws configure`)
- IAM permissions (see `skl-aws-iam` for storage policy templates)

## Operation: S3

Object storage ΓÇö files, backups, static sites, data lake.

```bash
# Create bucket (us-east-1 has no LocationConstraint)
aws s3api create-bucket --bucket my-bucket --region us-east-1
aws s3api create-bucket --bucket my-bucket --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1

# Upload
aws s3 cp local-file.txt s3://my-bucket/path/file.txt
aws s3 sync ./dist s3://my-bucket/static/ --delete

# Download
aws s3 cp s3://my-bucket/path/file.txt ./
aws s3 sync s3://my-bucket/static/ ./local-copy/

# List
aws s3 ls s3://my-bucket/path/ --recursive --human-readable

# Delete
aws s3 rm s3://my-bucket/path/file.txt
aws s3 rm s3://my-bucket/ --recursive

# Make bucket public (static website)
aws s3api put-bucket-website --bucket my-bucket \
  --website-configuration '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"404.html"}}'
aws s3api delete-public-access-block --bucket my-bucket
```

**Presigned URL generation (temporary access):**
```bash
# Generate presigned GET URL (valid 1 hour)
aws s3 presign s3://my-bucket/path/file.txt --expires-in 3600

# Presigned PUT URL (for client-side uploads)
aws s3 presign s3://my-bucket/uploads/new-file.txt --expires-in 3600 --region us-east-1
```
```python
import boto3
s3 = boto3.client("s3")
# GET (download)
url = s3.generate_presigned_url("get_object",
    Params={"Bucket": "my-bucket", "Key": "path/file.txt"}, ExpiresIn=3600)
# PUT (upload)
url = s3.generate_presigned_url("put_object",
    Params={"Bucket": "my-bucket", "Key": "uploads/new.txt", "ContentType": "text/plain"},
    ExpiresIn=900)
```

**S3 Transfer Acceleration (faster uploads over long distances):**
```bash
# Enable Transfer Acceleration on bucket
aws s3api put-bucket-accelerate-configuration \
  --bucket my-bucket --accelerate-configuration Status=Enabled

# Use accelerated endpoint
aws s3 cp large-file.tar.gz s3://my-bucket/ \
  --endpoint-url https://my-bucket.s3-accelerate.amazonaws.com
# ~50-500% faster from distant regions (Asia ΓåÆ US-East, etc.)
```

**S3 bucket policy templates:**

```json
// Read-only public (static site)
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
```

```json
// Allow specific IAM role only
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::ACCOUNT:role/my-role"},
    "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"],
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
```

## Operation: RDS

Managed relational databases (PostgreSQL, MySQL, Aurora).

```bash
# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier my-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.2 \
  --master-username admin \
  --master-user-password $(openssl rand -base64 20) \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxx \
  --no-publicly-accessible

# List instances
aws rds describe-db-instances --query "DBInstances[].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address]" --output table

# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier my-postgres \
  --db-snapshot-identifier my-postgres-snap-$(date +%Y%m%d)

# Aurora Serverless v2 (scales to 0)
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora \
  --engine aurora-postgresql \
  --engine-version 16.1 \
  --serverless-v2-scaling-configuration MinCapacity=0,MaxCapacity=4 \
  --master-username admin --master-user-password YOUR_PASSWORD
```

**Read replicas (scale read traffic):**
```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier my-postgres-replica \
  --source-db-instance-identifier my-postgres \
  --db-instance-class db.t3.small \
  --availability-zone us-east-1b

# Promote replica to standalone (for blue/green migrations)
aws rds promote-read-replica --db-instance-identifier my-postgres-replica

# Point read traffic to replica endpoint
# Replica endpoint: my-postgres-replica.xxxx.us-east-1.rds.amazonaws.com
```

**RDS Proxy (connection pooling for serverless):**
```bash
# Create RDS Proxy (requires IAM role + Secrets Manager secret)
aws rds create-db-proxy \
  --db-proxy-name my-rds-proxy \
  --engine-family POSTGRESQL \
  --auth '[{"AuthScheme":"SECRETS","SecretArn":"arn:aws:secretsmanager:...","IAMAuth":"DISABLED"}]' \
  --role-arn arn:aws:iam::ACCOUNT:role/rds-proxy-role \
  --vpc-subnet-ids subnet-xxx subnet-yyy \
  --vpc-security-group-ids sg-xxx

# Register target (point proxy at RDS instance)
aws rds register-db-proxy-targets \
  --db-proxy-name my-rds-proxy \
  --db-instance-identifiers my-postgres
# Use proxy endpoint instead of direct DB endpoint in Lambda/ECS configs
```

## Operation: DYNAMODB

Serverless NoSQL ΓÇö single-digit millisecond latency, auto-scaling.

```bash
# Create table
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Put item
aws dynamodb put-item --table-name Users \
  --item '{"userId":{"S":"u001"},"name":{"S":"Alice"},"email":{"S":"alice@example.com"}}'

# Get item
aws dynamodb get-item --table-name Users \
  --key '{"userId":{"S":"u001"}}'

# Query
aws dynamodb query --table-name Users \
  --key-condition-expression "userId = :id" \
  --expression-attribute-values '{":id":{"S":"u001"}}'

# DynamoDB Local (development)
docker run -p 8000:8000 amazon/dynamodb-local
AWS_DEFAULT_REGION=us-east-1 aws dynamodb list-tables --endpoint-url http://localhost:8000
```

**GSI/LSI design patterns:**
```bash
# Global Secondary Index (different partition key ΓÇö cross-partition queries)
aws dynamodb create-table \
  --table-name Orders \
  --attribute-definitions \
    AttributeName=orderId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=createdAt,AttributeType=S \
  --key-schema AttributeName=orderId,KeyType=HASH \
  --global-secondary-indexes '[{
    "IndexName": "UserOrders",
    "KeySchema": [{"AttributeName":"userId","KeyType":"HASH"},{"AttributeName":"createdAt","KeyType":"RANGE"}],
    "Projection": {"ProjectionType":"ALL"},
    "BillingMode": "PAY_PER_REQUEST"
  }]' \
  --billing-mode PAY_PER_REQUEST

# Query GSI
aws dynamodb query --table-name Orders \
  --index-name UserOrders \
  --key-condition-expression "userId = :uid AND createdAt > :date" \
  --expression-attribute-values '{":uid":{"S":"u001"},":date":{"S":"2026-01-01"}}'
```

**DynamoDB Streams (event-driven triggers):**
```bash
# Enable stream on table
aws dynamodb update-table --table-name Users \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# Get stream ARN (use as Lambda trigger)
aws dynamodb describe-table --table-name Users \
  --query "Table.LatestStreamArn" --output text
```

**TTL (auto-expire items):**
```bash
# Enable TTL on a timestamp attribute
aws dynamodb update-time-to-live --table-name Sessions \
  --time-to-live-specification "Enabled=true,AttributeName=expiresAt"
# Set expiresAt = Unix timestamp (epoch seconds) on each item
```

**On-Demand vs Provisioned capacity:**
| Mode | When to use | Cost model |
|------|-------------|-----------|
| On-Demand (`PAY_PER_REQUEST`) | Unpredictable traffic, new apps | Per request |
| Provisioned + Auto Scaling | Predictable steady load | Per RCU/WCU-hour |
| Reserved Capacity | Known sustained throughput | 1/3yr upfront discount |

## Operation: EFS

Elastic File System ΓÇö shared POSIX file storage mountable by multiple EC2/ECS instances.

```bash
# Create EFS
aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --tags Key=Name,Value=my-efs

# Create mount target (one per AZ)
aws efs create-mount-target \
  --file-system-id fs-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --security-groups sg-xxxxxxxx

# Mount (on EC2)
sudo mount -t efs -o tls fs-xxxxxxxx:/ /mnt/efs

# /etc/fstab entry
echo "fs-xxxxxxxx:/ /mnt/efs efs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
```

## Operation: BACKUP

Cross-service backup management.

```bash
# Create backup plan
aws backup create-backup-plan --backup-plan '{
  "BackupPlanName": "DailyBackup",
  "Rules": [{
    "RuleName": "Daily",
    "TargetBackupVaultName": "Default",
    "ScheduleExpression": "cron(0 2 * * ? *)",
    "Lifecycle": {"DeleteAfterDays": 30}
  }]
}'

# On-demand backup
aws backup start-backup-job \
  --backup-vault-name Default \
  --resource-arn arn:aws:rds:::db:my-postgres \
  --iam-role-arn arn:aws:iam::ACCOUNT:role/AWSBackupDefaultServiceRole
```
