from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Get all records
print("Fetching all records...")
records = table.all()

# Find people who work at TabbyML
tabbyml_people = []
for record in records:
    fields = record['fields']
    company = fields.get('目前就职', '')
    name = fields.get('您的姓名', '')
    
    # Check if company contains TabbyML (case insensitive)
    if company and 'tabbyml' in str(company).lower():
        tabbyml_people.append({
            'name': name,
            'company': company,
            'title': fields.get('Title', ''),
            'record_id': record['id']
        })

print(f"\nFound {len(tabbyml_people)} people working at TabbyML:\n")
for person in tabbyml_people:
    print(f"Name: {person['name']}")
    print(f"Company: {person['company']}")
    print(f"Title: {person['title']}")
    print(f"Record ID: {person['record_id']}")
    print("-" * 50)

