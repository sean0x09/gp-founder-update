from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Search for David Ha
print("Searching for David Ha in Airtable...")
records = table.all()

david_ha = None
for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '')
    
    # Check if name matches David Ha (case insensitive, handle variations)
    if name and ('david' in name.lower() and 'ha' in name.lower()):
        david_ha = {
            'record_id': record['id'],
            'name': name,
            'title': fields.get('Title', ''),
            'company': fields.get('目前就职', ''),
            'linkedin': fields.get('Profiles', ''),
            'current_bio': fields.get('Bio', ''),
            'all_fields': fields
        }
        break

if not david_ha:
    print("❌ Could not find David Ha in the table")
    exit(1)

print(f"\n✓ Found David Ha!")
print(f"Name: {david_ha['name']}")
print(f"Title: {david_ha['title']}")
print(f"Company: {david_ha['company']}")
print(f"LinkedIn: {david_ha['linkedin']}")
print(f"Current Bio: {david_ha['current_bio'] or 'None'}")
print("-" * 50)

# Generated bio based on research:
# - Co-Founder and CEO of Sakana AI
# - Previously led Google Brain Research team in Japan
# - Former head of research at Stability AI
# - Former Managing Director at Goldman Sachs
# - PhD from University of Tokyo
# - Research interests in complex self-organizing systems and AI advancement

bio = "David Ha is the Co-Founder and CEO of Sakana AI, where he leads research on complex self-organizing systems and the self-advancement of artificial intelligence. Previously, he led the Google Brain Research team in Japan and served as head of research at Stability AI, bringing deep expertise from his background that spans AI research, quantitative finance, and complex systems."

print(f"\nGenerated Bio:\n{bio}\n")

# Update Airtable
table.update(david_ha['record_id'], {
    'Bio': bio
})

print(f"✓ Successfully updated bio for {david_ha['name']}")

