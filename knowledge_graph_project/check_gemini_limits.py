"""Check Gemini API model limits and configurations"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Get model info
model_name = "gemini-2.5-pro"
model = genai.GenerativeModel(model_name)

# Get model information
print(f"=== Gemini Model Information: {model_name} ===\n")

# Try to get model info
try:
    model_info = genai.get_model(f"models/{model_name}")
    
    print("Model Details:")
    print(f"  Name: {model_info.name}")
    print(f"  Display Name: {model_info.display_name}")
    print(f"  Description: {model_info.description}")
    
    print("\nToken Limits:")
    print(f"  Input Token Limit: {model_info.input_token_limit}")
    print(f"  Output Token Limit: {model_info.output_token_limit}")
    
    print("\nSupported Generation Methods:")
    for method in model_info.supported_generation_methods:
        print(f"  - {method}")
    
    print("\nTemperature Range:")
    print(f"  Min: {model_info.temperature}")
    print(f"  Max: {model_info.max_temperature if hasattr(model_info, 'max_temperature') else 'N/A'}")
    
except Exception as e:
    print(f"Error getting model info: {e}")

# Test generation config limits
print("\n=== Testing Generation Config ===\n")

try:
    from google.generativeai.types import GenerationConfig
    
    # Test different max_output_tokens values
    test_values = [1000, 8192, 32768, 64000, 100000]
    
    for value in test_values:
        try:
            config = GenerationConfig(
                max_output_tokens=value,
                temperature=0.2
            )
            print(f"✓ max_output_tokens={value:,} - Config created successfully")
            print(f"  Actual value in config: {config.max_output_tokens}")
        except Exception as e:
            print(f"✗ max_output_tokens={value:,} - Error: {e}")
            
except Exception as e:
    print(f"Error testing generation config: {e}")