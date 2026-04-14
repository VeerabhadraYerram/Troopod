import httpx
from io import BytesIO
import json
from PIL import Image

def test():
    # Create simple AD mockup (Red Square with some text to trigger Gemini vision correctly without flagging as blank/empty)
    # Actually just a solid color might make Gemini Vision refuse to find marketing hooks.
    # Let's see if Gemini handles "nothing" robustly as per our instructions.
    img = Image.new('RGB', (800, 400), color = (255, 100, 100))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    urls = [
        "https://example.com",
    ]
    
    for url in urls:
        print(f"Testing URL: {url}")
        files = {"ad_image": ("test.jpg", img_bytes, "image/jpeg")}
        data = {"landing_page_url": url}
        
        try:
            resp = httpx.post("http://127.0.0.1:8000/api/personalize", data=data, files=files, timeout=60.0)
            print("HTTP STATUS:", resp.status_code)
            r_json = resp.json()
            print("Success:", r_json.get("success"))
            print("Extracted:", list(r_json.get("page_sections_extracted", {}).keys()))
            if r_json.get("success"):
               print("Generated Personalization:", r_json.get("personalization_generated"))
            else:
               print("API Error Message:", r_json.get("message"))
            print("---")
        except Exception as e:
            print("Test script exception:", e)

if __name__ == "__main__":
    test()
