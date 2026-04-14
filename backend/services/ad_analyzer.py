import os
import json
from google import genai
from google.genai import types
from models import AdInsights
from PIL import Image

def analyze_ad(image: Image.Image) -> AdInsights:
    """
    Analyzes an ad image using Gemini to extract structured insights.
    Includes exponential backoff for 429 rate limits.
    """
    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set")
                
            client = genai.Client(api_key=api_key)
            
            prompt = """
            You are an expert marketing AI. Analyze the provided ad creative and extract the following structured information.
            If you are not confident about a field because the ad lacks the information, leave it as an empty string or empty array.
            Do NOT hallucinate.
            """
            
            schema = AdInsights.model_json_schema()
            schema.pop("title", None)
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,
                ),
            )
            data = json.loads(response.text)
            return AdInsights(**data)
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 15 # Shorter wait to avoid frontend timeout
                print(f"Rate limited (attempt {attempt+1}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            import traceback
            print(f"Error analyzing ad: {str(e)}")
            return AdInsights()
    
    return AdInsights()
