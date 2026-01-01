from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import time

try:
    from ddgs import DDGS
    HAS_DDG = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDG = True
    except ImportError:
        HAS_DDG = False
        print("Warning: ddgs not installed. Install with: pip install ddgs")
        print("The script will still work but won't perform web searches.")

load_dotenv()

# Check for required environment variables
airtable_token = os.getenv('AIRTABLE_TOKEN')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
airtable_table_id = os.getenv('AIRTABLE_TABLE_ID')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if not airtable_token:
    print("❌ Error: AIRTABLE_TOKEN not found in environment variables")
    print("   Please set it in your .env file or environment")
    exit(1)
if not airtable_base_id:
    print("❌ Error: AIRTABLE_BASE_ID not found in environment variables")
    print("   Please set it in your .env file or environment")
    exit(1)
if not airtable_table_id:
    print("❌ Error: AIRTABLE_TABLE_ID not found in environment variables")
    print("   Please set it in your .env file or environment")
    exit(1)
if not anthropic_key:
    print("❌ Error: ANTHROPIC_API_KEY not found in environment variables")
    print("   Please set it in your .env file or environment")
    exit(1)

# Initialize clients
airtable_api = Api(airtable_token)
table = airtable_api.table(airtable_base_id, airtable_table_id)
claude = Anthropic(api_key=anthropic_key)

# Search for 龚文茂
target_name = "龚文茂"
print(f"Searching for {target_name} in Airtable...")
records = table.all()

person = None
for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '').strip()
    
    # Check if name matches (case insensitive, handle variations)
    if name and target_name in name:
        person = {
            'record_id': record['id'],
            'name': name,
            'title': fields.get('Title', '').strip(),
            'company': fields.get('目前就职', '').strip(),
            'linkedin': fields.get('Profiles', '').strip(),
            'current_bio': fields.get('Bio', '').strip(),
            'all_fields': fields
        }
        break

if not person:
    print(f"❌ Could not find {target_name} in the table")
    exit(1)

print(f"\n✓ Found {person['name']}!")
print(f"Name: {person['name']}")
print(f"Title: {person['title']}")
print(f"Company: {person['company']}")
print(f"LinkedIn: {person['linkedin']}")
print(f"Current Bio: {person['current_bio'] or 'None'}")
print("-" * 80)

# Build search query
search_terms = [person['name']]
if person['company']:
    search_terms.append(person['company'])
if person['title']:
    search_terms.append(person['title'])

search_query = " ".join(search_terms)
print(f"\nSearching online for: {search_query}")

# Perform web search to gather information
web_search_results = ""
if HAS_DDG:
    try:
        with DDGS() as ddgs:
            # Search for the person
            results = list(ddgs.text(search_query, max_results=10))
            if results:
                web_search_results = "\n\nOnline search results:\n"
                for idx, result in enumerate(results[:10], 1):
                    web_search_results += f"{idx}. {result.get('title', '')}\n"
                    web_search_results += f"   {result.get('body', '')}\n"
                    web_search_results += f"   URL: {result.get('href', '')}\n\n"
                print(f"✓ Found {len(results)} search results")
            else:
                print(f"⚠ No search results found")
    except Exception as e:
        print(f"⚠ Warning: Web search failed: {e}")
        web_search_results = ""
else:
    print(f"⚠ Skipping web search (library not installed)")

# Build information string for Claude
info_parts = []
if person['name']:
    info_parts.append(f"Name: {person['name']}")
if person['title']:
    info_parts.append(f"Title: {person['title']}")
if person['company']:
    info_parts.append(f"Company: {person['company']}")
if person['linkedin']:
    info_parts.append(f"LinkedIn: {person['linkedin']}")

info_text = "\n".join(info_parts)

# Create prompt for Claude with web search results
prompt = f"""I need you to write a comprehensive professional bio paragraph for this person. Use the information provided below, including any web search results, to research their background, past experiences, achievements, and current work.

Basic Information:
{info_text}
{web_search_results}

Please gather and synthesize information about:
- Their current role and what they're building/working on
- Past work experiences and companies they've worked at
- Key achievements, milestones, or notable accomplishments
- Educational background (if relevant and notable)
- What makes them interesting or unique
- Their company's mission/product if they're a founder

Based on all the information above, write a comprehensive paragraph bio (3-5 sentences) that:
1. Introduces who they are and their current role/company
2. Describes what they're building or working on
3. Highlights key past experiences and achievements
4. Makes it easy for someone reading through a database to understand who they are and strike up a conversation

Style: Professional but engaging, similar to this example (but shorter - one paragraph):

"Louis Gong is the Co-Founder and CEO of OctoPaul, where he's building an AI platform for probability-based decision making with the core philosophy of 'AI for Probability'. He previously co-founded Orange Interactive, which successfully listed on China's NEEQ (stock code: 870110), and founded FlipBrand, creating the influencer brand '老海龚' which achieved over 500M RMB in GMV. His current venture OSport.AI uses LLM combined with real-time sports data to provide predictions with a 70% accuracy rate, and the platform is designed to expand into other high-uncertainty scenarios like intelligent investment advisory."

Now research and write a similar comprehensive paragraph bio for the person above:"""

print("\nGenerating bio with Claude...")
try:
    # Generate bio with Claude - try different model names
    # Try claude-3-opus first, then fall back to others
    models_to_try = [
        "claude-3-opus-20240229",
        "claude-3-5-sonnet-20241022", 
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    message = None
    last_error = None
    for model_name in models_to_try:
        try:
            print(f"  Trying model: {model_name}")
            message = claude.messages.create(
                model=model_name,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except Exception as e:
            last_error = e
            continue
    
    if message is None:
        raise Exception(f"All models failed. Last error: {last_error}")
    
    bio = message.content[0].text.strip()
    
    # Clean up the bio (remove quotes if Claude adds them)
    if bio.startswith('"') and bio.endswith('"'):
        bio = bio[1:-1]
    if bio.startswith("'") and bio.endswith("'"):
        bio = bio[1:-1]
    
    print(f"\n{'='*80}")
    print("GENERATED BIO:")
    print(f"{'='*80}")
    print(bio)
    print(f"{'='*80}\n")
    
    # Ask for confirmation
    print(f"This will update the Bio column for {person['name']} in Airtable.")
    response = input("Type 'yes' to proceed, anything else to cancel: ")
    
    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)
    
    # Update Airtable
    table.update(person['record_id'], {
        'Bio': bio
    })
    
    print(f"\n✓ Successfully updated bio for {person['name']}")
    
except Exception as e:
    print(f"\n✗ Error generating bio: {e}")
    exit(1)

