from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
from collections import Counter, defaultdict

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Tag migration mapping
TAG_MIGRATION_MAP = {
    'Doer': 'Founder',
    'Frontier': 'Frontier',  # Keep as is
    'Engineer / Lead': 'Engineer',
    'Investor': 'Investor',  # Keep as is
    'Student': 'Student',  # Keep as is
    'Professor': 'Academic',
    'VP': 'Executive',
    'lawyer': 'Professional',
    # Tags to remove (set to None)
    '非会员': None,  # Remove - should be in membership status field
    'House Owner': None,  # Remove - not a professional category
}

# Final list of valid tags
VALID_TAGS = {
    'Founder',
    'Frontier',
    'Researcher',  # New tag (not in current data, but available for future)
    'Engineer',
    'Investor',
    'Academic',
    'Student',
    'Executive',
    'Professional',
}

def normalize_tag(tag):
    """Normalize tag by stripping whitespace."""
    if not tag:
        return None
    return str(tag).strip() if str(tag).strip() else None

def migrate_tags(old_tags):
    """
    Migrate old tags to new tags according to the migration map.
    Returns a list of new tags (may be empty if all tags are removed).
    """
    if not old_tags:
        return []
    
    # Handle both list and string formats
    tag_list = []
    if isinstance(old_tags, list):
        tag_list = old_tags
    elif isinstance(old_tags, str):
        # Try splitting by common delimiters
        for delimiter in [',', ';', '|', '\n']:
            if delimiter in old_tags:
                tag_list = [t.strip() for t in old_tags.split(delimiter) if t.strip()]
                break
        else:
            # Single tag value
            if old_tags.strip():
                tag_list = [old_tags.strip()]
    
    # Migrate each tag
    new_tags = []
    for tag in tag_list:
        normalized = normalize_tag(tag)
        if not normalized:
            continue
        
        # Check migration map
        if normalized in TAG_MIGRATION_MAP:
            new_tag = TAG_MIGRATION_MAP[normalized]
            if new_tag and new_tag not in new_tags:  # Add if not None and not duplicate
                new_tags.append(new_tag)
        else:
            # Unknown tag - keep it but warn
            if normalized not in new_tags:
                new_tags.append(normalized)
    
    return new_tags

# IMPORTANT PREREQUISITE:
# Before running this migration, you MUST add the following new tag options
# to the Airtable "标签" field dropdown:
#   1. Founder
#   2. Academic
#   3. Executive
#   4. Professional
#   5. Researcher (optional, for future use)
#
# The existing tags should already be in the dropdown:
#   - Frontier (keep as is)
#   - Investor (keep as is)
#   - Student (keep as is)
#   - Engineer (needs to be added - replacing "Engineer / Lead")
#
# To add options in Airtable:
#   1. Open your Airtable base
#   2. Go to the table with the "标签" field
#   3. Click on the field header
#   4. Edit the field options and add the new values above
#   5. Then run this script

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Analyze current tags and plan migrations
migration_stats = {
    'no_change': [],
    'needs_migration': [],
    'will_be_removed': [],
    'unknown_tags': defaultdict(list),
}

old_tag_counts = Counter()
new_tag_counts = Counter()

for record in records:
    fields = record['fields']
    old_tags = fields.get('标签', '')
    name = fields.get('您的姓名', 'Unknown')
    record_id = record['id']
    
    # Count old tags
    if isinstance(old_tags, list):
        for tag in old_tags:
            if tag:
                old_tag_counts[str(tag).strip()] += 1
    elif old_tags:
        old_tag_counts[str(old_tags).strip()] += 1
    
    # Plan migration
    new_tags = migrate_tags(old_tags)
    
    # Check if migration is needed
    old_tags_list = []
    if isinstance(old_tags, list):
        old_tags_list = [normalize_tag(t) for t in old_tags if normalize_tag(t)]
    elif old_tags:
        old_tags_list = [normalize_tag(old_tags)]
    
    # Normalize for comparison
    old_tags_set = set(old_tags_list)
    new_tags_set = set(new_tags)
    
    # Check for unknown tags (tags not in migration map)
    unknown_tags = []
    for tag in old_tags_list:
        if tag and tag not in TAG_MIGRATION_MAP:
            unknown_tags.append(tag)
    
    if unknown_tags:
        for tag in unknown_tags:
            migration_stats['unknown_tags'][tag].append({
                'name': name,
                'record_id': record_id,
            })
    
    # Categorize migration
    if old_tags_set == new_tags_set:
        migration_stats['no_change'].append({
            'name': name,
            'record_id': record_id,
            'tags': old_tags_list,
        })
    elif not new_tags and old_tags_list:
        # All tags will be removed
        migration_stats['will_be_removed'].append({
            'name': name,
            'record_id': record_id,
            'old_tags': old_tags_list,
        })
    else:
        migration_stats['needs_migration'].append({
            'name': name,
            'record_id': record_id,
            'old_tags': old_tags_list,
            'new_tags': new_tags,
        })
    
    # Count new tags
    for tag in new_tags:
        new_tag_counts[tag] += 1

# Print analysis
print("TAG MIGRATION ANALYSIS:")
print("=" * 80)
print(f"Records with no changes needed: {len(migration_stats['no_change'])}")
print(f"Records that need migration: {len(migration_stats['needs_migration'])}")
print(f"Records that will have all tags removed: {len(migration_stats['will_be_removed'])}")
print(f"Records with unknown tags: {sum(len(v) for v in migration_stats['unknown_tags'].values())}")

# Show migration mapping
print("\n\nTAG MIGRATION MAPPING:")
print("=" * 80)
for old_tag, new_tag in TAG_MIGRATION_MAP.items():
    if new_tag is None:
        print(f"  '{old_tag}' → REMOVE")
    else:
        print(f"  '{old_tag}' → '{new_tag}'")

# Show old tag distribution
print("\n\nCURRENT TAG DISTRIBUTION:")
print("=" * 80)
for tag, count in old_tag_counts.most_common():
    print(f"  '{tag}': {count} occurrences")

# Show new tag distribution (projected)
print("\n\nPROJECTED NEW TAG DISTRIBUTION:")
print("=" * 80)
for tag, count in new_tag_counts.most_common():
    print(f"  '{tag}': {count} occurrences")

# Show sample migrations
print("\n\nSAMPLE MIGRATIONS (first 20):")
print("=" * 80)
for i, item in enumerate(migration_stats['needs_migration'][:20], 1):
    old_str = ', '.join(item['old_tags'])
    new_str = ', '.join(item['new_tags'])
    print(f"{i}. {item['name']}:")
    print(f"   Old: [{old_str}]")
    print(f"   New: [{new_str}]")

if len(migration_stats['needs_migration']) > 20:
    print(f"\n... and {len(migration_stats['needs_migration']) - 20} more migrations")

# Show records that will have tags removed
if migration_stats['will_be_removed']:
    print("\n\nRECORDS THAT WILL HAVE ALL TAGS REMOVED:")
    print("=" * 80)
    for item in migration_stats['will_be_removed']:
        old_str = ', '.join(item['old_tags'])
        print(f"  {item['name']}: [{old_str}]")

# Show unknown tags
if migration_stats['unknown_tags']:
    print("\n\nWARNING: UNKNOWN TAGS FOUND (not in migration map):")
    print("=" * 80)
    for tag, records_list in migration_stats['unknown_tags'].items():
        print(f"  '{tag}': {len(records_list)} occurrences")
        print(f"    Sample records: {', '.join([r['name'] for r in records_list[:5]])}")
        if len(records_list) > 5:
            print(f"    ... and {len(records_list) - 5} more")

# IMPORTANT: Before running this migration, you need to add the new tag options
# to the Airtable dropdown field. The new tags that need to be added are:
# - Founder
# - Academic  
# - Executive
# - Professional
# - Researcher (optional, for future use)
#
# The existing tags (Frontier, Investor, Student, Engineer) should already exist.
# After adding these options in Airtable, you can run this script.

# Check for --yes flag to skip confirmation
skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

# Ask for confirmation (unless --yes flag is provided)
if not skip_confirmation:
    print("\n" + "=" * 80)
    print(f"\nThis script will migrate tags for {len(migration_stats['needs_migration'])} records.")
    if migration_stats['will_be_removed']:
        print(f"WARNING: {len(migration_stats['will_be_removed'])} records will have all tags removed.")
    if migration_stats['unknown_tags']:
        print(f"WARNING: {sum(len(v) for v in migration_stats['unknown_tags'].values())} records have unknown tags that will be kept as-is.")
    print("\nDo you want to proceed? (This will update Airtable)")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")

    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
else:
    print("\n" + "=" * 80)
    print(f"\nProceeding with tag migration (--yes flag detected)...")
    if migration_stats['will_be_removed']:
        print(f"WARNING: {len(migration_stats['will_be_removed'])} records will have all tags removed.")
    if migration_stats['unknown_tags']:
        print(f"WARNING: {sum(len(v) for v in migration_stats['unknown_tags'].values())} records have unknown tags that will be kept as-is.")

# Perform migration
print(f"\nMigrating tags for {len(migration_stats['needs_migration'])} records...")
print("=" * 80)

updated_count = 0
error_count = 0
removed_count = 0

# Migrate records that need changes
for item in migration_stats['needs_migration']:
    try:
        # Determine the format to use based on field type
        # Try single string first (for single-select), then list (for multi-select)
        if len(item['new_tags']) == 0:
            # Empty - use None to clear the field
            update_value = None
        elif len(item['new_tags']) == 1:
            # Single tag - use string format (works for both single-select and multi-select)
            update_value = item['new_tags'][0]
        else:
            # Multiple tags - try list format (for multi-select fields)
            update_value = item['new_tags']
        
        table.update(item['record_id'], {
            '标签': update_value
        })
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"  Progress: {updated_count}/{len(migration_stats['needs_migration'])} records updated...")
    except Exception as e:
        error_count += 1
        print(f"  Error updating {item['name']} (ID: {item['record_id']}): {e}")
        # If list format failed, try single string format (for single-select fields)
        if len(item['new_tags']) > 1:
            try:
                # Try with just the first tag
                table.update(item['record_id'], {
                    '标签': item['new_tags'][0]
                })
                updated_count += 1
                error_count -= 1  # Adjust error count since we recovered
                print(f"  Recovered: {item['name']} - using first tag only (single-select field)")
            except Exception as e2:
                print(f"  Still failed: {e2}")

# Remove tags from records that should have them removed
for item in migration_stats['will_be_removed']:
    try:
        # Set to None to clear the field (works for both single-select and multi-select)
        table.update(item['record_id'], {
            '标签': None
        })
        removed_count += 1
        if removed_count % 10 == 0:
            print(f"  Progress: {removed_count}/{len(migration_stats['will_be_removed'])} records cleaned...")
    except Exception as e:
        error_count += 1
        print(f"  Error removing tags from {item['name']} (ID: {item['record_id']}): {e}")

print("\n" + "=" * 80)
print("MIGRATION COMPLETE!")
print("=" * 80)
print(f"Successfully migrated: {updated_count} records")
if removed_count > 0:
    print(f"Successfully removed tags: {removed_count} records")
if error_count > 0:
    print(f"Errors: {error_count} records")
print(f"\nTag migration completed successfully!")

