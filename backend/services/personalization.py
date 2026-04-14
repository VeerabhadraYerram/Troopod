import os
import json
from google import genai
from google.genai import types
from models import AdInsights, PersonalizedContent, ExtractedSection
from typing import Dict, Optional

def generate_personalization(
    insights: AdInsights, 
    extracted_sections: Dict[str, ExtractedSection]
) -> Optional[PersonalizedContent]:
    """
    Rewrites landing page copy using Groq (Llama 3.3 70B) for high speed and reliability.
    """
    import time
    from groq import Groq
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set. Falling back to Gemini logic if possible (not implemented).")
        return None # In a real app, we might fall back to Gemini
        
    client = Groq(api_key=api_key)
    max_retries = 3
    
    sections_context = {k: v.text_content for k, v in extracted_sections.items()}
    
    prompt = f"""
    You are an expert CRO copywriter. 
    Given the following Ad Insights and the Current Landing Page text, rewrite the page text to match the ad's hooks and audience.
    
    Constraints:
    - Preserve factual accuracy.
    - Do not invent offers/features.
    - BE BOLD: Make the copy noticeably more persuasive and aligned with the ad than the original.
    - Ensure text length is roughly similar to the original (±30%).
    - Only return fields that were provided in the Current Page Text.
    
    Return the result as a JSON object matching the requested schema.
    
    Ad Insights:
    {insights.model_dump_json(indent=2)}
    
    Current Page Text:
    {json.dumps(sections_context, indent=2)}
    """
    
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON assistant. Always return valid JSON matching the user's requested fields."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            
            data = json.loads(chat_completion.choices[0].message.content)
            new_content = PersonalizedContent(**data)
            
            # Validation: only keep fields that exist in the extracted sections
            validated = PersonalizedContent()
            for field in new_content.model_fields.keys():
                orig_text = sections_context.get(field, "")
                new_text = getattr(new_content, field)
                
                if new_text and orig_text:
                    # Reject if > 2.5x original length (allow small strings extra buffer)
                    if len(new_text) <= 2.5 * max(len(orig_text), 20):
                        setattr(validated, field, new_text)
                    else:
                        setattr(validated, field, orig_text)

            return validated
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 15
                print(f"Groq Rate limited (attempt {attempt+1}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            import traceback
            print(f"Error generating personalization with Groq: {str(e)}")
            return None
    
    return None
    
    return None
