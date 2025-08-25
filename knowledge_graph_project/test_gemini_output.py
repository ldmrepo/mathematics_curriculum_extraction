"""Test Gemini API output limits"""
import asyncio
import os
from src.ai_models import AIModelManager
from loguru import logger

async def test_gemini_output():
    """Test Gemini output with long response request"""
    
    # Enable debug logging
    logger.add("test_gemini.log", level="DEBUG")
    
    ai_manager = AIModelManager()
    
    # Request a very long response
    prompt = """
Generate a very long JSON object with 100 items. Each item should have:
- id (number)
- name (string with at least 20 characters)
- description (string with at least 100 characters)
- properties (object with at least 5 properties)

Make sure the response is a complete, valid JSON. Start with:
```json
{
  "items": [
"""
    
    try:
        response = await ai_manager.get_completion('gemini_pro', prompt)
        
        print(f"Response length: {len(response['content'])} characters")
        print(f"Finish reason: {response.get('finish_reason', 'Unknown')}")
        print(f"Output tokens: {response.get('output_tokens', 'Unknown')}")
        
        # Save response to file
        with open('debug/test_gemini_response.txt', 'w', encoding='utf-8') as f:
            f.write(response['content'])
        
        # Check if response is truncated
        if response['content'].strip().endswith('}'):
            print("✓ Response appears complete")
        else:
            print("✗ Response appears truncated")
            print(f"Last 100 chars: ...{response['content'][-100:]}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_gemini_output())