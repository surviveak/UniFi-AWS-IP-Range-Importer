import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any


def get_aws_ip_ranges(services: List[str] = None, regions: List[str] = None, ipv4_only: bool = True) -> Dict[str, List[str]]:
    """Fetch AWS IP ranges from the official JSON file, grouped by service.
    
    Args:
        services: List of AWS services to filter by (e.g., ["CLOUDFRONT", "S3"])
        regions: List of AWS regions to filter by (e.g., ["us-east-1", "us-west-2"])
        ipv4_only: If True, only return IPv4 addresses (default: True)
    
    Returns:
        Dictionary mapping service names to lists of IP prefixes
    """
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
    
    # Group prefixes by service
    service_prefixes = {}
    
    # IPv4 prefixes
    for prefix in data.get("prefixes", []):
        service = prefix.get("service")
        if services and service not in services:
            continue
        if regions and prefix.get("region") not in regions:
            continue
        
        if service not in service_prefixes:
            service_prefixes[service] = []
        service_prefixes[service].append(prefix["ip_prefix"])
    
    # IPv6 prefixes (only if ipv4_only is False)
    if not ipv4_only:
        for prefix in data.get("ipv6_prefixes", []):
            service = prefix.get("service")
            if services and service not in services:
                continue
            if regions and prefix.get("region") not in regions:
                continue
            
            if service not in service_prefixes:
                service_prefixes[service] = []
            service_prefixes[service].append(prefix["ipv6_prefix"])
    
    return service_prefixes


def update_unifi_address_group(
    console_id: str,
    site_name: str,
    group_id: str,
    api_key: str,
    ip_addresses: List[str]
) -> Dict[str, Any]:
    """Update UniFi address group with new IP addresses using legacy API.
    
    WARNING: This REPLACES all addresses in the group. Any existing addresses
    not in the ip_addresses list will be removed.
    
    Args:
        console_id: UniFi console ID
        site_name: UniFi site internal reference name
        group_id: Address group ID to update
        api_key: UniFi API key
        ip_addresses: List of IP addresses/CIDR blocks to set in the group
    
    Returns:
        API response dictionary
    """
    url = f"https://api.ui.com/v1/connector/consoles/{console_id}/proxy/network/api/s/{site_name}/rest/firewallgroup/{group_id}"
    
    payload = {
        "group_members": ip_addresses
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
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"UniFi API error: {e.code} - {error_body}")


def lambda_handler(event, context):
    """Lambda handler triggered by SNS notification for AWS IP range updates."""
    
    # Get configuration from environment variables
    console_id = os.environ.get("UNIFI_CONSOLE_ID")
    site_name = os.environ.get("UNIFI_SITE_NAME")
    api_key = os.environ.get("UNIFI_API_KEY")
    
    # Parse service and region filters (comma-separated)
    aws_services_str = os.environ.get("AWS_SERVICE_FILTER", "AMAZON")
    aws_regions_str = os.environ.get("AWS_REGION_FILTER")
    
    # Parse group mappings (format: SERVICE1:GROUP_ID1,SERVICE2:GROUP_ID2)
    group_mappings_str = os.environ.get("UNIFI_GROUP_MAPPINGS")
    
    # Legacy single group support
    single_group_id = os.environ.get("UNIFI_GROUP_ID")
    
    aws_services = [s.strip() for s in aws_services_str.split(",")] if aws_services_str else None
    aws_regions = [r.strip() for r in aws_regions_str.split(",")] if aws_regions_str else None
    
    # Parse group mappings
    group_mappings = {}
    if group_mappings_str:
        for mapping in group_mappings_str.split(","):
            if ":" in mapping:
                service, group_id = mapping.split(":", 1)
                group_mappings[service.strip()] = group_id.strip()
    
    # Validate required environment variables
    required_vars = {
        "UNIFI_CONSOLE_ID": console_id,
        "UNIFI_SITE_NAME": site_name,
        "UNIFI_API_KEY": api_key
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Validate that we have either group mappings or a single group ID
    if not group_mappings and not single_group_id:
        raise ValueError("Must provide either UNIFI_GROUP_MAPPINGS or UNIFI_GROUP_ID")
    
    print(f"Fetching AWS IP ranges for services: {aws_services}")
    if aws_regions:
        print(f"Filtering by regions: {aws_regions}")
    
    # Fetch AWS IP ranges grouped by service
    service_ip_ranges = get_aws_ip_ranges(services=aws_services, regions=aws_regions)
    
    total_ips = sum(len(ips) for ips in service_ip_ranges.values())
    print(f"Found {total_ips} total IP ranges across {len(service_ip_ranges)} services")
    
    results = []
    
    # If using group mappings, update each service to its own group
    if group_mappings:
        for service, group_id in group_mappings.items():
            if service not in service_ip_ranges:
                print(f"Warning: No IP ranges found for service {service}")
                continue
            
            ip_ranges = service_ip_ranges[service]
            print(f"Updating {service} group {group_id} with {len(ip_ranges)} IPs")
            
            result = update_unifi_address_group(
                console_id=console_id,
                site_name=site_name,
                group_id=group_id,
                api_key=api_key,
                ip_addresses=ip_ranges
            )
            
            results.append({
                "service": service,
                "group_id": group_id,
                "ip_count": len(ip_ranges),
                "result": result
            })
    
    # Legacy mode: combine all services into single group
    else:
        all_ips = []
        for service, ips in service_ip_ranges.items():
            all_ips.extend(ips)
        
        print(f"Updating single group {single_group_id} with {len(all_ips)} IPs from all services")
        
        result = update_unifi_address_group(
            console_id=console_id,
            site_name=site_name,
            group_id=single_group_id,
            api_key=api_key,
            ip_addresses=all_ips
        )
        
        results.append({
            "mode": "legacy_single_group",
            "group_id": single_group_id,
            "ip_count": len(all_ips),
            "result": result
        })
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Successfully updated UniFi address groups",
            "total_ips": total_ips,
            "groups_updated": len(results),
            "results": results
        })
    }
