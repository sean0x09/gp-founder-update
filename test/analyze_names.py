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

# Analyze 您的姓名 (Your Name) column
print("ANALYZING '您的姓名' (Your Name) COLUMN:")
print("=" * 80)

chinese_names = []
chinese_name_counts = Counter()
empty_chinese = 0

for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '')
    
    if not name or not isinstance(name, str) or not name.strip():
        empty_chinese += 1
        continue
    
    name_clean = name.strip()
    chinese_names.append({
        'name': name_clean,
        'record_id': record['id']
    })
    chinese_name_counts[name_clean] += 1

print(f"Records with names: {len(chinese_names)}")
print(f"Records without names: {empty_chinese}")
print(f"Unique name values: {len(chinese_name_counts)}\n")

# Show issues with Chinese names
print("SAMPLE NAMES (first 30):")
for name, count in chinese_name_counts.most_common(30):
    print(f"  '{name}': {count} occurrences")

# Analyze 别名/英文名 (Alias/English Name) column
print("\n\nANALYZING '别名/英文名' (Alias/English Name) COLUMN:")
print("=" * 80)

english_names = []
english_name_counts = Counter()
empty_english = 0

for record in records:
    fields = record['fields']
    english_name = fields.get('别名/英文名', '')
    
    if not english_name or not isinstance(english_name, str) or not english_name.strip():
        empty_english += 1
        continue
    
    english_name_clean = english_name.strip()
    english_names.append({
        'name': english_name_clean,
        'chinese_name': fields.get('您的姓名', 'Unknown'),
        'record_id': record['id']
    })
    english_name_counts[english_name_clean] += 1

print(f"Records with English names: {len(english_names)}")
print(f"Records without English names: {empty_english}")
print(f"Unique English name values: {len(english_name_counts)}\n")

# Show issues with English names
print("SAMPLE ENGLISH NAMES (first 30):")
for name, count in english_name_counts.most_common(30):
    print(f"  '{name}': {count} occurrences")

# Look for patterns and issues
print("\n\nIDENTIFYING ISSUES:")
print("=" * 80)

# Check for names with extra whitespace
whitespace_issues = []
for name_data in chinese_names + english_names:
    name = name_data['name']
    if name != name.strip() or '  ' in name or '\t' in name or '\n' in name:
        whitespace_issues.append(name_data)

if whitespace_issues:
    print(f"\nFound {len(whitespace_issues)} names with whitespace issues")
    for issue in whitespace_issues[:10]:
        print(f"  '{issue['name']}' (has extra whitespace)")

# Check for inconsistent capitalization in English names
capitalization_issues = []
for name_data in english_names:
    name = name_data['name']
    # Check if it's likely an English name (contains Latin letters)
    if re.search(r'[a-zA-Z]', name):
        # Check if it's not properly capitalized (should be "First Last" format)
        words = name.split()
        if len(words) >= 2:
            # Check if first letter of each word is not capitalized
            if any(word and not word[0].isupper() for word in words):
                capitalization_issues.append(name_data)

if capitalization_issues:
    print(f"\nFound {len(capitalization_issues)} English names with capitalization issues")
    for issue in capitalization_issues[:10]:
        print(f"  '{issue['name']}' (improper capitalization)")

# Check for names that might be in wrong column
print("\n\nCHECKING FOR NAMES IN WRONG COLUMNS:")
print("=" * 80)

# English names in Chinese column
english_in_chinese = []
for record in records:
    fields = record['fields']
    chinese_name = fields.get('您的姓名', '')
    if chinese_name and re.search(r'^[a-zA-Z\s]+$', chinese_name.strip()) and not any('\u4e00' <= char <= '\u9fff' for char in chinese_name):
        english_in_chinese.append({
            'record_id': record['id'],
            'chinese_name': chinese_name,
            'english_name': fields.get('别名/英文名', '')
        })

if english_in_chinese:
    print(f"\nFound {len(english_in_chinese)} records with English names in Chinese name column:")
    for item in english_in_chinese[:10]:
        print(f"  您的姓名: '{item['chinese_name']}' | 别名/英文名: '{item['english_name']}'")

# Chinese names in English column
chinese_in_english = []
for record in records:
    fields = record['fields']
    english_name = fields.get('别名/英文名', '')
    if english_name and any('\u4e00' <= char <= '\u9fff' for char in english_name):
        chinese_in_english.append({
            'record_id': record['id'],
            'chinese_name': fields.get('您的姓名', ''),
            'english_name': english_name
        })

if chinese_in_english:
    print(f"\nFound {len(chinese_in_english)} records with Chinese names in English name column:")
    for item in chinese_in_english[:10]:
        print(f"  您的姓名: '{item['chinese_name']}' | 别名/英文名: '{item['english_name']}'")

# Check for duplicate entries (same name in both columns)
duplicates = []
for record in records:
    fields = record['fields']
    chinese_name = fields.get('您的姓名', '').strip()
    english_name = fields.get('别名/英文名', '').strip()
    
    if chinese_name and english_name and chinese_name == english_name:
        duplicates.append({
            'record_id': record['id'],
            'name': chinese_name
        })

if duplicates:
    print(f"\nFound {len(duplicates)} records with same name in both columns:")
    for item in duplicates[:10]:
        print(f"  '{item['name']}' appears in both columns")

# Check for names with special characters or formatting issues
formatting_issues = []
for name_data in chinese_names + english_names:
    name = name_data['name']
    # Check for unusual characters or patterns
    if re.search(r'[^\w\s\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', name):
        # Allow common punctuation but flag unusual ones
        if not re.search(r'^[\w\s\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\-\'\.]+$', name):
            formatting_issues.append(name_data)

if formatting_issues:
    print(f"\nFound {len(formatting_issues)} names with unusual formatting:")
    for issue in formatting_issues[:10]:
        print(f"  '{issue['name']}'")

# Check for empty vs filled patterns
print("\n\nCOLUMN FILL PATTERNS:")
print("=" * 80)

both_filled = 0
only_chinese = 0
only_english = 0
neither = 0

for record in records:
    fields = record['fields']
    chinese_name = fields.get('您的姓名', '').strip()
    english_name = fields.get('别名/英文名', '').strip()
    
    if chinese_name and english_name:
        both_filled += 1
    elif chinese_name:
        only_chinese += 1
    elif english_name:
        only_english += 1
    else:
        neither += 1

print(f"Both columns filled: {both_filled}")
print(f"Only Chinese name filled: {only_chinese}")
print(f"Only English name filled: {only_english}")
print(f"Neither filled: {neither}")

print("\n" + "=" * 80)
print("Analysis complete!")

