from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
import os
import io

# Load .env from project root (one level up from backend/)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from models import ModificationResponse
from services.ad_analyzer import analyze_ad
from services.html_parser import fetch_html, extract_sections, apply_modifications
from services.personalization import generate_personalization

app = FastAPI(title="Troopod AI PM MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/personalize", response_model=ModificationResponse)
async def personalize_endpoint(
    landing_page_url: str = Form(...),
    ad_image: UploadFile = File(...)
):
    try:
        # 1. Read Ad Image
        image_bytes = await ad_image.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. Extract Ad Insights
        insights = analyze_ad(image)
        
        # 3. Fetch and Parse Landing Page
        html = await fetch_html(landing_page_url)
        sections, soup = extract_sections(html, landing_page_url)
        
        # Capture base-tagged original HTML
        base_tagged_original_html = str(soup)
        
        if not sections:
            return ModificationResponse(
                success=False,
                message="Could not identify any editable sections on the landing page.",
                original_html=base_tagged_original_html
            )
            
        # 4. Generate Personalization
        updates = generate_personalization(insights, sections)
        
        if not updates:
            return ModificationResponse(
                success=False,
                message="Failed to generate personalized content. Returning original HTML.",
                original_html=base_tagged_original_html
            )
            
        # Convert Pydantic to dict dropping empty
        update_dict = {k: v for k, v in updates.model_dump().items() if v}
        
        # 5. Render to new HTML
        new_html = apply_modifications(soup, update_dict, sections)
        
        return ModificationResponse(
            success=True,
            message="Successfully personalized landing page.",
            ad_insights=insights,
            page_sections_extracted=sections,
            personalization_generated=updates,
            original_html=base_tagged_original_html,
            personalized_html=new_html
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return ModificationResponse(
                success=False,
                message="Gemini API rate limit exceeded. Our AI is currently busy. Please wait 60 seconds and try again."
            )
        elif "blocking automated access" in error_msg or "503" in error_msg:
            return ModificationResponse(
                success=False,
                message="This website is blocking our automated personalizer. Please try a different URL or a simpler landing page."
            )
            
        raise HTTPException(status_code=500, detail=error_msg)
