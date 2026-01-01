from pyairtable import Api
from dotenv import load_dotenv
import os
from collections import Counter, defaultdict
import re

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Collect all titles
titles = []
title_counts = Counter()
empty_count = 0

for record in records:
    fields = record['fields']
    title = fields.get('Title', '')
    name = fields.get('您的姓名', 'Unknown')
    
    if not title or not isinstance(title, str) or not title.strip():
        empty_count += 1
        continue
    
    title_clean = title.strip()
    titles.append({
        'title': title_clean,
        'name': name,
        'record_id': record['id']
    })
    title_counts[title_clean] += 1

print(f"Records with titles: {len(titles)}")
print(f"Records without titles: {empty_count}")
print(f"Unique title values: {len(title_counts)}\n")

# Show most common titles
print("MOST COMMON TITLES:")
print("=" * 80)
for title, count in title_counts.most_common(30):
    print(f"  '{title}': {count} occurrences")

# Analyze variations - normalize for comparison
def normalize_title_for_comparison(title):
    """
    Normalize title for finding variations.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove common punctuation
    """
    if not title:
        return ""
    
    normalized = str(title).strip().lower()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    # Remove common punctuation that doesn't affect meaning
    normalized = normalized.replace('.', '').replace(',', '').replace('&', 'and')
    return normalized

# Group titles by normalized form
normalized_groups = defaultdict(list)

for title_data in titles:
    normalized = normalize_title_for_comparison(title_data['title'])
    if normalized:
        normalized_groups[normalized].append(title_data)

# Find groups with multiple variants
print("\n\nTITLE VARIATIONS (same meaning, different formatting):")
print("=" * 80)

variations = {}
for normalized, entries in normalized_groups.items():
    unique_titles = set(entry['title'] for entry in entries)
    if len(unique_titles) > 1:
        variations[normalized] = {
            'variants': sorted(list(unique_titles)),
            'count': len(entries),
            'entries': entries
        }

if variations:
    # Sort by number of affected records
    sorted_variations = sorted(variations.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"Found {len(variations)} title groups with variations affecting {sum(v['count'] for v in variations.values())} records\n")
    
    for i, (normalized, data) in enumerate(sorted_variations[:30], 1):
        print(f"{i}. Normalized: '{normalized}'")
        print(f"   Variants: {data['variants']}")
        print(f"   Records affected: {data['count']}")
        print()
    
    if len(variations) > 30:
        print(f"... and {len(variations) - 30} more variation groups")
else:
    print("No significant variations found!")

# Analyze common patterns
print("\n\nCOMMON TITLE PATTERNS:")
print("=" * 80)

# Look for common prefixes/suffixes
prefixes = Counter()
suffixes = Counter()
words = Counter()

for title_data in titles:
    title = title_data['title']
    words_in_title = title.split()
    
    if words_in_title:
        # First word (prefix)
        prefixes[words_in_title[0].lower()] += 1
        # Last word (suffix)
        suffixes[words_in_title[-1].lower()] += 1
    
    # All words
    for word in words_in_title:
        words[word.lower()] += 1

print("\nMost common first words:")
for word, count in prefixes.most_common(15):
    print(f"  '{word}': {count}")

print("\nMost common last words:")
for word, count in suffixes.most_common(15):
    print(f"  '{word}': {count}")

print("\nMost common words overall:")
for word, count in words.most_common(20):
    print(f"  '{word}': {count}")

# Look for specific patterns that might need normalization
print("\n\nPOTENTIAL NORMALIZATION OPPORTUNITIES:")
print("=" * 80)

# Check for common abbreviations vs full forms
abbreviation_patterns = {
    'ceo': ['chief executive officer', 'ceo'],
    'cto': ['chief technology officer', 'cto'],
    'cfo': ['chief financial officer', 'cfo'],
    'coo': ['chief operating officer', 'coo'],
    'cpo': ['chief product officer', 'cpo'],
    'cmo': ['chief marketing officer', 'cmo'],
    'vp': ['vice president', 'vp'],
    'svp': ['senior vice president', 'svp'],
    'evp': ['executive vice president', 'evp'],
}

for pattern_name, patterns in abbreviation_patterns.items():
    found = []
    for title_data in titles:
        title_lower = title_data['title'].lower()
        for pattern in patterns:
            if pattern in title_lower:
                found.append(title_data['title'])
                break
    
    if found:
        unique_found = set(found)
        if len(unique_found) > 1:
            print(f"\n{pattern_name.upper()} variations:")
            for variant in sorted(unique_found)[:10]:
                count = sum(1 for t in found if t == variant)
                print(f"  '{variant}': {count} occurrences")
            if len(unique_found) > 10:
                print(f"  ... and {len(unique_found) - 10} more variants")

print("\n" + "=" * 80)
print("Analysis complete!")

