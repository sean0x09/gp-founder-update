#!/usr/bin/env python3
"""
Universal bio generator script for Airtable records.
Usage: python generate_bio.py "Person Name" [--yes]
       python generate_bio.py "Name1" "Name2" "Name3" [--yes]
"""

from pyairtable import Api
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import sys
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

# Load environment variables from parent directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Check for required environment variables
airtable_token = os.getenv('AIRTABLE_TOKEN')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
airtable_table_id = os.getenv('AIRTABLE_TABLE_ID')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if not airtable_token:
    print("❌ Error: AIRTABLE_TOKEN not found in environment variables")
    print("   Please set it in your .env file or environment")
    sys.exit(1)
if not airtable_base_id:
    print("❌ Error: AIRTABLE_BASE_ID not found in environment variables")
    print("   Please set it in your .env file or environment")
    sys.exit(1)
if not airtable_table_id:
    print("❌ Error: AIRTABLE_TABLE_ID not found in environment variables")
    print("   Please set it in your .env file or environment")
    sys.exit(1)
if not anthropic_key:
    print("❌ Error: ANTHROPIC_API_KEY not found in environment variables")
    print("   Please set it in your .env file or environment")
    sys.exit(1)

# Initialize clients
airtable_api = Api(airtable_token)
table = airtable_api.table(airtable_base_id, airtable_table_id)
claude = Anthropic(api_key=anthropic_key)

def find_person_in_airtable(name):
    """Search for a person in Airtable by name."""
    records = table.all()
    
    # Try exact match first
    for record in records:
        fields = record['fields']
        record_name = fields.get('您的姓名', '').strip()
        if record_name and name.strip() == record_name:
            return {
                'record_id': record['id'],
                'name': record_name,
                'title': fields.get('Title', '').strip(),
                'company': fields.get('目前就职', '').strip(),
                'linkedin': fields.get('Profiles', '').strip(),
                'current_bio': fields.get('Bio', '').strip(),
                'all_fields': fields
            }
    
    # Try partial match (name contains search term or vice versa)
    name_lower = name.strip().lower()
    for record in records:
        fields = record['fields']
        record_name = fields.get('您的姓名', '').strip()
        if record_name:
            record_name_lower = record_name.lower()
            if name_lower in record_name_lower or record_name_lower in name_lower:
                return {
                    'record_id': record['id'],
                    'name': record_name,
                    'title': fields.get('Title', '').strip(),
                    'company': fields.get('目前就职', '').strip(),
                    'linkedin': fields.get('Profiles', '').strip(),
                    'current_bio': fields.get('Bio', '').strip(),
                    'all_fields': fields
                }
    
    return None

def search_online(person):
    """Perform web search for the person."""
    search_terms = [person['name']]
    if person['company']:
        search_terms.append(person['company'])
    if person['title']:
        search_terms.append(person['title'])
    
    search_query = " ".join(search_terms)
    print(f"  Searching online for: {search_query}")
    
    web_search_results = ""
    if HAS_DDG:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=10))
                if results:
                    web_search_results = "\n\nOnline search results:\n"
                    for idx, result in enumerate(results[:10], 1):
                        web_search_results += f"{idx}. {result.get('title', '')}\n"
                        web_search_results += f"   {result.get('body', '')}\n"
                        web_search_results += f"   URL: {result.get('href', '')}\n\n"
                    print(f"  ✓ Found {len(results)} search results")
                else:
                    print(f"  ⚠ No search results found")
        except Exception as e:
            print(f"  ⚠ Warning: Web search failed: {e}")
            web_search_results = ""
    else:
        print(f"  ⚠ Skipping web search (library not installed)")
    
    return web_search_results

def generate_bio(person, web_search_results):
    """Generate bio using Claude."""
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
    
    # Create prompt for Claude
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

    print("  Generating bio with Claude...")
    
    # Try different Claude models
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
    
    return bio

def process_person(name, auto_confirm=False):
    """Process a single person: find, search, generate bio, and update."""
    print(f"\n{'='*80}")
    print(f"Processing: {name}")
    print(f"{'='*80}")
    
    # Find person in Airtable
    person = find_person_in_airtable(name)
    
    if not person:
        print(f"❌ Could not find '{name}' in the table")
        return False
    
    print(f"\n✓ Found {person['name']}!")
    print(f"  Name: {person['name']}")
    print(f"  Title: {person['title']}")
    print(f"  Company: {person['company']}")
    print(f"  LinkedIn: {person['linkedin']}")
    print(f"  Current Bio: {person['current_bio'] or 'None'}")
    
    # Search online
    web_search_results = search_online(person)
    
    # Generate bio
    try:
        bio = generate_bio(person, web_search_results)
        
        print(f"\n{'='*80}")
        print("GENERATED BIO:")
        print(f"{'='*80}")
        print(bio)
        print(f"{'='*80}\n")
        
        # Ask for confirmation (unless --yes flag)
        if not auto_confirm:
            print(f"This will update the Bio column for {person['name']} in Airtable.")
            response = input("Type 'yes' to proceed, anything else to cancel: ")
            if response.lower() != 'yes':
                print("\nOperation cancelled.")
                return False
        
        # Update Airtable
        table.update(person['record_id'], {
            'Bio': bio
        })
        
        print(f"✓ Successfully updated bio for {person['name']}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error generating bio: {e}")
        return False

def main():
    """Main function."""
    # Parse command line arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    flags = [arg for arg in sys.argv[1:] if arg.startswith('--')]
    
    auto_confirm = '--yes' in flags or '-y' in flags
    
    if not args:
        print("Usage: python generate_bio.py \"Person Name\" [--yes]")
        print("       python generate_bio.py \"Name1\" \"Name2\" \"Name3\" [--yes]")
        print("\nOptions:")
        print("  --yes, -y    Skip confirmation prompt")
        sys.exit(1)
    
    # Process each name
    success_count = 0
    total_count = len(args)
    
    for name in args:
        if process_person(name, auto_confirm=auto_confirm):
            success_count += 1
        time.sleep(1)  # Rate limiting between people
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Successfully processed: {success_count}/{total_count}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

