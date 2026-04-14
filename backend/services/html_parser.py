import httpx
from bs4 import BeautifulSoup
from models import ExtractedSection
from typing import Dict, Tuple

def get_css_selector(element) -> str:
    path = []
    parent = element
    while parent and parent.name != '[document]':
        if parent.name:
            siblings = parent.find_previous_siblings(parent.name)
            index = len(siblings) + 1
            path.append(f"{parent.name}:nth-of-type({index})")
        parent = parent.parent
    path.reverse()
    return " > ".join(path)

async def fetch_html(url: str) -> str:
    MAX_SIZE = 2 * 1024 * 1024 # 2MB
    content = b""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        try:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    content += chunk
                    if len(content) > MAX_SIZE:
                        raise ValueError("HTML response exceeded 2MB limit")
                return content.decode('utf-8', errors='ignore')
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                 # Common on Amazon when blocked
                 raise ValueError("The target website is blocking automated access (503 Service Unavailable). Please try another URL.")
            raise e

def extract_sections(html: str, url: str) -> Tuple[Dict[str, ExtractedSection], BeautifulSoup]:
    soup = BeautifulSoup(html, "lxml")
    
    # 0. Inject base tag for Streamlit relative assets/CSS resolution
    if soup.html:
        head = soup.find('head')
        if not head:
            head = soup.new_tag('head')
            soup.html.insert(0, head)
            
        if not head.find('base'):
            base_tag = soup.new_tag('base', href=url)
            head.insert(0, base_tag)
            
    sections = {}
    
    # 1. Hero Headline: First visible h1 OR h2 OR largest heading
    hero = soup.find(['h1', 'h2', 'h3'])
    if hero and hero.get_text(strip=True):
        sections['hero_headline'] = ExtractedSection(
            dom_path=get_css_selector(hero), text_content=hero.get_text(separator=' ', strip=True)
        )
    
    # 2. Subheadline: First p/h2/h3 near hero
    if hero:
        subhead = hero.find_next(['p', 'h2', 'h3'])
        # Ensure it's not the same as hero
        if subhead and subhead == hero:
            subhead = subhead.find_next(['p', 'h2', 'h3'])
            
        if subhead and subhead.get_text(strip=True):
            sections['subheadline'] = ExtractedSection(
                dom_path=get_css_selector(subhead), text_content=subhead.get_text(separator=' ', strip=True)
            )
            
    # 3. Primary CTA: More robust detection
    cta = soup.find(lambda tag: tag.name in ['button', 'a'] and tag.get_text(strip=True) and 
                   (any(cls in str(tag.get('class', '')).lower() for cls in ['btn', 'button', 'cta', 'primary'])) and
                   len(tag.get_text(strip=True)) < 40)
    
    if not cta:
        # Fallback to first short button-link
        cta = soup.find(lambda tag: tag.name in ['button', 'a'] and tag.get_text(strip=True) and len(tag.get_text(strip=True)) < 30)

    if cta:
        sections['cta_text'] = ExtractedSection(
            dom_path=get_css_selector(cta), text_content=cta.get_text(separator=' ', strip=True)
        )

    # 4. Promo Banner: Look for alert strips, top bars, or elements with 'promo/banner'
    promo = soup.find(lambda tag: tag.name in ['div', 'section', 'p'] and 
                     any(kw in str(tag.get('class', '')).lower() or kw in str(tag.get('id', '')).lower() 
                         for kw in ['promo', 'banner', 'announcement', 'alert-bar']) and
                     10 < len(tag.get_text(strip=True)) < 200)
    if promo:
        sections['promo_banner'] = ExtractedSection(
            dom_path=get_css_selector(promo), text_content=promo.get_text(separator=' ', strip=True)
        )

    # 5. Featured Highlight: Look for feature boxes or benefit sections
    highlight = soup.find(lambda tag: tag.name in ['div', 'section', 'h3', 'h4'] and 
                         any(kw in str(tag.get('class', '')).lower() for kw in ['feature', 'highlight', 'benefit', 'value-prop']) and
                         10 < len(tag.get_text(strip=True)) < 300)
    if highlight:
        sections['featured_highlight'] = ExtractedSection(
            dom_path=get_css_selector(highlight), text_content=highlight.get_text(separator=' ', strip=True)
        )
        
    return sections, soup

def apply_modifications(soup: BeautifulSoup, modifications: Dict[str, str], extracted: Dict[str, ExtractedSection]) -> str:
    from bs4 import NavigableString
    
    replacements_made = 0
    for key, new_text in modifications.items():
        if key in extracted and new_text:
            original = extracted[key]
            selector = original.dom_path
            
            # Try 1: Precise CSS Selector
            node = soup.select_one(selector)
            
            # Try 2: Fallback to exact text match if selector fails or text mismatch
            if not node or original.text_content not in node.get_text():
                # Find all elements with this exact text
                potential_nodes = soup.find_all(string=lambda t: original.text_content in str(t))
                if potential_nodes:
                    node = potential_nodes[0].parent

            if node:
                # Safe Text Replacement: 
                # Find the primary text node and update it, clear others to avoid duplication
                text_nodes = [t for t in node.descendants if isinstance(t, NavigableString) and t.strip()]
                
                if text_nodes:
                    # Update first significant text node, clear others
                    for i, t in enumerate(text_nodes):
                        if i == 0:
                            # Highlight the change with a subtle span to make it obvious in the demo
                            highlight_span = soup.new_tag("span", style="background-color: rgba(255, 255, 0, 0.2); border-bottom: 2px solid gold; padding: 2px 4px; border-radius: 3px;")
                            highlight_span.string = new_text
                            t.replace_with(highlight_span)
                        else:
                            t.replace_with(NavigableString(""))
                    replacements_made += 1
                else:
                    # Last resort: clear and set
                    node.clear()
                    node.string = new_text
                    replacements_made += 1
    
    print(f"Applied {replacements_made} personalization replacements to the DOM.")
    return str(soup)
