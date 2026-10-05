import re

class TextAnalyzer:
    def analyze(self, text):
        if not text or not text.strip():
            return {
                'words': 0,
                'sentences': 0,
                'characters': 0,
                'reading_time_mins': 0,
                'reading_time_secs': 0
            }
            
        text = text.strip()
        
        # Characters (excluding whitespace for exact count, or including. Let's include all but give exact)
        characters = len(text)
        
        # Words
        words = len(text.split())
        
        # Sentences
        sentences = len(re.split(r'[.!?]+', text))
        # Adjust for empty string at end if text ends with punctuation
        if re.search(r'[.!?]+$', text):
            sentences = max(1, sentences - 1)
            
        # Reading time (average 200 words per minute)
        total_seconds = int((words / 200) * 60)
        reading_time_mins = total_seconds // 60
        reading_time_secs = total_seconds % 60
        
        return {
            'words': words,
            'sentences': sentences,
            'characters': characters,
            'reading_time_mins': reading_time_mins,
            'reading_time_secs': reading_time_secs
        }
