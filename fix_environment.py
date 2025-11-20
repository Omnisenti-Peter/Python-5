"""
Environment fix script - clears proxy settings that might interfere with OpenAI
"""
import os
import sys

print("=" * 60)
print("Environment Fix Script")
print("=" * 60)
print()

# Check for proxy environment variables
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
found_proxies = []

print("Checking for proxy environment variables...")
for var in proxy_vars:
    if os.environ.get(var):
        found_proxies.append(var)
        print(f"  Found: {var} = {os.environ.get(var)}")

if found_proxies:
    print()
    print("⚠ Proxy settings detected!")
    print("These may interfere with OpenAI API calls.")
    print()
    print("To temporarily disable proxies for this session:")
    print()
    if sys.platform == 'win32':
        print("PowerShell:")
        for var in found_proxies:
            print(f'  $env:{var}=""')
        print()
        print("CMD:")
        for var in found_proxies:
            print(f'  set {var}=')
    else:
        print("Terminal:")
        for var in found_proxies:
            print(f'  unset {var}')
    print()
    print("After running these commands, restart Flask app.")
else:
    print("  ✓ No proxy environment variables found")

print()
print("=" * 60)
print("Checking OpenAI library installation...")
print("=" * 60)

try:
    import openai
    print(f"✓ OpenAI library installed: version {openai.__version__}")

    # Check if version is compatible
    version_parts = openai.__version__.split('.')
    major_version = int(version_parts[0])

    if major_version < 1:
        print("⚠ WARNING: OpenAI library version is too old!")
        print("  Please upgrade: pip install --upgrade openai")
    else:
        print("  ✓ Version is compatible with new API")

except ImportError:
    print("✗ OpenAI library not installed")
    print("  Install with: pip install openai")

print()
print("=" * 60)
print("Recommended actions:")
print("=" * 60)
print()
print("1. Update OpenAI library:")
print("   pip install --upgrade openai")
print()
print("2. If you have proxy settings, temporarily disable them")
print()
print("3. Restart your Flask application")
print()
print("4. Test API connection:")
print("   python test_api_keys.py")
print()
