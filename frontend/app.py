import streamlit as st
import streamlit.components.v1 as components
import httpx
import json
import io
from PIL import Image

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
                # Prepare multipart payload
                files = {"ad_image": ("ad.jpg", ad_image_bytes, "image/jpeg")}
                data = {"landing_page_url": lp_url}
                
                # We configure backend dynamically
                import os
                backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
                response = httpx.post(f"{backend_url}/api/personalize", data=data, files=files, timeout=45.0)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        st.success("Personalization Complete!")
                        st.json(result.get("personalization_generated", {}))
                        
                        # Display previews
                        st.divider()
                        pcol1, pcol2 = st.columns(2)
                        
                        with pcol1:
                            st.subheader("Original Page")
                            components.html(result["original_html"], height=800, scrolling=True)
                            
                        with pcol2:
                            st.subheader("Personalized Page")
                            components.html(result["personalized_html"], height=800, scrolling=True)
                    else:
                        msg = result.get("message", "Unknown error")
                        if "rate limit" in msg.lower():
                            st.warning(f"🕒 {msg}")
                        elif "blocking" in msg.lower():
                            st.error(f"🛡️ {msg}")
                        else:
                            st.error(f"❌ Personalization Failed: {msg}")
                            
                        if "original_html" in result and result["original_html"]:
                            st.subheader("Fallback: Original Page")
                            components.html(result["original_html"], height=600, scrolling=True)
                else:
                    try:
                        err_detail = response.json().get("detail", response.text)
                    except:
                        err_detail = response.text
                    st.error(f"Backend Service Error: {err_detail}")
                    
            except Exception as e:
                st.error(f"Frontend connection error: {str(e)}")
