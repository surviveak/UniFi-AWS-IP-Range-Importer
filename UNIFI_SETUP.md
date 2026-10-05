# UniFi Setup Guide

## Prerequisites

You need a UniFi Cloud account with API access enabled.

## Step 1: Get Your API Key

1. Log in to [UniFi Cloud Console](https://unifi.ui.com/)
2. Go to **Settings** → **API**
3. Click **Create New API Key**
4. Give it a descriptive name (e.g., "AWS CIDR Importer")
5. Set appropriate permissions (needs write access to firewall rules)
6. Copy and save the API key securely

## Step 2: Find Your Console ID

Your Console ID is in the URL when you're logged into your UniFi console:
```
https://unifi.ui.com/consoles/{CONSOLE_ID}/...
```

Example: `7483C276F471000000000421848500000000044E4851000000005D354A60:1555269794`

## Step 3: Find Your Site Name (Internal Reference)

The site name is the short internal reference, not the UUID. You can find it via API:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://api.ui.com/v1/connector/consoles/{CONSOLE_ID}/proxy/network/integration/v1/sites"
```

Look for the `internalReference` field (e.g., "3zhjetkb", "default").

## Step 4: Create or Find an Address Group

### Via UniFi UI:
1. Go to **Settings** → **Security** → **Traffic & Security**
2. Click **Firewall** tab
3. Scroll to **Groups** section
4. Click **Create New Group**
5. Name it (e.g., "AWS-IP-Ranges")
6. Type: **Address/Subnet**
7. Add a placeholder address initially (e.g., "0.0.0.0/32")
8. Save

### Via API (List existing groups):
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://api.ui.com/v1/connector/consoles/{CONSOLE_ID}/proxy/network/api/s/{SITE_NAME}/rest/firewallgroup"
```

Look for `group_type: "address-group"` and note the `_id` field.

## Step 5: Get the Address Group ID

From the API response in Step 4, find your group and copy its `_id` field.

Example response:
```json
{
  "meta": {"rc": "ok"},
  "data": [{
    "_id": "698f75a2cc1fbbf442a1b923",
    "name": "AWS-IP-Ranges",
    "group_type": "address-group",
    "group_members": ["0.0.0.0/32"]
  }]
}
```

## Step 6: (Optional) Create Firewall Rules

Once the address group is populated with AWS IPs, you can use it in firewall rules:

1. Go to **Settings** → **Security** → **Firewall & Security**
2. Click **Traffic Rules** tab
3. Create rules that reference your "AWS-IP-Ranges" address group
4. Example: Allow traffic from AWS IP ranges to specific services

## Summary

You'll need these values for your Lambda environment variables:

- **UNIFI_CONSOLE_ID**: Your console ID (found in the URL when logged into UniFi)
- **UNIFI_SITE_NAME**: Your site's `internalReference` (e.g., "default" or custom name)
- **UNIFI_GROUP_ID**: Your address group's `_id` field
- **UNIFI_API_KEY**: Your API key from Step 1

## Important Notes

- The Lambda will **replace** all addresses in the group each time it runs
- Changing filters will immediately remove IPs that no longer match
- AWS publishes thousands of IP ranges - ensure your UniFi device can handle the list size
- Consider filtering by specific AWS services or regions to reduce the list size
- Test with a small subset first using the `AWS_SERVICE_FILTER` or `AWS_REGION_FILTER` environment variables

### Behavior on Filter Changes

**Adding a service/region:**
- New IPs will be added to the address group
- Existing IPs remain (if they still match the filter)

**Removing a service/region:**
- IPs for that service/region will be removed immediately
- This could break firewall rules that depend on those IPs
- Review your firewall rules before changing filters

**Example:**
```
Initial: AWS_SERVICE_FILTER="EC2,S3" → 500 IPs in group
Change to: AWS_SERVICE_FILTER="EC2" → Only EC2 IPs remain, S3 IPs removed
```

## Troubleshooting

### API Key Permissions
If you get 403 errors, ensure your API key has sufficient permissions for firewall management.

### Rate Limiting
UniFi API may have rate limits. The Lambda is designed to run infrequently (only when AWS updates IP ranges).

### Large Address Lists
If you have too many IPs, consider:
- Filtering by specific AWS services (e.g., "CLOUDFRONT", "S3", "EC2")
- Filtering by specific regions (e.g., "us-east-1")
- Creating multiple address groups for different services
