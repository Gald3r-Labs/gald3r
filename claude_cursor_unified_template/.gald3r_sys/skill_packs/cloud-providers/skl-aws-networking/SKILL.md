---
name: skl-aws-networking
description: AWS networking ΓÇö VPC architecture, Route 53 DNS, CloudFront CDN, ALB/NLB load balancers, VPN, VPC peering. 3-tier VPC template included.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# AWS Networking (VPC / Route53 / CloudFront / ALB)

Core networking services for production-grade AWS architectures.

## Prerequisites

- AWS CLI configured
- IAM permissions (see `skl-aws-iam`)

## 3-Tier VPC Template

Standard production VPC with public, private, and data subnets across 2 AZs.

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc}]' \
  --query "Vpc.VpcId" --output text)

# Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query "InternetGateway.InternetGatewayId" --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# Subnets (public x2, private x2, data x2)
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-1a}]'
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-1b}]'
# Repeat for private (10.0.10.0/24, 10.0.11.0/24) and data (10.0.20.0/24, 10.0.21.0/24)
```

**CIDR allocation:**
| Tier | AZ-a | AZ-b | Access |
|------|------|------|--------|
| Public | 10.0.1.0/24 | 10.0.2.0/24 | IGW ΓåÆ internet |
| Private | 10.0.10.0/24 | 10.0.11.0/24 | NAT ΓåÆ internet |
| Data | 10.0.20.0/24 | 10.0.21.0/24 | No internet |

## Operation: VPC

VPC operations after initial setup.

```bash
# List VPCs
aws ec2 describe-vpcs --query "Vpcs[].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table

# Create NAT Gateway (for private subnet internet access)
EIP=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
aws ec2 create-nat-gateway --subnet-id subnet-public-1a --allocation-id $EIP

# Security Group
SG_ID=$(aws ec2 create-security-group --group-name web-sg \
  --description "Web tier" --vpc-id $VPC_ID --query "GroupId" --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
```

## Operation: ROUTE53

DNS management for domains and internal routing.

```bash
# List hosted zones
aws route53 list-hosted-zones --query "HostedZones[].[Name,Id,Config.PrivateZone]" --output table

# Create public zone
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference $(date +%s)

# Create A record
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "1.2.3.4"}]
      }
    }]
  }'

# Alias record (points to AWS resource, no TTL)
# Use for: ALB, CloudFront, S3 website, API Gateway
# "AliasTarget": {"HostedZoneId": "ALB_ZONE_ID", "DNSName": "alb.amazonaws.com", "EvaluateTargetHealth": true}

# Health check
aws route53 create-health-check \
  --caller-reference $(date +%s) \
  --health-check-config "Protocol=HTTPS,FullyQualifiedDomainName=app.example.com,Port=443,Type=HTTPS"
```

## Operation: CLOUDFRONT

CDN for static assets, APIs, and origin protection.

```bash
# Create distribution (from S3)
aws cloudfront create-distribution \
  --distribution-config file://cf-config.json

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id EXXXXXXXXX \
  --paths "/*"

# List distributions
aws cloudfront list-distributions \
  --query "DistributionList.Items[].[Id,DomainName,Status]" --output table
```

**WAF attachment:**
```bash
WEBACL_ARN=$(aws wafv2 create-web-acl \
  --name my-waf --scope CLOUDFRONT --region us-east-1 \
  --default-action Allow={} \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=myWAF \
  --rules file://waf-rules.json \
  --query "Summary.ARN" --output text)
# Attach in CloudFront distribution config: "WebACLId": "<WEBACL_ARN>"
```

**OAC ΓÇö Origin Access Control (replaces OAI for S3 origins):**
```bash
OAC_ID=$(aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name":"my-oac","OriginAccessControlOriginType":"s3",
    "SigningBehavior":"always","SigningProtocol":"sigv4"
  }' --query "OriginAccessControl.Id" --output text)

# S3 bucket policy ΓÇö allow only CloudFront
aws s3api put-bucket-policy --bucket my-bucket --policy "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"cloudfront.amazonaws.com\"},
    \"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::my-bucket/*\",
    \"Condition\":{\"StringEquals\":{\"AWS:SourceArn\":\"arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID\"}}}]}"
```

**Custom error pages (in distribution config):**
```json
"CustomErrorResponses": {"Quantity":2,"Items":[
  {"ErrorCode":404,"ResponsePagePath":"/errors/404.html","ResponseCode":"404","ErrorCachingMinTTL":300},
  {"ErrorCode":403,"ResponsePagePath":"/errors/403.html","ResponseCode":"403","ErrorCachingMinTTL":300}
]}

## Operation: ALB

Application Load Balancer for HTTP/HTTPS routing.

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name prod-alb --type application \
  --subnets subnet-pub-1a subnet-pub-1b \
  --security-groups $SG_ID \
  --query "LoadBalancers[0].LoadBalancerArn" --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name web-targets --protocol HTTP --port 80 \
  --vpc-id $VPC_ID --target-type ip \
  --health-check-path /health \
  --query "TargetGroups[0].TargetGroupArn" --output text)

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS --port 443 \
  --certificates CertificateArn=$ACM_ARN \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

**Sticky sessions (session affinity):**
```bash
# Enable sticky sessions on target group
aws elbv2 modify-target-group-attributes \
  --target-group-arn $TG_ARN \
  --attributes Key=stickiness.enabled,Value=true \
               Key=stickiness.type,Value=lb_cookie \
               Key=stickiness.lb_cookie.duration_seconds,Value=86400
```

**Path-based routing (route /api/* to a different target group):**
```bash
# Create second target group for API
API_TG_ARN=$(aws elbv2 create-target-group \
  --name api-targets --protocol HTTP --port 8080 \
  --vpc-id $VPC_ID --target-type ip \
  --query "TargetGroups[0].TargetGroupArn" --output text)

# Add path-based rule to existing listener
aws elbv2 rule-create \
  --listener-arn $LISTENER_ARN \
  --priority 10 \
  --conditions '[{"Field":"path-pattern","Values":["/api/*"]}]' \
  --actions "Type=forward,TargetGroupArn=$API_TG_ARN"
```

## Operation: VPN

Site-to-site VPN for connecting on-premises networks.

```bash
# Create Customer Gateway (your on-prem router's public IP)
aws ec2 create-customer-gateway \
  --type ipsec.1 --public-ip 203.0.113.1 --bgp-asn 65000

# Create Virtual Private Gateway
VGW=$(aws ec2 create-vpn-gateway --type ipsec.1 --query "VpnGateway.VpnGatewayId" --output text)
aws ec2 attach-vpn-gateway --vpn-gateway-id $VGW --vpc-id $VPC_ID

# Create VPN connection
aws ec2 create-vpn-connection \
  --type ipsec.1 --customer-gateway-id cgw-xxx \
  --vpn-gateway-id $VGW
```

## Operation: PEERING

VPC-to-VPC private connectivity.

```bash
# Initiate peering (same or cross-account)
PEER_ID=$(aws ec2 create-vpc-peering-connection \
  --vpc-id vpc-aaaa --peer-vpc-id vpc-bbbb \
  --query "VpcPeeringConnection.VpcPeeringConnectionId" --output text)

# Accept (in peer VPC's account/region)
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $PEER_ID

# Add route to each VPC's route table
aws ec2 create-route --route-table-id rtb-xxx \
  --destination-cidr-block 10.1.0.0/16 \
  --vpc-peering-connection-id $PEER_ID
```

**AWS PrivateLink & VPC Interface Endpoints (private access to AWS services):**
```bash
# Create Interface endpoint for S3 (keeps traffic off internet)
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.s3 \
  --subnet-ids subnet-private-1a subnet-private-1b \
  --security-group-ids $SG_ID \
  --private-dns-enabled

# Create Interface endpoint for DynamoDB
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --subnet-ids subnet-private-1a \
  --security-group-ids $SG_ID

# Gateway endpoint for S3/DynamoDB (free, recommended over Interface for these)
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Gateway \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-private-1a rtb-private-1b

# Create PrivateLink to expose your own service to other VPCs
# 1. Create NLB pointing to your service
# 2. Create VPC Endpoint Service from the NLB
aws ec2 create-vpc-endpoint-service-configuration \
  --network-load-balancer-arns $NLB_ARN \
  --acceptance-required
# 3. Consumers create Interface endpoints using your service name
```

| Endpoint type | Services | Cost | DNS |
|--------------|----------|------|-----|
| Gateway | S3, DynamoDB | Free | Route table |
| Interface (PrivateLink) | 100+ AWS services | ~$7/mo/AZ | Private DNS |
