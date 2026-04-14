import streamlit as st
import streamlit.components.v1 as components
import httpx
import json
import io
import os
import sys
from PIL import Image

# Add backend to sys.path so we can import services directly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Import services directly (no API call needed in unified app)
try:
    from backend.services.ad_analyzer import analyze_ad
    from backend.services.personalization import generate_personalization
    from backend.services.html_parser import fetch_html, extract_sections, apply_modifications
except ImportError:
    # Fallback for different execution contexts
    from services.ad_analyzer import analyze_ad
    from services.personalization import generate_personalization
    from services.html_parser import fetch_html, extract_sections, apply_modifications

st.set_page_config(layout="wide", page_title="Troopod AI PM MVP")

st.title("Landing Page Personalizer (AI CRO)")

st.markdown("""
Upload an Ad Creative (Image) or Provide an Ad URL.
Then enter the target Landing Page URL.
The system will dynamically modify the page's copy to match the ad's hooks.
""")

col1, col2 = st.columns(2)

with st.sidebar:
    st.title("System Status")
    st.info("🤖 **Hybrid AI Active**\n\n👁️ **Vision**: Gemini 2.0\n\n✍️ **Copy**: Groq Llama 3.3")
    st.divider()
    st.caption("Using Groq for ultra-fast text generation and bypassing quota limits.")

col1, col2 = st.columns(2)

with col1:
    ad_input_type = st.radio("Ad Source", ["Upload Image", "Image URL"])
    ad_image_bytes = None
    
    if ad_input_type == "Upload Image":
        uploaded_file = st.file_uploader("Upload Ad Creative", type=['png', 'jpg', 'jpeg', 'webp'])
        if uploaded_file:
            ad_image_bytes = uploaded_file.getvalue()
            st.image(ad_image_bytes, caption="Uploaded Ad", use_column_width=True)
    else:
        ad_url = st.text_input("Ad Image URL")
        if ad_url:
            try:
                resp = httpx.get(ad_url, timeout=10)
                resp.raise_for_status()
                ad_image_bytes = resp.content
                st.image(ad_image_bytes, caption="Fetched Ad", use_column_width=True)
            except Exception as e:
                st.error(f"Could not load image from URL: {e}")

with col2:
    lp_url = st.text_input("Target Landing Page URL", placeholder="https://example.com")
    
if st.button("Generate Personalized Page", type="primary"):
    if not lp_url:
        st.error("Please enter a landing page URL")
    elif not lp_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    elif not ad_image_bytes:
        st.error("Please provide an Ad creative (Image or URL)")
    else:
        with st.spinner("Analyzing Ad and Injecting CRO insights..."):
            try:
                # 1. Fetch HTML
                html = httpx.get(lp_url, follow_redirects=True, timeout=15.0).text
                
                # 2. Extract Sections
                extracted, soup = extract_sections(html, lp_url)
                
                if not extracted:
                    st.error("Could not extract any content from the landing page. It might be blocking automated access.")
                else:
                    # 3. Analyze Ad
                    insights = analyze_ad(ad_image_bytes)
                    
                    if not insights:
                        st.error("Ad analysis failed. Please check your Gemini API key.")
                    else:
                        # 4. Personalize
                        updates = generate_personalization(insights, extracted)
                        
                        if not updates:
                            st.warning("Personalization generation failed (Rate limited). Showing original page.")
                            st.subheader("Original Page (Fallback)")
                            components.html(html, height=800, scrolling=True)
                        else:
                            # 5. Mutate
                            personalized_html = apply_modifications(soup, updates.model_dump(), extracted)
                            
                            st.success("Personalization Complete!")
                            st.json(updates.model_dump())
                            
                            # Display previews
                            st.divider()
                            pcol1, pcol2 = st.columns(2)
                            
                            with pcol1:
                                st.subheader("Original Page")
                                components.html(html, height=800, scrolling=True)
                                
                            with pcol2:
                                st.subheader("Personalized Page")
                                components.html(personalized_html, height=800, scrolling=True)
                                
            except Exception as e:
                st.error(f"Processing error: {str(e)}")
                import traceback
                print(traceback.format_exc())
