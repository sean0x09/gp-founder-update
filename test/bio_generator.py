from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Initialize clients
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))
claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Get records without bios
records = table.all()

for record in records:
    fields = record['fields']
    
    # Skip if bio already exists
    if fields.get('Bio'):
        continue
    
    name = fields.get('您的姓名', '')
    title = fields.get('Title', '')
    company = fields.get('目前就职', '')
    linkedin = fields.get('Profiles', '')
    
    # Skip if no name
    if not name:
        continue
    
    # Generate bio with Claude
    prompt = f"""Write a concise 2-sentence professional bio for:
Name: {name}
Title: {title}
Company: {company}
Keep it professional and founder-focused."""
    
    try:
        message = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        
        bio = message.content[0].text
        
        # Update Airtable
        table.update(record['id'], {
            'Bio': bio
        })
        
        print(f"✓ Generated bio for {name}")
        time.sleep(1)  # Rate limiting
    except Exception as e:
        print(f"✗ Error processing {name}: {e}")
        time.sleep(1)

