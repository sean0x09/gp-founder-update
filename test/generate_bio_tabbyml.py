from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize clients
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))
claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Specific record ID for 张萌 at TabbyML
record_id = 'recouBYBaOW1GHWk1'

# Get the specific record
record = table.get(record_id)
fields = record['fields']

name = fields.get('您的姓名', '')
title = fields.get('Title', '')
company = fields.get('目前就职', '')
linkedin = fields.get('Profiles', '')

print(f"Processing: {name}")
print(f"Title: {title}")
print(f"Company: {company}")
print(f"Current Bio: {fields.get('Bio', 'None')}")
print("-" * 50)

# Generate bio with Claude
prompt = f"""Write a concise 2-sentence professional bio for:
Name: {name}
Title: {title}
Company: {company}
Keep it professional and founder-focused."""

print("Generating bio with Claude...")
message = claude.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=150,
    messages=[{"role": "user", "content": prompt}]
)

bio = message.content[0].text
print(f"\nGenerated Bio:\n{bio}\n")

# Update Airtable
table.update(record_id, {
    'Bio': bio
})

print(f"✓ Successfully updated bio for {name}")

