import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key is not None}")
if api_key:
    print(f"API Key prefix: {api_key[:15]}...")
else:
    print("ERROR: No API key found in .env file")
    exit(1)

# Test with direct Google GenAI SDK
try:
    import google.generativeai as genai
    
    # Configure
    genai.configure(api_key=api_key)
    
    # List available models
    print("\n📋 Available models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  ✓ {model.name}")
    
    # Test with a simple prompt
    print("\n🧪 Testing model...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say 'Hello, I am working!'")
    print(f"✅ Response: {response.text}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install google-generativeai")
    
except Exception as e:
    print(f"❌ Error: {e}")