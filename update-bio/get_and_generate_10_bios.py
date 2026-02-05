#!/usr/bin/env python3
"""
Script to get 10 names from Airtable that don't have bios, and generate bios for them.
"""

from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
import subprocess

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Check for required environment variables
airtable_token = os.getenv('AIRTABLE_TOKEN')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
airtable_table_id = os.getenv('AIRTABLE_TABLE_ID')

if not airtable_token or not airtable_base_id or not airtable_table_id:
    print("❌ Error: Missing required environment variables")
    sys.exit(1)

# Initialize Airtable client
airtable_api = Api(airtable_token)
table = airtable_api.table(airtable_base_id, airtable_table_id)

# Get all records
print("Fetching records from Airtable...")
records = table.all()
print(f"Total records: {len(records)}\n")

# Find records without bios
records_without_bios = []
for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '').strip()
    bio = fields.get('Bio', '').strip()
    
    # Skip if no name or if bio already exists
    if not name or bio:
        continue
    
    records_without_bios.append({
        'name': name,
        'title': fields.get('Title', '').strip(),
        'company': fields.get('目前就职', '').strip(),
    })

print(f"Found {len(records_without_bios)} records without bios")
print(f"Selecting 10 to process...\n")

# Get first 10
names_to_process = [r['name'] for r in records_without_bios[:10]]

if not names_to_process:
    print("❌ No records found without bios")
    sys.exit(1)

print("Names to process:")
for i, name in enumerate(names_to_process, 1):
    print(f"  {i}. {name}")
print()

# Call generate_bio.py with these names
script_path = os.path.join(os.path.dirname(__file__), 'generate_bio.py')
cmd = [sys.executable, script_path] + names_to_process + ['--yes']

print("Running generate_bio.py for these names...\n")
subprocess.run(cmd)

