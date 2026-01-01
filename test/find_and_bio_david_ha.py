from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize clients
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))
claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

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

# Prepare information for bio generation
info_parts = [f"Name: {david_ha['name']}"]
if david_ha['title']:
    info_parts.append(f"Title: {david_ha['title']}")
if david_ha['company']:
    info_parts.append(f"Company: {david_ha['company']}")

# Try to get LinkedIn information
linkedin_info = ""
if david_ha['linkedin']:
    print(f"\nFound LinkedIn URL: {david_ha['linkedin']}")
    print("Note: Cannot directly access LinkedIn, but will search online for information...")
    linkedin_info = f"LinkedIn URL: {david_ha['linkedin']}"

# Build search query for online research
search_query = f"David Ha"
if david_ha['company']:
    search_query += f" {david_ha['company']}"
if david_ha['title']:
    search_query += f" {david_ha['title']}"

print(f"\nSearching online for: {search_query}")

# Additional research information about David Ha
research_info = """
Additional background information:
- Co-Founder and CEO of Sakana AI
- Previously led Google Brain Research team in Japan as Research Scientist
- Former Managing Director and head of interest rates trading at Goldman Sachs in Japan
- Research interests include complex self-organizing systems and the self-advancement of artificial intelligence
- Holds undergraduate degree in engineering science from University of Toronto
- Holds PhD from University of Tokyo
- Previously head of research at Stability AI
"""

# Generate bio with Claude, including instruction to use web search knowledge
prompt = f"""Write a concise 2-sentence professional bio for:
{chr(10).join(info_parts)}
{linkedin_info if linkedin_info else ''}

{research_info}

Please write a professional, founder-focused bio that highlights their expertise and achievements. 
Keep it concise (exactly 2 sentences) and professional. Focus on their current role as CEO of Sakana AI and their background in AI research."""

print("\nGenerating bio with Claude...")
message = claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=200,
    messages=[{"role": "user", "content": prompt}]
)

bio = message.content[0].text.strip()
print(f"\nGenerated Bio:\n{bio}\n")

# Update Airtable
table.update(david_ha['record_id'], {
    'Bio': bio
})

print(f"✓ Successfully updated bio for {david_ha['name']}")

