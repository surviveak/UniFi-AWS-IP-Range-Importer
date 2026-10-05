# Deployment Guide

## AWS Lambda Environment Variables

When you deploy to AWS Lambda, configure these environment variables:

### Required Variables
- `UNIFI_CONSOLE_ID` = `your-console-id-here`
- `UNIFI_SITE_NAME` = `your-site-name-here`
- `UNIFI_GROUP_ID` = `your-group-id-here`
- `UNIFI_API_KEY` = `your-api-key-here`

### Optional Filter Variables

**AWS_SERVICE_FILTER** (default: "AMAZON")
- Single service: `EC2`
- Multiple services: `CLOUDFRONT,S3,EC2`
- All AWS services: `AMAZON`
- Common services: `CLOUDFRONT`, `S3`, `EC2`, `ROUTE53`, `DYNAMODB`, `API_GATEWAY`

**AWS_REGION_FILTER** (default: all regions)
- Single region: `us-east-1`
- Multiple regions: `us-east-1,us-west-2,eu-west-1`
- Leave empty for all regions

## Deployment Steps

### 1. Package the Lambda

```bash
# Create deployment package
zip lambda_deployment.zip lambda_function.py
```

### 2. Create Lambda Function in AWS Console

1. Go to AWS Lambda Console
2. Click **Create function**
3. Choose **Author from scratch**
4. Function name: `UniFi-AWS-CIDR-Importer`
5. Runtime: **Python 3.12** (or 3.9+)
6. Click **Create function**

### 3. Upload Code

1. In the **Code** tab, click **Upload from** → **.zip file**
2. Upload `lambda_deployment.zip`
3. Click **Save**

### 4. Configure Environment Variables

1. Go to **Configuration** → **Environment variables**
2. Click **Edit**
3. Add all required variables (see above)
4. Add optional filter variables as needed
5. Click **Save**

### 5. Configure Lambda Settings

1. Go to **Configuration** → **General configuration**
2. Set **Timeout** to `30 seconds` (fetching AWS IPs can take a few seconds)
3. Set **Memory** to `256 MB` (default is fine)

### 6. Subscribe to SNS Topic

1. Go to **Configuration** → **Triggers**
2. Click **Add trigger**
3. Select **SNS**
4. SNS topic ARN: `arn:aws:sns:us-east-1:806199016981:AmazonIpSpaceChanged`
5. Click **Add**

Note: This SNS topic is in us-east-1, so your Lambda should be in us-east-1 or you need to create a cross-region subscription.

### 7. Test the Lambda

1. Go to **Test** tab
2. Create a new test event (use default template)
3. Click **Test**
4. Check the execution results and logs

## Testing Locally Before Deployment

Update `test_lambda.py` with your desired filters:

```python
# Around line 79-80
os.environ["AWS_SERVICE_FILTER"] = "EC2"  # Change this
os.environ["AWS_REGION_FILTER"] = "us-east-1"  # Change this
```

Then run:
```bash
python test_lambda.py
```

## Monitoring

After deployment, monitor your Lambda:

1. **CloudWatch Logs**: Check `/aws/lambda/UniFi-AWS-CIDR-Importer` log group
2. **Metrics**: Monitor invocations, errors, and duration
3. **UniFi Console**: Verify the address group is being updated

## Manual Invocation

### Using AWS CLI

Trigger the Lambda manually at any time:

```bash
# Invoke the function
aws lambda invoke --function-name UniFi-AWS-CIDR-Importer response.json

# View the response
cat response.json
```

### Using AWS Console

1. Open [AWS Lambda Console](https://console.aws.amazon.com/lambda)
2. Select `UniFi-AWS-CIDR-Importer`
3. Click **Test** tab
4. Click **Test** button
5. View results in the execution log

### Using PowerShell (Windows)

```powershell
# Invoke and view logs
aws lambda invoke --function-name UniFi-AWS-CIDR-Importer --log-type Tail response.json --query 'LogResult' --output text | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }

# View response
type response.json
```

### When to Invoke Manually

- After changing environment variables (service/region filters)
- To force an immediate update
- For testing after deployment
- When troubleshooting issues

## Troubleshooting

### Lambda times out
- Increase timeout in Configuration → General configuration
- Check if you're filtering too broadly (too many IPs)

### UniFi API errors
- Verify API key is valid
- Check console ID, site name, and group ID are correct
- Ensure UniFi device is online and accessible

### Too many IP addresses
- Use `AWS_SERVICE_FILTER` to limit to specific services
- Use `AWS_REGION_FILTER` to limit to specific regions
- Example: `AWS_SERVICE_FILTER=CLOUDFRONT` and `AWS_REGION_FILTER=us-east-1`

## Example Configurations

### CloudFront only (for CDN)
```
AWS_SERVICE_FILTER=CLOUDFRONT
AWS_REGION_FILTER=  (leave empty)
```

### EC2 in US regions only
```
AWS_SERVICE_FILTER=EC2
AWS_REGION_FILTER=us-east-1,us-east-2,us-west-1,us-west-2
```

### Multiple services in one region
```
AWS_SERVICE_FILTER=EC2,S3,DYNAMODB
AWS_REGION_FILTER=us-east-1
```
