"""Helper script to create multiple UniFi address groups for different AWS services."""
import json
import urllib.request
import urllib.error

# Configuration - Update these with your actual values
CONSOLE_ID = "your-console-id-here"
SITE_NAME = "your-site-name-here"
API_KEY = "your-api-key-here"

# Services to create groups for
SERVICES = [
    "EC2",
    "S3",
    "CLOUDFRONT",
    "ROUTE53",
    "ROUTE53_HEALTHCHECKS",
    "DYNAMODB",
    "API_GATEWAY"
]


def create_address_group(console_id: str, site_name: str, api_key: str, group_name: str):
    """Create a new UniFi address group."""
    url = f"https://api.ui.com/v1/connector/consoles/{console_id}/proxy/network/api/s/{site_name}/rest/firewallgroup"
    
    payload = {
        "name": group_name,
        "group_type": "address-group",
        "group_members": []  # Empty - will be populated by Lambda
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error creating group {group_name}: {e.code} - {error_body}")
        return None


def list_address_groups(console_id: str, site_name: str, api_key: str):
    """List all existing address groups."""
    url = f"https://api.ui.com/v1/connector/consoles/{console_id}/proxy/network/api/s/{site_name}/rest/firewallgroup"
    
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            return result.get("data", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error listing groups: {e.code} - {error_body}")
        return []


def main():
    print("=" * 60)
    print("UniFi Address Group Creator for AWS Services")
    print("=" * 60)
    print()
    
    # List existing groups
    print("Fetching existing address groups...")
    existing_groups = list_address_groups(CONSOLE_ID, SITE_NAME, API_KEY)
    existing_names = {g["name"]: g["_id"] for g in existing_groups if g.get("group_type") == "address-group"}
    
    print(f"Found {len(existing_names)} existing address groups")
    print()
    
    # Create groups for each service
    group_mappings = []
    
    for service in SERVICES:
        group_name = f"AWS-{service}"
        
        if group_name in existing_names:
            group_id = existing_names[group_name]
            print(f"✓ {group_name} already exists (ID: {group_id})")
            group_mappings.append(f"{service}:{group_id}")
        else:
            print(f"Creating {group_name}...")
            result = create_address_group(CONSOLE_ID, SITE_NAME, API_KEY, group_name)
            
            if result and result.get("meta", {}).get("rc") == "ok":
                data = result.get("data", [])
                if data:
                    group_id = data[0]["_id"]
                    print(f"✓ Created {group_name} (ID: {group_id})")
                    group_mappings.append(f"{service}:{group_id}")
            else:
                print(f"✗ Failed to create {group_name}")
    
    print()
    print("=" * 60)
    print("Configuration for Lambda")
    print("=" * 60)
    print()
    print("Add this to your Lambda environment variables:")
    print()
    print(f"UNIFI_GROUP_MAPPINGS={','.join(group_mappings)}")
    print()
    print("Or use in samconfig.toml:")
    print()
    print(f'UniFiGroupMappings="{",".join(group_mappings)}"')
    print()


if __name__ == "__main__":
    main()
