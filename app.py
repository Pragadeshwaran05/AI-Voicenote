import os
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from services.tts_service import TTSService
from services.text_analyzer import TextAnalyzer
from services.database import Database
from services.nlp_service import NLPService
from services.document_service import DocumentService
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_123')
app.config['AUDIO_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'audio')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5MB limit

os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize services
db = Database()
tts_service = TTSService(app.config['AUDIO_FOLDER'])
analyzer = TextAnalyzer()
nlp_service = NLPService()
document_service = DocumentService()

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/documents')
def documents():
    return render_template('documents.html')

@app.route('/library')
def library():
    return render_template('library.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')
    
@app.route('/help')
def help_page():
    return render_template('help.html')



@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text', '').strip()
    language = data.get('language', 'en')
    voice = data.get('voice', 'default')
    speed = float(data.get('speed', 1.0))
    reading_mode = data.get('reading_mode', 'standard')
    
    if not text:
        return jsonify({'error': 'Text is empty'}), 400
        
    if len(text) > 5000:
        return jsonify({'error': 'Text exceeds maximum length of 5000 characters'}), 400

    # Auto-adjust speed based on reading mode if no custom speed is strictly set
    # (Simplified for Phase 2: we assume the frontend might just pass speed)
    if reading_mode == 'accessibility':
        speed = min(speed, 0.8)
    elif reading_mode == 'presentation':
        speed = min(speed, 0.9)

    filename = f"voice_{uuid.uuid4().hex[:10]}.wav"
    
    try:
        # Run brief analysis for DB storage
        lang_res = nlp_service.detect_language(text)
        sent_res = nlp_service.analyze_sentiment(text)
        emo_res = nlp_service.detect_emotion(text)
        
        # Generate audio
        audio_path = tts_service.generate_audio(text, language, voice, speed, filename)
        
        # Save to database (with AI metadata)
        record_id = db.save_generation(
            text=text, 
            language=language, 
            voice=voice, 
            speed=speed, 
            audio_filename=filename,
            lang_detected=lang_res['name'],
            sentiment=sent_res['label'],
            emotion=emo_res['label'],
            reading_mode=reading_mode
        )
        
        return jsonify({
            'success': True,
            'message': 'Voice generated successfully',
            'audio_url': f'/audio/{filename}',
            'filename': filename,
            'id': record_id
        })
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return jsonify({'error': 'Failed to generate voice. Please try again.'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.route('/download/<filename>')
def download_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename, as_attachment=True)

@app.route('/api/history', methods=['GET'])
def get_history():
    search = request.args.get('search', '')
    lang = request.args.get('lang', '')
    mode = request.args.get('mode', '')
    fav = request.args.get('favorite') == 'true'
    limit = int(request.args.get('limit', 50))
    
    records = db.get_recent_generations(
        limit=limit,
        search_query=search if search else None,
        language_filter=lang if lang else None,
        mode_filter=mode if mode else None,
        favorite_only=fav
    )
    return jsonify(records)

@app.route('/api/favorite/<int:record_id>', methods=['POST'])
def toggle_favorite(record_id):
    data = request.json
    is_favorite = data.get('is_favorite', True)
    try:
        db.toggle_favorite(record_id, is_favorite)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'POST':
        settings_data = request.json
        db.save_settings(settings_data)
        return jsonify({'success': True})
    else:
        return jsonify(db.get_settings())

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(db.get_stats())

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.txt', '.pdf', '.docx']:
        return jsonify({'error': f'Unsupported file type: {ext}'}), 400
        
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        extracted_text = document_service.extract_text(file_path, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return jsonify({'success': True, 'text': extracted_text})
    except Exception as e:
        print(f"Error parsing document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    # Fetch the record first to get the filename
    records = db.get_recent_generations(limit=100)
    record = next((r for r in records if r['id'] == record_id), None)
    
    success = db.delete_generation(record_id)
    if success:
        # Also remove the file
        if record and record['audio_filename']:
            file_path = os.path.join(app.config['AUDIO_FOLDER'], record['audio_filename'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
                    
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete record'}), 400

@app.route('/api/text-stats', methods=['POST'])
def text_stats():
    data = request.json
    text = data.get('text', '')
    stats = analyzer.analyze(text)
    return jsonify(stats)

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    stats = analyzer.analyze(text)
    language = nlp_service.detect_language(text)
    sentiment = nlp_service.analyze_sentiment(text)
    emotion = nlp_service.detect_emotion(text)
    keywords = nlp_service.extract_keywords(text)
    
    return jsonify({
        'success': True,
        'language': language,
        'sentiment': sentiment,
        'emotion': emotion,
        'keywords': keywords,
        'statistics': stats
    })

@app.route('/api/enhance', methods=['POST'])
def enhance_text():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    enhanced = nlp_service.enhance_text(text)
    return jsonify({'success': True, 'enhanced_text': enhanced})

@app.route('/api/summarize', methods=['POST'])
def summarize_text():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    summary = nlp_service.summarize_text(text)
    return jsonify({'success': True, 'summary': summary})

@app.route('/api/voices', methods=['GET'])
def get_voices():
    language = request.args.get('language', 'en')
    voices = tts_service.get_available_voices(language)
    return jsonify(voices)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
