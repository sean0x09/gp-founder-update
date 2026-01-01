from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import re

load_dotenv()

# Initialize Airtable client
airtable_api = Api(os.getenv('AIRTABLE_TOKEN'))
table = airtable_api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Path to profile images folder
PROFILE_IMAGES_DIR = Path('/Users/yizeshen/Desktop/profile-images')

def normalize_name(name):
    """
    Normalize a name for matching by:
    - Removing extra whitespace
    - Converting to lowercase
    - Removing special characters that might interfere
    """
    if not name:
        return ""
    # Remove extra whitespace and convert to lowercase
    normalized = re.sub(r'\s+', ' ', str(name).strip()).lower()
    return normalized

def extract_name_from_filename(filename):
    """
    Extract a name from a filename by removing the extension and cleaning it up.
    Handles cases like:
    - "David Ha.png" -> "David Ha"
    - "Chuyue (Livia) Sun.png" -> "Chuyue (Livia) Sun" or "Chuyue Sun"
    - "Bolbi Liu 硅谷创业者 AdsGency AI CEO .png" -> "Bolbi Liu"
    """
    # Remove file extension
    name = Path(filename).stem
    
    # Remove trailing/leading spaces
    name = name.strip()
    
    # Try to extract just the name part if there's extra info
    # Look for patterns like "Name 额外信息" or "Name (info)"
    # For now, we'll try to match the first part before any long extra text
    # But keep parentheses content as it might be part of the name
    
    return name

def find_matching_record(image_name, records):
    """
    Find a matching Airtable record for an image filename.
    Returns the record if found, None otherwise.
    """
    # Normalize the image name
    image_normalized = normalize_name(extract_name_from_filename(image_name))
    
    # Try exact match first
    for record in records:
        airtable_name = record['fields'].get('您的姓名', '')
        if not airtable_name:
            continue
        
        airtable_normalized = normalize_name(airtable_name)
        
        # Exact match
        if image_normalized == airtable_normalized:
            return record
        
        # Check if image name contains airtable name or vice versa
        if image_normalized in airtable_normalized or airtable_normalized in image_normalized:
            return record
        
        # Try matching without parentheses content
        image_no_parens = re.sub(r'\s*\([^)]+\)\s*', ' ', image_normalized).strip()
        airtable_no_parens = re.sub(r'\s*\([^)]+\)\s*', ' ', airtable_normalized).strip()
        
        if image_no_parens == airtable_no_parens:
            return record
        
        # Try matching first and last name parts
        # Split by spaces and check if key parts match
        image_parts = set(image_normalized.split())
        airtable_parts = set(airtable_normalized.split())
        
        # If there's significant overlap (at least 2 words match, or 1 word if it's long)
        common_parts = image_parts & airtable_parts
        if len(common_parts) >= 2 or (len(common_parts) == 1 and len(list(common_parts)[0]) > 4):
            return record
    
    return None

def main():
    # Check for flags
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    overwrite = '--overwrite' in sys.argv or '-o' in sys.argv
    
    # Get all image files
    print("Scanning profile images folder...")
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
        image_files.extend(PROFILE_IMAGES_DIR.glob(ext))
        image_files.extend(PROFILE_IMAGES_DIR.glob(ext.upper()))
    
    print(f"Found {len(image_files)} image files")
    
    # Get all records from Airtable
    print("\nFetching all records from Airtable...")
    records = table.all()
    print(f"Found {len(records)} records in Airtable")
    
    # Build a list of records with names for matching
    records_with_names = [r for r in records if r['fields'].get('您的姓名')]
    print(f"Found {len(records_with_names)} records with names")
    
    # Match images to records
    print("\nMatching images to records...")
    matches = []
    unmatched_images = []
    
    for image_file in image_files:
        match = find_matching_record(image_file.name, records_with_names)
        if match:
            matches.append({
                'image_path': image_file,
                'record': match,
                'name': match['fields'].get('您的姓名')
            })
        else:
            unmatched_images.append(image_file.name)
    
    print(f"\nMatched {len(matches)} images to records")
    print(f"Unmatched images: {len(unmatched_images)}")
    
    if unmatched_images:
        print("\nUnmatched images (first 20):")
        for img in unmatched_images[:20]:
            print(f"  - {img}")
        if len(unmatched_images) > 20:
            print(f"  ... and {len(unmatched_images) - 20} more")
    
    if not matches:
        print("\nNo matches found. Exiting.")
        return
    
    # Show preview of matches
    print("\n\nPreview of matches (first 10):")
    print("=" * 80)
    for i, match in enumerate(matches[:10], 1):
        print(f"{i}. {match['image_path'].name} -> {match['name']}")
    
    if len(matches) > 10:
        print(f"\n... and {len(matches) - 10} more matches")
    
    # Ask for confirmation
    if not skip_confirmation:
        print("\n" + "=" * 80)
        print(f"\nReady to upload {len(matches)} profile images to Airtable.")
        print("This will update the 'Profile Picture' column for matched records.")
        if overwrite:
            print("Note: --overwrite flag is set, existing profile pictures will be replaced.")
        print("\nDo you want to proceed? (This will update Airtable)")
        print("Tip: Use --yes or -y flag to skip confirmation")
        print("Tip: Use --overwrite or -o flag to replace existing profile pictures")
        response = input("Type 'yes' to proceed, anything else to cancel: ")
        
        if response.lower() != 'yes':
            print("\nOperation cancelled.")
            return
    else:
        print("\n" + "=" * 80)
        print(f"\nProceeding with upload of {len(matches)} images (--yes flag detected)...")
    
    # Upload images
    print("\n" + "=" * 80)
    print("Uploading profile images...")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, match in enumerate(matches, 1):
        try:
            record_id = match['record']['id']
            image_path = match['image_path']
            name = match['name']
            
            # Check if record already has a profile picture
            existing_picture = match['record']['fields'].get('Profile Picture', [])
            if existing_picture and not overwrite:
                print(f"[{i}/{len(matches)}] Skipping {name} - already has profile picture (use --overwrite to replace)")
                skipped_count += 1
                continue
            
            # Upload the attachment
            print(f"[{i}/{len(matches)}] Uploading {image_path.name} for {name}...")
            table.upload_attachment(record_id, 'Profile Picture', image_path)
            success_count += 1
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(matches)} images processed...")
                
        except Exception as e:
            error_count += 1
            print(f"  Error uploading {match['image_path'].name} for {match['name']}: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE!")
    print("=" * 80)
    print(f"Successfully uploaded: {success_count} images")
    print(f"Skipped (already had picture): {skipped_count} records")
    if error_count > 0:
        print(f"Errors: {error_count} images")
    if unmatched_images:
        print(f"\nNote: {len(unmatched_images)} images could not be matched to records")

if __name__ == '__main__':
    main()

