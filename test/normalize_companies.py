from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
from collections import defaultdict
import re

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

def normalize_company_name(company):
    """
    Normalize a company name for comparison purposes.
    - Convert to lowercase
    - Strip whitespace
    - Remove extra spaces
    - Remove common punctuation that doesn't affect meaning
    """
    if not company or not isinstance(company, str):
        return ""
    
    # Convert to string and strip
    normalized = str(company).strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Convert to lowercase for comparison
    normalized_lower = normalized.lower()
    
    return normalized_lower, normalized

def choose_canonical_name(variants):
    """
    Choose the best canonical name from a list of variants.
    Prefers:
    1. The most common variant
    2. If tie, the one with proper capitalization (first letter uppercase)
    3. If tie, the shortest one
    """
    if not variants:
        return None
    
    # Count occurrences
    variant_counts = defaultdict(int)
    for variant in variants:
        variant_counts[variant] += 1
    
    # Find the most common
    max_count = max(variant_counts.values())
    most_common = [v for v, count in variant_counts.items() if count == max_count]
    
    # If multiple with same count, prefer proper capitalization
    properly_capitalized = [v for v in most_common if v and v[0].isupper()]
    if properly_capitalized:
        # Among properly capitalized, prefer shortest
        return min(properly_capitalized, key=len)
    
    # Otherwise, prefer shortest among most common
    return min(most_common, key=len)

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Group companies by normalized name
company_groups = defaultdict(list)

for record in records:
    fields = record['fields']
    company = fields.get('目前就职', '')
    name = fields.get('您的姓名', 'Unknown')
    
    if not company:
        continue
    
    # Normalize for grouping
    normalized_lower, original = normalize_company_name(company)
    
    if normalized_lower:
        company_groups[normalized_lower].append({
            'record_id': record['id'],
            'name': name,
            'company': original,
            'normalized': normalized_lower
        })

# Find groups with multiple variants (same normalized but different original)
print("ANALYZING COMPANY NAME VARIATIONS:")
print("=" * 80)

variations_to_fix = {}
total_variants = 0

for normalized, entries in company_groups.items():
    # Get unique original company names
    unique_originals = set(entry['company'] for entry in entries)
    
    if len(unique_originals) > 1:
        # Multiple variants found
        variations_to_fix[normalized] = {
            'variants': list(unique_originals),
            'entries': entries,
            'canonical': choose_canonical_name(list(unique_originals))
        }
        total_variants += len(entries)

print(f"\nFound {len(variations_to_fix)} company names with variations")
print(f"Total records affected: {total_variants}\n")

# Show top variations
print("TOP COMPANY NAME VARIATIONS:")
print("=" * 80)
sorted_variations = sorted(
    variations_to_fix.items(),
    key=lambda x: len(x[1]['entries']),
    reverse=True
)

for i, (normalized, data) in enumerate(sorted_variations[:20], 1):
    print(f"\n{i}. Normalized: '{normalized}'")
    print(f"   Variants found: {data['variants']}")
    print(f"   Canonical choice: '{data['canonical']}'")
    print(f"   Records affected: {len(data['entries'])}")

if len(variations_to_fix) > 20:
    print(f"\n... and {len(variations_to_fix) - 20} more variations")

# Check for --yes flag to skip confirmation
skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

# Ask for confirmation (unless --yes flag is provided)
if not skip_confirmation:
    print("\n" + "=" * 80)
    print(f"\nFound {total_variants} records with company name variations.")
    print("This script will normalize all variations to their canonical form.")
    print("\nDo you want to proceed? (This will update Airtable)")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")

    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
else:
    print("\n" + "=" * 80)
    print(f"\nFound {total_variants} records with company name variations.")
    print("Proceeding with normalization (--yes flag detected)...")

# Update records with normalized company names
print(f"\nNormalizing {total_variants} company names...")
print("=" * 80)

updated_count = 0
error_count = 0

for normalized, data in variations_to_fix.items():
    canonical = data['canonical']
    
    for entry in data['entries']:
        # Only update if the current value is different from canonical
        if entry['company'] != canonical:
            try:
                table.update(entry['record_id'], {
                    '目前就职': canonical
                })
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"  Progress: {updated_count}/{total_variants} records updated...")
            except Exception as e:
                error_count += 1
                print(f"  Error updating {entry['name']} (ID: {entry['record_id']}): {e}")

print("\n" + "=" * 80)
print("NORMALIZATION COMPLETE!")
print("=" * 80)
print(f"Successfully updated: {updated_count} records")
if error_count > 0:
    print(f"Errors: {error_count} records")
print(f"\nAll company name variations have been normalized.")

