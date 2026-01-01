from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
import re

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

def has_chinese_characters(text):
    """Check if text contains Chinese characters"""
    if not text:
        return False
    return any('\u4e00' <= char <= '\u9fff' for char in text)

def is_likely_english_name(text):
    """Check if text is likely an English name (contains mostly Latin letters)"""
    if not text:
        return False
    # Remove common punctuation and whitespace
    cleaned = re.sub(r'[^\w]', '', text)
    if not cleaned:
        return False
    # Check if it's mostly Latin letters
    latin_ratio = sum(1 for c in cleaned if c.isalpha() and ord(c) < 128) / len(cleaned)
    return latin_ratio > 0.7 and not has_chinese_characters(text)

def is_likely_bio_or_description(text):
    """Check if text looks like a bio/description rather than a name"""
    if not text:
        return False
    # If it's very long, it's probably not a name
    if len(text) > 100:
        return True
    # If it contains multiple sentences or many punctuation marks
    if text.count('.') > 2 or text.count('，') > 2 or text.count('。') > 1:
        return True
    # If it contains numbers that look like years or references
    if re.search(r'\d{4}', text) or re.search(r'\[\d+\]', text):
        return True
    return False

def normalize_english_name(name):
    """
    Normalize an English name:
    - Trim whitespace
    - Fix capitalization (First Last format)
    - Remove extra whitespace
    - Handle special cases
    """
    if not name:
        return name
    
    # Trim and clean whitespace
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Remove trailing punctuation that shouldn't be in names
    name = re.sub(r'[?.,;:!]+$', '', name)
    
    # Skip if it looks like a bio
    if is_likely_bio_or_description(name):
        return None  # Return None to indicate it should be cleared
    
    # Remove titles/job descriptions that might be mixed in (e.g., "Founder & CEO")
    # But be careful - some names might legitimately contain these
    # Only remove if it's clearly a title pattern at the end
    # Check if name contains title-like patterns
    original_name = name
    
    # First, handle Chinese comma (，) - often used before titles
    if '，' in name:
        # Split by Chinese comma and take only the first part (the name)
        parts = name.split('，')
        if len(parts) > 1:
            # Check if the part after comma looks like a title
            after_comma = parts[1].strip().lower()
            title_keywords = ['founder', 'ceo', 'cto', 'scientist', 'engineer', 'aws', 'research', 'director']
            if any(keyword in after_comma for keyword in title_keywords):
                name = parts[0].strip()
    
    # Remove title patterns at the end
    title_patterns = [
        r'\s+(Founder|CEO|CTO|COO|CPO|CMO|VP|President|Director|Manager|Engineer|Scientist|Professor|Entrepreneur|Research).*$',
        r'\s+企业家.*$',
        r'\s+连续创业者.*$',
    ]
    for pattern in title_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # If we removed a lot, make sure we still have a reasonable name
    if len(name.strip()) < 2:
        # Probably removed too much, restore original but clean it differently
        name = original_name
        # Just remove trailing punctuation and titles more carefully
        name = re.sub(r'[，,]\s*(Founder|CEO|CTO|Scientist|Engineer|aws|Research).*$', '', name, flags=re.IGNORECASE)
    
    # Handle comma-separated names (e.g., "Haoru, Xue" -> "Haoru Xue")
    # But be careful - "Last, First" is common, but we want "First Last"
    if ',' in name and not '(' in name:  # Don't mess with parenthetical names
        parts = [p.strip() for p in name.split(',')]
        # If it looks like "Last, First" format (single word last name, single word first name), reverse it
        if len(parts) == 2:
            last_part = parts[0]
            first_part = parts[1]
            # If first part is a single word and second part is a single word, likely "Last, First"
            if len(last_part.split()) == 1 and len(first_part.split()) == 1:
                name = f"{first_part} {last_part}"
            else:
                # Otherwise, just join with space
                name = ' '.join(parts)
        else:
            name = ' '.join(parts)
    
    # Handle names with parentheses (e.g., "Kelly (许润沁) Xu")
    # Keep the format but fix capitalization, preserving spacing
    if '(' in name and ')' in name:
        # Find all parenthetical content
        def replace_paren(match):
            inner = match.group(1)
            # Normalize inner content (preserve Chinese characters)
            if has_chinese_characters(inner):
                normalized_inner = inner  # Keep Chinese as-is
            else:
                normalized_inner = normalize_name_part(inner)
            return '(' + normalized_inner + ')'
        
        # Replace parenthetical content
        result = re.sub(r'\(([^)]+)\)', replace_paren, name)
        
        # Normalize parts outside parentheses
        # Split by parentheses but preserve them
        parts = re.split(r'(\([^)]+\))', result)
        normalized_parts = []
        for part in parts:
            if part.startswith('(') and part.endswith(')'):
                # Keep parentheses as-is
                normalized_parts.append(part)
            elif part.strip():
                # Normalize words outside parentheses
                words = part.split()
                normalized_words = []
                for word in words:
                    # Preserve common acronyms
                    if word.upper() in ['CEO', 'CTO', 'COO', 'CPO', 'CMO', 'VP', 'AI', 'AWS']:
                        normalized_words.append(word.upper())
                    else:
                        normalized_words.append(normalize_name_part(word))
                normalized_parts.append(' '.join(normalized_words))
        
        # Join and clean up extra spaces
        final = ' '.join(normalized_parts)
        return re.sub(r'\s+', ' ', final).strip()
    
    # Split into words and capitalize each word
    words = name.split()
    normalized_words = []
    
    for word in words:
        # Skip empty words
        if not word:
            continue
        
        # Preserve common acronyms
        if word.upper() in ['CEO', 'CTO', 'COO', 'CPO', 'CMO', 'VP', 'AI', 'AWS']:
            normalized_words.append(word.upper())
        # Handle special prefixes like "Dr.", "Mr.", etc.
        elif word.lower().endswith('.') and len(word) <= 4:
            normalized_words.append(word.capitalize())
        else:
            # Capitalize first letter, lowercase rest
            normalized_words.append(word.capitalize())
    
    return ' '.join(normalized_words)

def normalize_name_part(part):
    """Normalize a part of a name"""
    if not part:
        return part
    # Capitalize first letter, lowercase rest
    return part.capitalize()

def normalize_chinese_name(name):
    """Normalize a Chinese name - mainly trim whitespace"""
    if not name:
        return name
    # Just trim and clean whitespace for Chinese names
    return re.sub(r'\s+', ' ', name.strip())

# Get all records
print("Fetching all records from Airtable...")
records = table.all()

print(f"\nTotal records: {len(records)}\n")
print("=" * 80)

# Analyze and prepare updates
updates_needed = []

for record in records:
    fields = record['fields']
    chinese_name_orig = fields.get('您的姓名', '').strip() if fields.get('您的姓名') else ''
    english_name_orig = fields.get('别名/英文名', '').strip() if fields.get('别名/英文名') else ''
    
    chinese_name_fixed = chinese_name_orig
    english_name_fixed = english_name_orig
    needs_update = False
    update_reason = []
    
    # Check if English name is in Chinese column
    if chinese_name_orig and is_likely_english_name(chinese_name_orig) and not has_chinese_characters(chinese_name_orig):
        # Move to English column
        if not english_name_orig:
            english_name_fixed = normalize_english_name(chinese_name_orig)
            chinese_name_fixed = ''
            needs_update = True
            update_reason.append(f"Moved English name from Chinese column: '{chinese_name_orig}'")
        else:
            # Both filled - keep English in English column, clear Chinese
            english_name_fixed = normalize_english_name(chinese_name_orig) if not english_name_fixed else normalize_english_name(english_name_fixed)
            chinese_name_fixed = ''
            needs_update = True
            update_reason.append(f"Moved English name from Chinese column (English already existed)")
    
    # Check if Chinese name is in English column
    if english_name_orig and has_chinese_characters(english_name_orig):
        # Move to Chinese column
        if not chinese_name_orig:
            chinese_name_fixed = normalize_chinese_name(english_name_orig)
            english_name_fixed = ''
            needs_update = True
            update_reason.append(f"Moved Chinese name from English column: '{english_name_orig}'")
        else:
            # Both filled - keep Chinese in Chinese column, clear English
            chinese_name_fixed = normalize_chinese_name(english_name_orig) if not chinese_name_fixed else normalize_chinese_name(chinese_name_fixed)
            english_name_fixed = ''
            needs_update = True
            update_reason.append(f"Moved Chinese name from English column (Chinese already existed)")
    
    # Check if English name looks like a bio/description
    if english_name_orig and is_likely_bio_or_description(english_name_orig):
        english_name_fixed = ''
        needs_update = True
        update_reason.append(f"Removed bio/description from English name: '{english_name_orig[:50]}...'")
    
    # Normalize English name capitalization
    if english_name_fixed and is_likely_english_name(english_name_fixed):
        normalized = normalize_english_name(english_name_fixed)
        if normalized != english_name_fixed:
            english_name_fixed = normalized
            needs_update = True
            update_reason.append(f"Fixed capitalization: '{english_name_orig}' -> '{normalized}'")
        elif normalized is None:
            # It was a bio, clear it
            english_name_fixed = ''
            needs_update = True
            update_reason.append(f"Cleared bio content from English name")
    
    # Normalize Chinese name (trim whitespace and remove titles)
    if chinese_name_fixed:
        # Check if Chinese name contains titles/job descriptions
        original_chinese = chinese_name_fixed
        # Remove common title patterns that might be mixed in
        chinese_name_fixed = re.sub(r'\s+(企业家|连续创业者|Co-Founder|Founder|CEO|CTO).*$', '', chinese_name_fixed, flags=re.IGNORECASE)
        chinese_name_fixed = re.sub(r'\s+/\s+.*$', '', chinese_name_fixed)  # Remove content after /
        
        normalized = normalize_chinese_name(chinese_name_fixed)
        if normalized != original_chinese:
            chinese_name_fixed = normalized
            needs_update = True
            if normalized != original_chinese:
                update_reason.append(f"Cleaned Chinese name: '{original_chinese}' -> '{normalized}'")
            else:
                update_reason.append(f"Fixed whitespace in Chinese name")
    
    # Check for duplicate (same name in both columns)
    if chinese_name_fixed and english_name_fixed and chinese_name_fixed == english_name_fixed:
        # If they're the same, keep in Chinese column, clear English
        english_name_fixed = ''
        needs_update = True
        update_reason.append(f"Removed duplicate name from English column")
    
    if needs_update:
        updates_needed.append({
            'record_id': record['id'],
            'chinese_name': chinese_name_fixed,
            'english_name': english_name_fixed,
            'reasons': update_reason,
            'original_chinese': chinese_name_orig,
            'original_english': english_name_orig
        })

print(f"ANALYSIS COMPLETE:")
print("=" * 80)
print(f"Records needing updates: {len(updates_needed)}\n")

# Show sample updates
if updates_needed:
    print("SAMPLE UPDATES (first 20):")
    print("=" * 80)
    for i, update in enumerate(updates_needed[:20], 1):
        print(f"\n{i}. Record ID: {update['record_id']}")
        print(f"   Reasons: {', '.join(update['reasons'])}")
        print(f"   Before: 您的姓名='{update['original_chinese']}' | 别名/英文名='{update['original_english']}'")
        print(f"   After:  您的姓名='{update['chinese_name']}' | 别名/英文名='{update['english_name']}'")
    
    if len(updates_needed) > 20:
        print(f"\n... and {len(updates_needed) - 20} more updates")

# Check for --yes flag to skip confirmation
skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

# Ask for confirmation (unless --yes flag is provided)
if not skip_confirmation:
    print("\n" + "=" * 80)
    print(f"\nFound {len(updates_needed)} records that need normalization.")
    print("This script will:")
    print("  - Move English names from Chinese column to English column")
    print("  - Move Chinese names from English column to Chinese column")
    print("  - Fix capitalization in English names")
    print("  - Remove bio/description content from name fields")
    print("  - Clean whitespace")
    print("\nDo you want to proceed? (This will update Airtable)")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")

    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
else:
    print("\n" + "=" * 80)
    print(f"\nFound {len(updates_needed)} records that need normalization.")
    print("Proceeding with normalization (--yes flag detected)...")

# Update records
print(f"\nNormalizing {len(updates_needed)} records...")
print("=" * 80)

updated_count = 0
error_count = 0

for update in updates_needed:
    try:
        update_fields = {}
        
        # Only update fields that changed
        if update['chinese_name'] != update['original_chinese']:
            update_fields['您的姓名'] = update['chinese_name'] if update['chinese_name'] else ''
        
        if update['english_name'] != update['original_english']:
            update_fields['别名/英文名'] = update['english_name'] if update['english_name'] else ''
        
        if update_fields:
            table.update(update['record_id'], update_fields)
            updated_count += 1
            if updated_count % 50 == 0:
                print(f"  Progress: {updated_count}/{len(updates_needed)} records updated...")
    except Exception as e:
        error_count += 1
        print(f"  Error updating record {update['record_id']}: {e}")

print("\n" + "=" * 80)
print("NORMALIZATION COMPLETE!")
print("=" * 80)
print(f"Successfully updated: {updated_count} records")
if error_count > 0:
    print(f"Errors: {error_count} records")
print(f"\nAll name fields have been normalized.")

