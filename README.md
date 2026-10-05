# 🎙️ AI VoiceNote — Intelligent Text-to-Speech Assistant

AI VoiceNote is an intelligent multilingual text-to-speech platform that understands text, analyzes its meaning and tone, enhances content, and converts it into natural speech. Built as a complete, full-stack Flask application.

## 🌟 Features
* **AI Text Intelligence**: Local NLP to detect language, sentiment, emotions, and extract keywords.
* **Document to Speech**: Upload `.txt`, `.pdf`, or `.docx` files to automatically extract and read the contents aloud.
* **Reading Modes**: Select "News", "Study", "Presentation", or "Accessibility" to automatically configure the voice cadence.
* **Advanced History & Library**: Browse previous generations, search your text, filter by reading mode, and favorite your best audios into the Audio Library.
* **Settings & Preferences**: Personalize the application by selecting default languages, voices, speeds, and auto-analyze preferences.
* **Modular TTS Engine**: Robust `BaseTTSProvider` architecture currently utilizing Windows SAPI5 (via `pyttsx3`) for offline generation. Easily extensible to cloud services.

## 🛠️ Technology Stack
* **Backend**: Python, Flask, SQLite3
* **Frontend**: HTML5, CSS3, Vanilla JS
* **NLP**: TextBlob (Sentiment), NRCLex (Emotion), Rake-NLTK (Keywords), langdetect
* **Document Parsing**: PyPDF2, python-docx
* **TTS**: pyttsx3, Windows COM/SAPI5

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd "AI voice nore"
   ```

2. **Set up a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Rename `.env.example` to `.env` and configure your secret key.
   ```bash
   cp .env.example .env
   ```

5. **Run the Application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

## 📊 Project Structure
* `/app.py`: Flask application and API routes.
* `/services/`: Modular core functionality (`database.py`, `tts_service.py`, `nlp_service.py`, `document_service.py`).
* `/templates/`: Jinja2 UI templates (Dashboard, Landing, Library, Settings, History, Help).
* `/static/`: CSS and Javascript assets.
* `/audio/`: Automatically generated `.wav` files.
* `/uploads/`: Temporary upload directory for parsing documents.

## ⚠️ Known Limitations
* **Voices**: The voices available depend entirely on your local OS installed speech packages.
* **Emotional Inflection**: While the app understands emotion, local offline TTS cannot dynamically change pitch or inflection based on emotion (cloud API integration required).
* **Speed/Pacing**: Reading modes adjust the baseline speed multiplier based on the mode.

---
*Developed for Phase 3 (Final)*
