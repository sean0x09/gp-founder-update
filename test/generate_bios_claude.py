from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import time
import sys

try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False
    print("Warning: duckduckgo-search not installed. Install with: pip install duckduckgo-search")
    print("The script will still work but won't perform web searches.")

load_dotenv()

# Initialize clients
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))
claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Command line arguments
skip_existing = '--skip-existing' in sys.argv or '--skip' in sys.argv
update_all = '--all' in sys.argv
dry_run = '--dry-run' in sys.argv

# Get all records
print("Fetching all records from Airtable...")
records = table.all()
print(f"Total records: {len(records)}\n")

# Filter records to process
records_to_process = []
for record in records:
    fields = record['fields']
    name = fields.get('您的姓名', '').strip()
    
    # Skip if no name
    if not name:
        continue
    
    # Check if bio exists
    existing_bio = fields.get('Bio', '').strip()
    
    if skip_existing and existing_bio:
        continue
    
    records_to_process.append({
        'record_id': record['id'],
        'name': name,
        'title': fields.get('Title', '').strip(),
        'company': fields.get('目前就职', '').strip(),
        'linkedin': fields.get('Profiles', '').strip(),
        'existing_bio': existing_bio
    })

print(f"Records to process: {len(records_to_process)}")
if skip_existing:
    print("(Skipping records with existing bios)")
if dry_run:
    print("(DRY RUN MODE - No updates will be made)")
print("=" * 80)

# Ask for confirmation unless --yes flag is provided
if not dry_run and '--yes' not in sys.argv and '-y' not in sys.argv:
    print(f"\nThis will generate and update bios for {len(records_to_process)} records.")
    print("This will search online for each person and may take a while.")
    print("Tip: Use --yes or -y flag to skip confirmation")
    response = input("Type 'yes' to proceed, anything else to cancel: ")
    
    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        exit(0)

# Process records
success_count = 0
error_count = 0

for i, person in enumerate(records_to_process, 1):
    print(f"\n[{i}/{len(records_to_process)}] Processing: {person['name']}")
    
    # Build search query
    search_terms = [person['name']]
    if person['company']:
        search_terms.append(person['company'])
    if person['title']:
        search_terms.append(person['title'])
    
    search_query = " ".join(search_terms)
    print(f"  Searching online for: {search_query}")
    
    # Perform web search to gather information
    web_search_results = ""
    if HAS_DDG:
        try:
            with DDGS() as ddgs:
                # Search for the person
                results = list(ddgs.text(search_query, max_results=5))
                if results:
                    web_search_results = "\n\nOnline search results:\n"
                    for idx, result in enumerate(results[:5], 1):
                        web_search_results += f"{idx}. {result.get('title', '')}\n"
                        web_search_results += f"   {result.get('body', '')}\n"
                        web_search_results += f"   URL: {result.get('href', '')}\n\n"
                    print(f"  Found {len(results)} search results")
                else:
                    print(f"  No search results found")
        except Exception as e:
            print(f"  Warning: Web search failed: {e}")
            web_search_results = ""
    else:
        print(f"  Skipping web search (library not installed)")
    
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

    try:
        # Generate bio with Claude (Claude will use its knowledge and can reason about web search)
        # Using a model that has access to current information
        message = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        bio = message.content[0].text.strip()
        
        # Clean up the bio (remove quotes if Claude adds them)
        if bio.startswith('"') and bio.endswith('"'):
            bio = bio[1:-1]
        if bio.startswith("'") and bio.endswith("'"):
            bio = bio[1:-1]
        
        print(f"  Generated bio ({len(bio)} chars)")
        preview_length = min(150, len(bio))
        print(f"  Preview: {bio[:preview_length]}{'...' if len(bio) > preview_length else ''}")
        
        if not dry_run:
            # Update Airtable
            table.update(person['record_id'], {
                'Bio': bio
            })
            print(f"  ✓ Updated bio for {person['name']}")
            success_count += 1
        else:
            print(f"  [DRY RUN] Would update bio for {person['name']}")
            print(f"  Bio: {bio}")
            success_count += 1
        
        # Rate limiting - be respectful to API
        time.sleep(2)  # Longer delay since we're doing more complex generation
        
    except Exception as e:
        error_count += 1
        print(f"  ✗ Error processing {person['name']}: {e}")
        time.sleep(1)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
if dry_run:
    print(f"[DRY RUN] Would have updated: {success_count} records")
else:
    print(f"Successfully updated: {success_count} records")
if error_count > 0:
    print(f"Errors: {error_count} records")
print(f"Total processed: {len(records_to_process)} records")
print("=" * 80)
