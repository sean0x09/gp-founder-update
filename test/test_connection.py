from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

api = Api(os.getenv('AIRTABLE_TOKEN'))
table = api.table(os.getenv('AIRTABLE_BASE_ID'), os.getenv('AIRTABLE_TABLE_ID'))

# Read first 5 records
records = table.all(max_records=5)
for record in records:
    print(f"Record ID: {record['id']}")
    print(f"Fields: {record['fields']}")
    print("-" * 50)

