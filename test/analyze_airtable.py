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

# Analyze field structure
all_fields = set()
field_types = {}
field_values = {}

for record in records:
    fields = record['fields']
    for field_name, field_value in fields.items():
        all_fields.add(field_name)
        
        # Track field types and sample values
        if field_name not in field_types:
            field_types[field_name] = []
        if field_name not in field_values:
            field_values[field_name] = []
        
        # Determine type
        if isinstance(field_value, list):
            field_types[field_name].append('list')
        elif isinstance(field_value, str):
            field_types[field_name].append('string')
        elif isinstance(field_value, (int, float)):
            field_types[field_name].append('number')
        elif isinstance(field_value, bool):
            field_types[field_name].append('boolean')
        else:
            field_types[field_name].append(type(field_value).__name__)
        
        # Store sample values (first 5 non-empty)
        if field_value and len(field_values[field_name]) < 5:
            if isinstance(field_value, list):
                field_values[field_name].append(str(field_value[:2]))  # First 2 items
            else:
                field_values[field_name].append(str(field_value)[:100])  # First 100 chars

# Print field analysis
print("\nFIELD STRUCTURE ANALYSIS:")
print("=" * 80)
for field in sorted(all_fields):
    type_counts = Counter(field_types[field])
    most_common_type = type_counts.most_common(1)[0][0]
    non_empty_count = sum(1 for r in records if field in r['fields'] and r['fields'][field])
    empty_count = len(records) - non_empty_count
    
    print(f"\nField: {field}")
    print(f"  Type: {most_common_type}")
    print(f"  Filled: {non_empty_count}/{len(records)} ({non_empty_count/len(records)*100:.1f}%)")
    print(f"  Empty: {empty_count}/{len(records)} ({empty_count/len(records)*100:.1f}%)")
    if field_values[field]:
        print(f"  Sample values:")
        for val in field_values[field][:3]:
            print(f"    - {val}")

# Data quality analysis
print("\n\nDATA QUALITY ANALYSIS:")
print("=" * 80)

# Check for missing critical fields
critical_fields = ['您的姓名', 'Title', '目前就职', 'Bio', 'Profiles']
print("\nMissing critical fields:")
for field in critical_fields:
    if field in all_fields:
        missing = sum(1 for r in records if field not in r['fields'] or not r['fields'].get(field))
        print(f"  {field}: {missing} records missing ({missing/len(records)*100:.1f}%)")
    else:
        print(f"  {field}: FIELD NOT FOUND IN TABLE")

# Check for duplicates
print("\n\nDUPLICATE CHECK:")
print("=" * 80)
name_counts = Counter()
for record in records:
    name = record['fields'].get('您的姓名', '')
    if name:
        name_counts[name] += 1

duplicates = {name: count for name, count in name_counts.items() if count > 1}
if duplicates:
    print(f"Found {len(duplicates)} duplicate names:")
    for name, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count} occurrences")
else:
    print("No duplicate names found")

# Show first few complete records
print("\n\nSAMPLE RECORDS (first 3 complete records):")
print("=" * 80)
shown = 0
for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '')
    if name and shown < 3:
        print(f"\nRecord {shown + 1}:")
        print(f"  ID: {record['id']}")
        for key, value in fields.items():
            if isinstance(value, list):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {str(value)[:100]}")
        shown += 1

print("\n" + "=" * 80)
print("Analysis complete!")

