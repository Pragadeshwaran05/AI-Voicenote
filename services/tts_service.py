import pyttsx3
import os
import sys

import pyttsx3
import os
import sys

class BaseTTSProvider:
    def get_available_voices(self, language='en'):
        raise NotImplementedError

    def generate_audio(self, text, language, voice, speed, filename):
        raise NotImplementedError

class Pyttsx3Provider(BaseTTSProvider):
    def __init__(self, audio_folder):
        self.audio_folder = audio_folder
        
    def _init_com(self):
        # On Windows, pythoncom needs to be initialized per thread for SAPI5
        if sys.platform == 'win32':
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                pass
        
    def get_available_voices(self, language='en'):
        self._init_com()
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice_list = []
            for v in voices:
                voice_list.append({
                    'id': v.id,
                    'name': v.name
                })
            return voice_list
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
        
    def generate_audio(self, text, language, voice, speed, filename):
        self._init_com()
        file_path = os.path.join(self.audio_folder, filename)
        
        try:
            engine = pyttsx3.init()
            default_rate = engine.getProperty('rate')
            engine.setProperty('rate', int(default_rate * speed))
            
            if voice and voice != 'default':
                try:
                    engine.setProperty('voice', voice)
                except Exception:
                    pass
                    
            engine.save_to_file(text, file_path)
            engine.runAndWait()
            
            return file_path
        except Exception as e:
            print(f"TTS Engine Error: {e}")
            raise Exception("Failed to generate audio due to a TTS engine error.")

class TTSService:
    """Wrapper that delegates to the configured provider."""
    def __init__(self, audio_folder):
        self.provider = Pyttsx3Provider(audio_folder)
        
    def get_available_voices(self, language='en'):
        return self.provider.get_available_voices(language)
        
    def generate_audio(self, text, language, voice, speed, filename):
        return self.provider.generate_audio(text, language, voice, speed, filename)

