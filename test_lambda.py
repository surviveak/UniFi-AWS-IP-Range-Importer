"""Test script for the UniFi AWS CIDR Importer Lambda function."""
import os
import sys
import lambda_function

# Configuration - Update these with your actual values
CONSOLE_ID = "your-console-id-here"
SITE_NAME = "your-site-name-here"
GROUP_ID = "your-group-id-here"
API_KEY = "your-api-key-here"

# Test with limited results
MAX_IPS = 2  # Only use first 2 IP ranges for testing

def test_fetch_aws_ips():
    """Test fetching AWS IP ranges with filters."""
    print("=" * 60)
    print("TEST 1: Fetching AWS IP ranges")
    print("=" * 60)
    
    # Test with EC2 in us-east-1
    services = ["EC2"]
    regions = ["us-east-1"]
    
    print(f"Services: {services}")
    print(f"Regions: {regions}")
    print()
    
    ip_ranges = lambda_function.get_aws_ip_ranges(services=services, regions=regions)
    
    print(f"Total IP ranges found: {len(ip_ranges)}")
    print(f"\nFirst {MAX_IPS} IP ranges:")
    for i, ip in enumerate(ip_ranges[:MAX_IPS], 1):
        print(f"  {i}. {ip}")
    
    return ip_ranges[:MAX_IPS]


def test_update_unifi(ip_ranges):
    """Test updating UniFi address group."""
    print("\n" + "=" * 60)
    print("TEST 2: Updating UniFi Address Group")
    print("=" * 60)
    
    print(f"Console ID: {CONSOLE_ID}")
    print(f"Site Name: {SITE_NAME}")
    print(f"Group ID: {GROUP_ID}")
    print(f"IP ranges to update: {ip_ranges}")
    print()
    
    try:
        result = lambda_function.update_unifi_address_group(
            console_id=CONSOLE_ID,
            site_name=SITE_NAME,
            group_id=GROUP_ID,
            api_key=API_KEY,
            ip_addresses=ip_ranges
        )
        
        print("✓ Successfully updated UniFi address group!")
        print(f"Response: {result}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating UniFi: {e}")
        return False


def test_full_lambda():
    """Test the full Lambda handler with environment variables."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Lambda Handler (with limit)")
    print("=" * 60)
    
    # Set environment variables
    os.environ["UNIFI_CONSOLE_ID"] = CONSOLE_ID
    os.environ["UNIFI_SITE_NAME"] = SITE_NAME
    os.environ["UNIFI_GROUP_ID"] = GROUP_ID
    os.environ["UNIFI_API_KEY"] = API_KEY
    os.environ["AWS_SERVICE_FILTER"] = "EC2"
    os.environ["AWS_REGION_FILTER"] = "us-east-1"
    
    # Temporarily modify the function to limit results
    original_func = lambda_function.get_aws_ip_ranges
    
    def limited_get_aws_ip_ranges(*args, **kwargs):
        results = original_func(*args, **kwargs)
        print(f"  (Limiting to {MAX_IPS} IPs for testing)")
        return results[:MAX_IPS]
    
    lambda_function.get_aws_ip_ranges = limited_get_aws_ip_ranges
    
    try:
        result = lambda_function.lambda_handler({}, {})
        print("\n✓ Lambda handler completed successfully!")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"\n✗ Lambda handler failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore original function
        lambda_function.get_aws_ip_ranges = original_func


if __name__ == "__main__":
    print("UniFi AWS CIDR Importer - Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Fetch AWS IPs
    ip_ranges = test_fetch_aws_ips()
    
    if not ip_ranges:
        print("\n✗ No IP ranges found. Check your filters.")
        sys.exit(1)
    
    # Test 2: Update UniFi
    success = test_update_unifi(ip_ranges)
    
    if not success:
        print("\n✗ Failed to update UniFi. Check your credentials and network.")
        sys.exit(1)
    
    # Test 3: Full Lambda handler
    success = test_full_lambda()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYou can now deploy the Lambda function with confidence.")
        print("\nTo test with more IPs, change MAX_IPS in this script.")
    else:
        print("\n✗ Some tests failed. Review the errors above.")
        sys.exit(1)
