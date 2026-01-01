from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Try a simple test with a common model
try:
    message = claude.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("✓ API key works!")
    print(f"Response: {message.content[0].text}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")

