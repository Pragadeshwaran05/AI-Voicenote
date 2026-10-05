import re

try:
    from langdetect import detect, detect_langs
except ImportError:
    pass

try:
    from textblob import TextBlob
except ImportError:
    pass

try:
    from rake_nltk import Rake
except ImportError:
    pass

try:
    from nrclex import NRCLex
except ImportError:
    pass

try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer
except ImportError:
    pass


class NLPService:
    def __init__(self):
        # We initialize Rake here if needed, but we'll do it lazily
        self._rake = None
        self._language_map = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French',
            'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
            'nl': 'Dutch', 'ru': 'Russian', 'zh-cn': 'Chinese',
            'ja': 'Japanese', 'ko': 'Korean', 'ta': 'Tamil',
            'hi': 'Hindi', 'ar': 'Arabic'
        }

    def detect_language(self, text):
        if not text:
            return {"name": "Unknown", "code": "unknown"}
        try:
            lang_code = detect(text)
            lang_name = self._language_map.get(lang_code, lang_code.upper())
            return {"name": lang_name, "code": lang_code}
        except Exception:
            return {"name": "Unknown", "code": "unknown"}

    def analyze_sentiment(self, text):
        if not text:
            return {"label": "Neutral", "score": 0.0}
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                label = "Positive"
            elif polarity < -0.1:
                label = "Negative"
            else:
                label = "Neutral"
                
            # Convert polarity [-1, 1] to a confidence-like score [0, 1]
            score = abs(polarity)
            # If it's neutral, score can be based on subjectivity (closer to 0 subjectivity = highly neutral)
            if label == "Neutral":
                score = 1.0 - blob.sentiment.subjectivity
                
            return {"label": label, "score": round(score, 2)}
        except Exception:
            return {"label": "Neutral", "score": 0.0}

    def detect_emotion(self, text):
        if not text:
            return {"label": "Neutral", "score": 0.0}
        try:
            emotion_obj = NRCLex()
            emotion_obj.load_raw_text(text)
            top_emotions = emotion_obj.top_emotions
            if top_emotions and top_emotions[0][1] > 0.0:
                # filter out 'positive' and 'negative' if there's a specific emotion tied
                specific_emotions = [e for e in top_emotions if e[0] not in ('positive', 'negative')]
                best = specific_emotions[0] if specific_emotions else top_emotions[0]
                label = best[0].capitalize()
                score = best[1]
                return {"label": label, "score": round(score, 2)}
            return {"label": "Neutral", "score": 1.0}
        except Exception as e:
            print(f"Emotion error: {e}")
            return {"label": "Neutral", "score": 1.0}

    def extract_keywords(self, text, max_keywords=5):
        if not text:
            return []
        try:
            if not self._rake:
                self._rake = Rake()
            self._rake.extract_keywords_from_text(text)
            keywords = self._rake.get_ranked_phrases()
            return keywords[:max_keywords]
        except Exception:
            # Basic fallback if NLTK data is missing
            words = re.findall(r'\b\w+\b', text.lower())
            freq = {}
            for w in words:
                if len(w) > 3:
                    freq[w] = freq.get(w, 0) + 1
            sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            return [w[0] for w in sorted_words[:max_keywords]]

    def summarize_text(self, text, sentences_count=2):
        if not text or len(text.split()) < 30:
            return "Text is already short."
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, sentences_count)
            return " ".join([str(sentence) for sentence in summary])
        except Exception:
            return "Summary unavailable. Ensure NLTK 'punkt' is installed."

    def enhance_text(self, text):
        if not text:
            return text
        
        # Rule-based basic enhancement
        # Capitalize first letter of each sentence
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        enhanced_sentences = []
        for s in sentences:
            if s:
                s = s.strip()
                if len(s) > 0:
                    s = s[0].upper() + s[1:]
                enhanced_sentences.append(s)
        
        enhanced_text = " ".join(enhanced_sentences)
        
        # Ensure it ends with punctuation
        if enhanced_text and enhanced_text[-1] not in '.!?':
            enhanced_text += '.'
            
        return enhanced_text
