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

def normalize_title_for_comparison(title):
    """
    Normalize title for finding variations.
    - Convert to lowercase
    - Remove extra whitespace
    - Normalize separators
    """
    if not title:
        return ""
    
    normalized = str(title).strip().lower()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    # Normalize separators - convert "and" to "&" for comparison
    normalized = normalized.replace(' and ', ' & ')
    # Remove spaces around &
    normalized = re.sub(r'\s*&\s*', ' & ', normalized)
    # Normalize slashes
    normalized = normalized.replace('/', ' & ')
    return normalized

def choose_canonical_title(variants):
    """
    Choose the best canonical title from a list of variants.
    Prefers:
    1. The most common variant
    2. If tie, the one with proper capitalization
    3. If tie, the one using "&" instead of "and"
    4. If tie, the shortest one
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
    
    # Scoring function for canonical selection
    def score_title(title):
        score = 0
        # Prefer proper capitalization (first letter uppercase)
        if title and title[0].isupper():
            score += 100
        # Prefer "&" over "and"
        if ' & ' in title or '&' in title:
            score += 50
        elif ' and ' in title.lower():
            score += 25
        # Prefer shorter (but not too short)
        score += max(0, 20 - len(title))
        return score
    
    # Score all most common variants
    scored = [(v, score_title(v)) for v in most_common]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[0][0] if scored else most_common[0]

def normalize_title_formatting(title):
    """
    Apply standard formatting rules to a title.
    - Proper capitalization
    - Consistent separator usage
    - Proper spacing
    """
    if not title:
        return title
    
    # Trim whitespace
    title = title.strip()
    
    # Normalize separators: convert "and" to "&" (but preserve Chinese)
    # Only do this for English "and" not in Chinese context
    title = re.sub(r'\s+and\s+', ' & ', title, flags=re.IGNORECASE)
    
    # Normalize spacing around &
    title = re.sub(r'\s*&\s*', ' & ', title)
    
    # Normalize slashes to ampersands (for English titles)
    # But be careful with Chinese titles that might use /
    if not any('\u4e00' <= char <= '\u9fff' for char in title):
        # No Chinese characters, safe to convert /
        title = re.sub(r'\s*/\s*', ' & ', title)
    
    # Fix capitalization for common patterns
    # Title case for words, but preserve acronyms
    words = title.split()
    normalized_words = []
    
    for i, word in enumerate(words):
        # Preserve acronyms (all caps, 2+ letters)
        if len(word) >= 2 and word.isupper() and word.isalpha():
            normalized_words.append(word)
        # Preserve mixed case words that look like proper nouns (e.g., "TSquare", "ByteDance")
        elif len(word) > 1 and word[0].isupper() and any(c.isupper() for c in word[1:]) and word.isalpha():
            normalized_words.append(word)
        # Preserve Chinese characters
        elif any('\u4e00' <= char <= '\u9fff' for char in word):
            normalized_words.append(word)
        # Preserve special words like "Co-" prefix
        elif word.lower().startswith('co-'):
            normalized_words.append('Co-' + word[3:].capitalize() if len(word) > 3 else word.capitalize())
        # First word should be capitalized
        elif i == 0:
            normalized_words.append(word.capitalize())
        # Common lowercase words (articles, prepositions)
        elif word.lower() in ['of', 'at', 'the', 'a', 'an', 'in', 'on']:
            normalized_words.append(word.lower())
        # Capitalize other words
        else:
            normalized_words.append(word.capitalize())
    
    title = ' '.join(normalized_words)
    
    # Clean up extra spaces
    title = re.sub(r'\s+', ' ', title)
    
    return title

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Group titles by normalized name
title_groups = defaultdict(list)

for record in records:
    fields = record['fields']
    title = fields.get('Title', '')
    name = fields.get('您的姓名', 'Unknown')
    
    if not title or not isinstance(title, str) or not title.strip():
        continue
    
    title_clean = title.strip()
    
    # Normalize for grouping
    normalized = normalize_title_for_comparison(title_clean)
    
    if normalized:
        title_groups[normalized].append({
            'record_id': record['id'],
            'name': name,
            'title': title_clean,
            'normalized': normalized
        })

# Find groups with multiple variants
print("ANALYZING TITLE VARIATIONS:")
print("=" * 80)

variations_to_fix = {}
total_variants = 0

for normalized, entries in title_groups.items():
    # Get unique original titles
    unique_originals = set(entry['title'] for entry in entries)
    
    if len(unique_originals) > 1:
        # Multiple variants found
        canonical = choose_canonical_title(list(unique_originals))
        # Apply formatting normalization to canonical
        canonical_formatted = normalize_title_formatting(canonical)
        
        variations_to_fix[normalized] = {
            'variants': list(unique_originals),
            'entries': entries,
            'canonical': canonical,
            'canonical_formatted': canonical_formatted
        }
        total_variants += len(entries)

print(f"\nFound {len(variations_to_fix)} title groups with variations")
print(f"Total records affected: {total_variants}\n")

# Show top variations
print("TOP TITLE VARIATIONS:")
print("=" * 80)
sorted_variations = sorted(
    variations_to_fix.items(),
    key=lambda x: len(x[1]['entries']),
    reverse=True
)

for i, (normalized, data) in enumerate(sorted_variations[:30], 1):
    print(f"\n{i}. Normalized: '{normalized}'")
    print(f"   Variants found: {data['variants']}")
    print(f"   Canonical choice: '{data['canonical_formatted']}'")
    print(f"   Records affected: {len(data['entries'])}")

if len(variations_to_fix) > 30:
    print(f"\n... and {len(variations_to_fix) - 30} more variation groups")

# Check for --yes flag to skip confirmation
skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

# Ask for confirmation (unless --yes flag is provided)
if not skip_confirmation:
    print("\n" + "=" * 80)
    print(f"\nFound {total_variants} records with title variations.")
    print("This script will normalize all variations to their canonical form.")
    print("\nDo you want to proceed? (This will update Airtable)")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")

    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
else:
    print("\n" + "=" * 80)
    print(f"\nFound {total_variants} records with title variations.")
    print("Proceeding with normalization (--yes flag detected)...")

# Update records with normalized titles
print(f"\nNormalizing {total_variants} titles...")
print("=" * 80)

updated_count = 0
error_count = 0

for normalized, data in variations_to_fix.items():
    canonical = data['canonical_formatted']
    
    for entry in data['entries']:
        # Only update if the current value is different from canonical
        if entry['title'] != canonical:
            try:
                table.update(entry['record_id'], {
                    'Title': canonical
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
print(f"\nAll title variations have been normalized.")

