from pyairtable import Api
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import re
import sys

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

def is_valid_url(url_string):
    """
    Check if a string is a valid URL.
    Returns True if valid, False otherwise.
    """
    if not url_string or not isinstance(url_string, str):
        return False
    
    url_string = url_string.strip()
    
    # Check for obviously invalid patterns
    invalid_patterns = [
        r'^http:///?$',  # http:// or http:///
        r'^https:///?$',  # https:// or https:///
        r'^http:///$',    # http:///
        r'^https:///$',   # https:///
        r'^/$',           # Just a slash
        r'^$',            # Empty string
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, url_string, re.IGNORECASE):
            return False
    
    # Try to parse as URL
    try:
        result = urlparse(url_string)
        # Must have a scheme (http or https)
        if not result.scheme:
            return False
        if result.scheme not in ['http', 'https']:
            return False
        # Must have a netloc (domain) or at least a path
        if not result.netloc and not result.path:
            return False
        # If netloc exists, it should have at least a dot (domain) or be localhost
        if result.netloc and '.' not in result.netloc and result.netloc != 'localhost':
            return False
        return True
    except Exception:
        return False

def categorize_url(url_string):
    """
    Categorize URLs into valid, invalid, or empty.
    """
    if not url_string:
        return 'empty'
    
    url_string = str(url_string).strip()
    
    if not url_string:
        return 'empty'
    
    if is_valid_url(url_string):
        return 'valid'
    else:
        return 'invalid'

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Analyze Profile URLs
url_stats = {
    'valid': [],
    'invalid': [],
    'empty': []
}

for record in records:
    fields = record['fields']
    profile_url = fields.get('Profiles', '')
    name = fields.get('您的姓名', 'Unknown')
    
    category = categorize_url(profile_url)
    url_stats[category].append({
        'record_id': record['id'],
        'name': name,
        'url': profile_url
    })

# Print statistics
print("PROFILE URL ANALYSIS:")
print("=" * 80)
print(f"Valid URLs: {len(url_stats['valid'])} ({len(url_stats['valid'])/len(records)*100:.1f}%)")
print(f"Invalid URLs: {len(url_stats['invalid'])} ({len(url_stats['invalid'])/len(records)*100:.1f}%)")
print(f"Empty URLs: {len(url_stats['empty'])} ({len(url_stats['empty'])/len(records)*100:.1f}%)")

# Show sample invalid URLs
print("\n\nSAMPLE INVALID URLs (first 20):")
print("=" * 80)
for i, item in enumerate(url_stats['invalid'][:20], 1):
    print(f"{i}. {item['name']}: '{item['url']}'")

if len(url_stats['invalid']) > 20:
    print(f"\n... and {len(url_stats['invalid']) - 20} more invalid URLs")

# Show breakdown of invalid URL patterns
print("\n\nINVALID URL PATTERNS:")
print("=" * 80)
pattern_counts = {}
for item in url_stats['invalid']:
    url = str(item['url']).strip()
    if url in pattern_counts:
        pattern_counts[url] += 1
    else:
        pattern_counts[url] = 1

# Sort by frequency
sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
for pattern, count in sorted_patterns[:10]:
    print(f"  '{pattern}': {count} occurrences")

# Check for --yes flag to skip confirmation
skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

# Ask for confirmation (unless --yes flag is provided)
if not skip_confirmation:
    print("\n" + "=" * 80)
    print(f"\nFound {len(url_stats['invalid'])} records with invalid Profile URLs.")
    print("This script will clear (set to empty) all invalid Profile URLs.")
    print("\nDo you want to proceed? (This will update Airtable)")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")

    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
else:
    print("\n" + "=" * 80)
    print(f"\nFound {len(url_stats['invalid'])} records with invalid Profile URLs.")
    print("Proceeding with cleanup (--yes flag detected)...")

# Update records with invalid URLs
print(f"\nCleaning {len(url_stats['invalid'])} invalid Profile URLs...")
print("=" * 80)

updated_count = 0
error_count = 0

for item in url_stats['invalid']:
    try:
        # Clear the invalid URL by setting it to empty
        table.update(item['record_id'], {
            'Profiles': ''
        })
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"  Progress: {updated_count}/{len(url_stats['invalid'])} records updated...")
    except Exception as e:
        error_count += 1
        print(f"  Error updating {item['name']} (ID: {item['record_id']}): {e}")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE!")
print("=" * 80)
print(f"Successfully updated: {updated_count} records")
if error_count > 0:
    print(f"Errors: {error_count} records")
print(f"\nAll invalid Profile URLs have been cleared.")

