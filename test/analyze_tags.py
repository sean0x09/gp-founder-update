from pyairtable import Api
from dotenv import load_dotenv
import os
from collections import Counter

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Collect all tag values
tag_values = []
tag_counts = Counter()
empty_count = 0
records_with_tags = []

for record in records:
    fields = record['fields']
    tags = fields.get('标签', '')
    name = fields.get('您的姓名', 'Unknown')
    
    if not tags:
        empty_count += 1
        continue
    
    # Handle both list and string formats
    if isinstance(tags, list):
        for tag in tags:
            if tag and str(tag).strip():
                tag_clean = str(tag).strip()
                tag_values.append(tag_clean)
                tag_counts[tag_clean] += 1
                records_with_tags.append({
                    'name': name,
                    'tag': tag_clean,
                    'record_id': record['id']
                })
    elif isinstance(tags, str):
        # Handle comma-separated or other delimited strings
        tag_str = tags.strip()
        if tag_str:
            # Try splitting by common delimiters
            for delimiter in [',', ';', '|', '\n']:
                if delimiter in tag_str:
                    split_tags = [t.strip() for t in tag_str.split(delimiter) if t.strip()]
                    for tag in split_tags:
                        tag_values.append(tag)
                        tag_counts[tag] += 1
                        records_with_tags.append({
                            'name': name,
                            'tag': tag,
                            'record_id': record['id']
                        })
                    break
            else:
                # Single tag value
                tag_values.append(tag_str)
                tag_counts[tag_str] += 1
                records_with_tags.append({
                    'name': name,
                    'tag': tag_str,
                    'record_id': record['id']
                })

print(f"Records with tags: {len(records) - empty_count}")
print(f"Records without tags: {empty_count}")
print(f"Total tag instances: {len(tag_values)}")
print(f"Unique tag values: {len(tag_counts)}\n")

# Show all unique tags with counts
print("ALL TAG VALUES (sorted by frequency):")
print("=" * 80)
for tag, count in tag_counts.most_common():
    print(f"  '{tag}': {count} occurrences")

# Show sample records for each tag
print("\n\nSAMPLE RECORDS FOR EACH TAG:")
print("=" * 80)
for tag, count in tag_counts.most_common():
    print(f"\nTag: '{tag}' ({count} occurrences)")
    # Show first 5 names with this tag
    sample_names = [r['name'] for r in records_with_tags if r['tag'] == tag][:5]
    for name in sample_names:
        print(f"  - {name}")
    if count > 5:
        print(f"  ... and {count - 5} more")

