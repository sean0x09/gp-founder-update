# Bio Generator

Universal script to generate and update professional bios for people in your Airtable database.

## Features

- 🔍 Searches online for background information
- 🤖 Uses Claude AI to generate comprehensive paragraph bios
- 📝 Updates Airtable Bio column automatically
- 👥 Can process single or multiple names at once
- ✅ Includes confirmation prompts (can be skipped with --yes)

## Setup

1. Make sure you have the required dependencies:
```bash
pip install pyairtable anthropic python-dotenv ddgs
```

2. Ensure your `.env` file in the project root has:
```
AIRTABLE_TOKEN=your_token
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_ID=your_table_id
ANTHROPIC_API_KEY=your_key
```

## Usage

### Single Person
```bash
python update-bio/generate_bio.py "Person Name"
```

### Multiple People
```bash
python update-bio/generate_bio.py "Name1" "Name2" "Name3"
```

### Skip Confirmation
```bash
python update-bio/generate_bio.py "Person Name" --yes
```

## Examples

```bash
# Generate bio for one person
python update-bio/generate_bio.py "龚文茂"

# Generate bios for multiple people
python update-bio/generate_bio.py "David Ha" "Louis Gong" "龚文茂"

# Generate and auto-update without confirmation
python update-bio/generate_bio.py "Person Name" --yes
```

## How It Works

1. Searches for the person in your Airtable database (by name)
2. Performs web search to gather background information
3. Uses Claude AI to generate a comprehensive paragraph bio
4. Shows you the generated bio
5. Updates the Bio column in Airtable (after confirmation)

The generated bio includes:
- Current role and company
- What they're building/working on
- Past experiences and achievements
- Key accomplishments

