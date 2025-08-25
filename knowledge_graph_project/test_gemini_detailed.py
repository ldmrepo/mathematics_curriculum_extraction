"""Test Gemini API response details"""
import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def test_gemini_response():
    """Test Gemini response with detailed metadata"""
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-pro")
    
    # Request a long structured response
    prompt = """
지식 그래프의 커뮤니티 클러스터 체계를 3단계 계층으로 설계하세요.

Level 0 (대분류): Resolution 0.1, 8-12개 클러스터
Level 1 (중분류): Resolution 0.5, 20-30개 클러스터  
Level 2 (소분류): Resolution 1.0, 40-60개 클러스터

각 레벨별로 20개 이상의 클러스터를 상세히 정의하세요.

출력 형식: 순수 JSON만 출력하세요.
"""
    
    config = genai.types.GenerationConfig(
        temperature=0.2,
        max_output_tokens=65536,  # Maximum for Gemini 2.5 Pro
        candidate_count=1
    )
    
    print(f"Generation Config:")
    print(f"  max_output_tokens: {config.max_output_tokens}")
    print(f"  temperature: {config.temperature}")
    print()
    
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=config
        )
        
        # Get response metadata
        print("Response Metadata:")
        print(f"  Text length: {len(response.text)} characters")
        
        if response.candidates:
            candidate = response.candidates[0]
            print(f"  Finish reason: {candidate.finish_reason.name}")
            print(f"  Safety ratings: {candidate.safety_ratings}")
            
            # Check token count if available
            if hasattr(candidate, 'token_count'):
                print(f"  Token count: {candidate.token_count}")
            
            # Check citation metadata if available
            if hasattr(candidate, 'citation_metadata'):
                print(f"  Citation metadata: {candidate.citation_metadata}")
        
        # Save response
        with open('debug/test_gemini_detailed_response.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Check if response is complete JSON
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response.text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.text
            
            data = json.loads(json_str)
            print("\n✓ Valid JSON response")
            print(f"  Top-level keys: {list(data.keys())}")
            
            # Count clusters at each level
            for key in data.keys():
                if isinstance(data[key], list):
                    print(f"  {key}: {len(data[key])} items")
                elif isinstance(data[key], dict):
                    for subkey in data[key].keys():
                        if isinstance(data[key][subkey], list):
                            print(f"  {key}.{subkey}: {len(data[key][subkey])} items")
                            
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON parsing failed at position {e.pos}")
            print(f"  Error: {e.msg}")
            
            # Show where it was truncated
            if len(response.text) > 100:
                print(f"\nLast 200 characters of response:")
                print(response.text[-200:])
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_response())