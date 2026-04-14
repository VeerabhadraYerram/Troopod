# Troopod AI PM Assignment: Landing Page Personalizer (MVP)

This repository contains a high-performance, production-ready AI Landing Page Personalizer built for the Troopod AI PM assessment.

## 🚀 The "Wow" Factor: Hybrid AI Architecture
To overcome the strict rate limits of free-tier AI models while maintaining top-tier vision capabilities, this MVP uses a **Hybrid Dual-Provider Strategy**:
- **👁️ Vision (Gemini 2.0 Flash)**: Analyzes ad creatives with superior spatial awareness and hook extraction.
- **✍️ Copy (Groq Llama 3.3 70B)**: Performs ultra-fast (<1s) text transformation, ensuring a stable and snappy demo experience even under high load.

## ✨ Key Features
- **Surgical DOM Mutation**: Uses a non-destructive logic that replaces text while preserving all original CSS, JS events, and nested HTML structures.
- **Visual Optimization Highlights**: Automatically highlights AI-optimized sections in yellow to prove the logic to the user in real-time.
- **Fuzzy Matching Support**: Robustly handles dynamic pages by falling back to text-content matching if CSS selectors drift.
- **CRO Principles**: The AI is specifically tuned to prioritize Hero Headlines, CTAs, and Value Props.

## 📁 Submission Documents
- **[Detailed System Explanation (Architecture & Logic)](file:///Users/shivaniyerram/Desktop/Projects/Troopod_AIPM/TROOPOD_EXPLANATION.md)**: Full answers to the technical questions (Hallucinations, Broken UI, Inconsistent outputs).

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- `GEMINI_API_KEY` (from Google AI Studio)
- `GROQ_API_KEY` (from Groq Cloud)

### Local Installation
1. **Clone & Setup Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Environment**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
```

### Running the System
**1. Start the Backend API (Terminal 1)**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**2. Start the Frontend App (Terminal 2)**
```bash
streamlit run frontend/app.py
```

## 🎥 Deployment Guide
- **Backend (Render/Railway)**: Deploy the `backend` folder as a Python service.
- **Frontend (Streamlit Cloud)**: Connect your GitHub repo and point to `frontend/app.py`. Ensure you set the `BACKEND_URL` environment variable to your Render/Railway URL.
