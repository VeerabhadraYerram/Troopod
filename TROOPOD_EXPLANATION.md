# Troopod AI PM Assignment: Landing Page Personalizer

**Candidate**: [Veerabhadra Yerram]  
**Project**: AI Landing Page Personalizer (MVP)

---

## 1. System Architecture & Flow

The system follows a synchronous **Extract → Analyze → Transform → Mutate** pipeline, optimized for speed and visual fidelity.

### **The 4-Step Pipeline**
1.  **Ingestion & Scraping**:
    - The backend fetches the target landing page HTML using `httpx` with browser-spoofing headers to bypass basic WAFs (Web Application Firewalls).
    - It extracts critical "CRO Anchors": H1s, subheadlines, Primary CTAs, and Promo Banners.
2.  **Multimodal Ad Analysis (Gemini 2.0 Vision)**:
    - The ad creative (image/URL) is sent to **Gemini 2.0 Flash**.
    - The model extracts semantic hooks, target audience, brand tone, and core value propositions.
3.  **Hybrid AI Transformation (Groq Llama 3.3)**:
    - To avoid rate-limiting bottle-necks and ensure sub-second response times, the system switches to **Groq**.
    - Llama 3.3 (70B) rewrites the landing page copy by merging the **Ad Insights** with the **Existing Page Context**.
4.  **Safe DOM Mutation**:
    - A custom mutation engine injects the new copy into a cloned version of the original HTML.
    - It uses **Fuzzy Text Matching** and **CSS Path Selectors** to ensure the new content lands exactly where the old content was, maintaining 100% layout integrity.

---

## 2. Key Components & Agent Design

### **A. The Vision Agent (The Analyst)**
- **Role**: Understand the "Why" behind the ad.
- **Design**: Uses zero-shot multimodal prompting. It is specifically instructed to ignore visual noise and focus on conversion-driving elements (hooks/audience).

### **B. The Personalization Agent (The Copywriter)**
- **Role**: Perform the CRO rewrite.
- **Design**: Operates in "Constraint-Aware Mode." It is provided with strict character-length limits and a "Factual Guardrail" system to prevent it from inventing offers not present in the original page.

### **C. The Mutation Engine (The UI Guard)**
- **Role**: Protect the existing UI.
- **Design**: Unlike generic "wrapper" agents that might break CSS, this engine uses a "surgical replacement" strategy. It only touches the inner content of elements, never their tags or classes.

---

## 3. Handling Edge Cases & Robustness

### **How we handle: Hallucinations**
- **Schema Validation**: We use Pydantic models to force the AI to return structured JSON.
- **Original Content Passthrough**: If the AI hallucinates a field that didn't exist in the original scrape, the Mutation Engine ignores it and keeps the original page state.

### **How we handle: Broken UI**
- **Length Normalization**: We measure the byte-length of original strings. If the AI output is >2.5x the original (which would likely break a layout), we either trim it or fall back to a more conservative rewrite.
- **Style Preservation**: We avoid replacing whole HTML chunks. We only swap `NavigableString` nodes inside the DOM, which preserves all styles, event listeners, and nested icons.

### **How we handle: Random Changes / Inconsistent Outputs**
- **Deterministic Prompting**: We use a low temperature (0.1) and system instructions that prioritize consistency over creative flair.
- **Fuzzy Matching Fallback**: If a page is dynamic and the CSS path shifts, the system looks for the literal text content. This ensures the correct button is updated even if the developer changed the page's ID or class.

---

## 4. Submission & Live Demo

**Live Demo**: [INSERT_YOUR_STREAMLIT_URL_HERE]  
**GitHub Repo**: [INSERT_YOUR_GITHUB_URL_HERE]

---

### **Assumptions Made**
- **Manual Trigger**: I assumed the user wants to trigger personalization manually rather than it happening automatically on every page load (better for demo transparency).
- **Text-Only Optimization**: I matched the requirement of "existing page enhanced" by focusing on high-ROI copy changes rather than re-ordering entire page sections, which would require a much more complex (and fragile) layout agent.
