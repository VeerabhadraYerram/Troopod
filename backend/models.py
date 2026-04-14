from pydantic import BaseModel
from typing import List, Optional, Dict

class AdInsights(BaseModel):
    offer: str = ""
    target_audience: str = ""
    product_category: str = ""
    hooks: List[str] = []
    tone: str = ""
    key_claims: List[str] = []

class ExtractedSection(BaseModel):
    dom_path: str
    text_content: str

class PersonalizedContent(BaseModel):
    hero_headline: str = ""
    subheadline: str = ""
    cta_text: str = ""
    promo_banner: str = ""
    featured_highlight: str = ""

class ModificationResponse(BaseModel):
    success: bool
    message: str
    ad_insights: Optional[AdInsights] = None
    page_sections_extracted: Dict[str, ExtractedSection] = {}
    personalization_generated: Optional[PersonalizedContent] = None
    original_html: str = ""
    personalized_html: str = ""
