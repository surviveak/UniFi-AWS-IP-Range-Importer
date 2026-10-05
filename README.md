# UniFi AWS CIDR Importer

AWS Lambda function that automatically updates UniFi firewall address groups when AWS publishes new IP ranges.

## Overview

This Lambda function:
- Subscribes to AWS SNS notifications for IP range updates
- Fetches the latest AWS IP ranges from the official JSON endpoint
- Filters by AWS service and region (configurable)
- Updates UniFi firewall address groups via the UniFi Cloud API
- Supports multiple address groups (one per service) for better performance
- Supports IPv4 addresses only (IPv6 can be enabled if needed)

## Features

- **Multi-Group Support**: Create separate address groups for each AWS service (EC2, S3, CloudFront, etc.)
- **Automatic Updates**: Triggered by AWS SNS when IP ranges change
- **Flexible Filtering**: Filter by AWS services and regions
- **Legacy Mode**: Backward compatible with single address group
- **Performance Optimized**: Smaller groups improve firewall performance

## Prerequisites

- AWS Account with Lambda and SNS access
- UniFi Cloud account with API access
- UniFi device (Dream Machine, Cloud Gateway, etc.)
- AWS SAM CLI installed (for deployment)
- Python 3.11+ (for local testing)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/unifi-aws-cidr-importer.git
cd unifi-aws-cidr-importer
```

### 2. Configure UniFi

Follow the [UniFi Setup Guide](UNIFI_SETUP.md) to:
- Generate a UniFi API key
- Find your Console ID and Site Name

### 3. Create Address Groups

**Option A: Use the helper script (Recommended)**

```bash
# Update create_address_groups.py with your credentials
python create_address_groups.py
```

This will create groups like `AWS-EC2`, `AWS-S3`, `AWS-CLOUDFRONT`, etc., and output the configuration string.

**Option B: Manual setup**

See [Multi-Group Setup Guide](MULTI_GROUP_SETUP.md) for detailed instructions.

### 4. Configure Deployment

Copy the example config:

```bash
cp samconfig.toml.example samconfig.toml
```

Edit `samconfig.toml` and update with your values from the helper script output.

### 5. Deploy with SAM

```bash
sam build
sam deploy --guided
```

### 6. Test the Function

```bash
aws lambda invoke --function-name UniFi-AWS-CIDR-Importer response.json
cat response.json
```

## Configuration

### Environment Variables

**Required:**
- `UNIFI_CONSOLE_ID` - Your UniFi console ID
- `UNIFI_SITE_NAME` - Your UniFi site internal reference
- `UNIFI_API_KEY` - Your UniFi API key

**Multi-Group Mode (Recommended):**
- `UNIFI_GROUP_MAPPINGS` - Service to group ID mappings (format: `SERVICE1:ID1,SERVICE2:ID2`)
- `AWS_SERVICE_FILTER` - Comma-separated AWS services matching the mappings

**Legacy Single-Group Mode:**
- `UNIFI_GROUP_ID` - Single address group ID
- `AWS_SERVICE_FILTER` - Comma-separated AWS services

**Optional:**
- `AWS_REGION_FILTER` - Comma-separated AWS regions (default: all regions)

### Example Configurations

**Multi-Group (Recommended):**
```bash
UNIFI_GROUP_MAPPINGS="EC2:id1,S3:id2,CLOUDFRONT:id3"
AWS_SERVICE_FILTER="EC2,S3,CLOUDFRONT"
AWS_REGION_FILTER="us-east-1"
```

**Single Group (Legacy):**
```bash
UNIFI_GROUP_ID="your-group-id"
AWS_SERVICE_FILTER="EC2,S3"
AWS_REGION_FILTER="us-east-1"
```

## Documentation

- [README.md](README.md) - This file
- [UNIFI_SETUP.md](UNIFI_SETUP.md) - UniFi configuration guide
- [MULTI_GROUP_SETUP.md](MULTI_GROUP_SETUP.md) - Multi-group setup guide (recommended)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment instructions

## Manual Updates

```bash
# Invoke the Lambda manually
aws lambda invoke --function-name UniFi-AWS-CIDR-Importer response.json
cat response.json
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more options.

## Architecture

```
AWS SNS Topic (AmazonIpSpaceChanged)
    ↓
AWS Lambda Function
    ↓
Fetch AWS IP Ranges → Filter by Service/Region → Update UniFi Address Groups
                                                   ↓
                                    ┌──────────────┼──────────────┐
                                    ↓              ↓              ↓
                                AWS-EC2        AWS-S3      AWS-CLOUDFRONT
```

## Files

- `lambda_function.py` - Main Lambda handler
- `template.yaml` - SAM CloudFormation template
- `samconfig.toml.example` - Example SAM configuration
- `create_address_groups.py` - Helper script to create UniFi groups
- `test_lambda.py` - Local testing script
- `requirements.txt` - Python dependencies (none - uses stdlib only)

## Security

- Never commit `samconfig.toml` with real credentials
- Store API keys securely
- Use least-privilege IAM roles
- Regularly rotate your UniFi API keys
- Review `.gitignore` to ensure sensitive files are excluded

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- AWS for publishing IP ranges at https://ip-ranges.amazonaws.com/ip-ranges.json
- UniFi for providing the Cloud API
- AWS SAM for simplifying Lambda deployments
