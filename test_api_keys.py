"""
Test script to verify API keys are working
Run this before using the Flask app to check your API configuration
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("API Key Configuration Test")
print("=" * 60)
print()

# Check OpenAI
openai_key = os.environ.get('OPENAI_API_KEY')
print(f"OpenAI API Key: ", end="")
if openai_key:
    print(f"✓ Found (starts with: {openai_key[:10]}...)")

    # Test OpenAI connection
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)

        # Try a simple test
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
            max_tokens=10
        )
        print(f"   OpenAI Test: ✓ SUCCESS - Response: {response.choices[0].message.content}")
    except ImportError:
        print("   OpenAI Test: ⚠ Library not installed (pip install openai)")
    except Exception as e:
        print(f"   OpenAI Test: ✗ FAILED - {str(e)}")
else:
    print("✗ Not found in .env file")

print()

# Check Anthropic
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
print(f"Anthropic API Key: ", end="")
if anthropic_key:
    print(f"✓ Found (starts with: {anthropic_key[:10]}...)")

    # Test Anthropic connection
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)

        # Try a simple test
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'Hello' in one word"}]
        )
        print(f"   Anthropic Test: ✓ SUCCESS - Response: {message.content[0].text}")
    except ImportError:
        print("   Anthropic Test: ⚠ Library not installed (pip install anthropic)")
    except Exception as e:
        print(f"   Anthropic Test: ✗ FAILED - {str(e)}")
else:
    print("✗ Not found in .env file")

print()
print("=" * 60)
print("Recommendations:")
print("=" * 60)

if not openai_key and not anthropic_key:
    print("⚠ No API keys found in .env file!")
    print()
    print("To fix this:")
    print("1. Open the .env file in the project root")
    print("2. Add your API key(s):")
    print("   OPENAI_API_KEY=sk-your-key-here")
    print("   ANTHROPIC_API_KEY=sk-ant-your-key-here")
    print("3. Save the file and restart the Flask app")
elif openai_key or anthropic_key:
    print("✓ At least one API key is configured!")
    print()
    print("You can now:")
    print("1. Start the Flask app: python app.py")
    print("2. Go to AI Assistant page")
    print("3. Test the AI enhancement feature")

print()
