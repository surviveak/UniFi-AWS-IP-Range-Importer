# Multi-Group Setup Guide

This guide explains how to configure the Lambda to update multiple UniFi address groups, one per AWS service.

## Why Use Multiple Groups?

**Benefits:**
- Better firewall performance (smaller groups)
- More granular firewall rules
- Easier to manage and troubleshoot
- Can enable/disable specific services independently

**Example:**
Instead of one group with 800+ IPs, you have:
- `AWS-EC2`: 450 IPs
- `AWS-S3`: 200 IPs
- `AWS-CLOUDFRONT`: 150 IPs

## Setup Steps

### 1. Create Address Groups in UniFi

You can create groups manually or use the helper script.

#### Option A: Use the Helper Script (Recommended)

Update `create_address_groups.py` with your credentials:

```python
CONSOLE_ID = "your-console-id-here"
SITE_NAME = "your-site-name-here"
API_KEY = "your-api-key-here"
```

Run the script:

```bash
python create_address_groups.py
```

The script will:
1. Check for existing groups
2. Create new groups for each service (AWS-EC2, AWS-S3, etc.)
3. Output the configuration string for Lambda

#### Option B: Create Manually via UniFi UI

For each AWS service you want to track:

1. Go to **Settings** → **Security** → **Traffic & Security**
2. Click **Firewall** tab → **Groups** section
3. Click **Create New Group**
4. Name: `AWS-EC2` (or AWS-S3, AWS-CLOUDFRONT, etc.)
5. Type: **Address/Subnet**
6. Add placeholder: `0.0.0.0/32`
7. Save and note the Group ID

Repeat for each service.

### 2. Get Group IDs

List all groups to get their IDs:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://api.ui.com/v1/connector/consoles/CONSOLE_ID/proxy/network/api/s/SITE_NAME/rest/firewallgroup"
```

Note the `_id` for each AWS group.

### 3. Configure Lambda

#### Format

The `UNIFI_GROUP_MAPPINGS` environment variable uses this format:

```
SERVICE1:GROUP_ID1,SERVICE2:GROUP_ID2,SERVICE3:GROUP_ID3
```

#### Example

```
EC2:698f75a2cc1fbbf442a1b923,S3:698f75a2cc1fbbf442a1b924,CLOUDFRONT:698f75a2cc1fbbf442a1b925
```

#### Update Lambda Environment Variables

**Via AWS CLI:**

```bash
aws lambda update-function-configuration \
  --function-name UniFi-AWS-CIDR-Importer \
  --environment "Variables={
    UNIFI_CONSOLE_ID=your-console-id,
    UNIFI_SITE_NAME=your-site-name,
    UNIFI_API_KEY=your-api-key,
    UNIFI_GROUP_MAPPINGS='EC2:id1,S3:id2,CLOUDFRONT:id3',
    AWS_SERVICE_FILTER='EC2,S3,CLOUDFRONT',
    AWS_REGION_FILTER='us-east-1'
  }"
```

**Via SAM deployment:**

Update `samconfig.toml`:

```toml
parameter_overrides = "UniFiConsoleId=\"...\" UniFiSiteName=\"...\" UniFiGroupMappings=\"EC2:id1,S3:id2\" AwsServiceFilter=\"EC2,S3\" AwsRegionFilter=\"us-east-1\""
```

Then redeploy:

```bash
sam build && sam deploy
```

**Via AWS Console:**

1. Go to Lambda function
2. Configuration → Environment variables
3. Remove `UNIFI_GROUP_ID` (if present)
4. Add `UNIFI_GROUP_MAPPINGS` with your service:id mappings
5. Update `AWS_SERVICE_FILTER` to match the services in your mappings

### 4. Test

Invoke the Lambda manually:

```bash
aws lambda invoke --function-name UniFi-AWS-CIDR-Importer response.json
cat response.json
```

Check that each group was updated:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Successfully updated UniFi address groups",
    "total_ips": 800,
    "groups_updated": 3,
    "results": [
      {"service": "EC2", "group_id": "...", "ip_count": 450},
      {"service": "S3", "group_id": "...", "ip_count": 200},
      {"service": "CLOUDFRONT", "group_id": "...", "ip_count": 150}
    ]
  }
}
```

## Configuration Examples

### Example 1: EC2, S3, and CloudFront

```bash
# Environment variables
UNIFI_GROUP_MAPPINGS="EC2:698f75a2cc1fbbf442a1b923,S3:698f75a2cc1fbbf442a1b924,CLOUDFRONT:698f75a2cc1fbbf442a1b925"
AWS_SERVICE_FILTER="EC2,S3,CLOUDFRONT"
AWS_REGION_FILTER="us-east-1"
```

### Example 2: Route53 Services

```bash
UNIFI_GROUP_MAPPINGS="ROUTE53:id1,ROUTE53_HEALTHCHECKS:id2"
AWS_SERVICE_FILTER="ROUTE53,ROUTE53_HEALTHCHECKS"
AWS_REGION_FILTER=""  # All regions
```

### Example 3: All Major Services

```bash
UNIFI_GROUP_MAPPINGS="EC2:id1,S3:id2,CLOUDFRONT:id3,DYNAMODB:id4,API_GATEWAY:id5"
AWS_SERVICE_FILTER="EC2,S3,CLOUDFRONT,DYNAMODB,API_GATEWAY"
AWS_REGION_FILTER="us-east-1,us-west-2"
```

## Important Notes

### Service Names Must Match

The services in `AWS_SERVICE_FILTER` must match the service names in `UNIFI_GROUP_MAPPINGS`.

**Correct:**
```
AWS_SERVICE_FILTER="EC2,S3"
UNIFI_GROUP_MAPPINGS="EC2:id1,S3:id2"
```

**Incorrect:**
```
AWS_SERVICE_FILTER="EC2,S3,CLOUDFRONT"
UNIFI_GROUP_MAPPINGS="EC2:id1,S3:id2"
# CloudFront IPs will be fetched but not updated (no mapping)
```

### Legacy Single Group Mode

The Lambda still supports the old single-group mode for backward compatibility:

```bash
# Old way - still works
UNIFI_GROUP_ID="698f75a2cc1fbbf442a1b923"
AWS_SERVICE_FILTER="EC2,S3"
# All IPs go into one group
```

If both `UNIFI_GROUP_MAPPINGS` and `UNIFI_GROUP_ID` are set, `UNIFI_GROUP_MAPPINGS` takes precedence.

## Common AWS Service Names

- `AMAZON` - All AWS services (not recommended for multi-group)
- `EC2` - EC2 instances
- `S3` - S3 storage
- `CLOUDFRONT` - CloudFront CDN
- `ROUTE53` - Route53 DNS
- `ROUTE53_HEALTHCHECKS` - Route53 health checks
- `DYNAMODB` - DynamoDB database
- `API_GATEWAY` - API Gateway
- `LAMBDA` - Lambda functions
- `ECS` - ECS containers
- `RDS` - RDS databases

See the full list at: https://ip-ranges.amazonaws.com/ip-ranges.json

## Troubleshooting

### Service not updating

Check that:
1. Service name in `UNIFI_GROUP_MAPPINGS` matches `AWS_SERVICE_FILTER`
2. Group ID is correct
3. Service has IPs in your filtered region

### "No IP ranges found for service"

This warning means the service has no IPs matching your region filter. Either:
- Remove the region filter for that service
- Remove the service from your configuration
- Check the service name is correct

### Performance issues

If you have many services with many IPs:
- Use region filters to reduce IP counts
- Consider updating groups on a schedule instead of every AWS update
- Monitor UniFi device CPU/memory usage
