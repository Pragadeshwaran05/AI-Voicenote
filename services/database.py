import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_name='voicenote.db'):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_name)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    voice TEXT NOT NULL,
                    speed REAL NOT NULL,
                    audio_filename TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Phase 2 Database Migrations (Add new columns safely)
            try: cursor.execute('ALTER TABLE voice_generations ADD COLUMN language_detected TEXT')
            except sqlite3.OperationalError: pass
            try: cursor.execute('ALTER TABLE voice_generations ADD COLUMN sentiment TEXT')
            except sqlite3.OperationalError: pass
            try: cursor.execute('ALTER TABLE voice_generations ADD COLUMN emotion TEXT')
            except sqlite3.OperationalError: pass
            try: cursor.execute('ALTER TABLE voice_generations ADD COLUMN reading_mode TEXT')
            except sqlite3.OperationalError: pass
            
            # Phase 3 Database Migrations
            try: cursor.execute('ALTER TABLE voice_generations ADD COLUMN is_favorite INTEGER DEFAULT 0')
            except sqlite3.OperationalError: pass
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
            ''')
                
            conn.commit()

    def save_generation(self, text, language, voice, speed, audio_filename, lang_detected=None, sentiment=None, emotion=None, reading_mode=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO voice_generations (text, language, voice, speed, audio_filename, language_detected, sentiment, emotion, reading_mode, is_favorite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (text, language, voice, speed, audio_filename, lang_detected, sentiment, emotion, reading_mode))
            conn.commit()
            return cursor.lastrowid

    def toggle_favorite(self, record_id, is_favorite):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE voice_generations SET is_favorite = ? WHERE id = ?', (1 if is_favorite else 0, record_id))
            conn.commit()

    def get_recent_generations(self, limit=20, search_query=None, language_filter=None, mode_filter=None, favorite_only=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM voice_generations WHERE 1=1'
            params = []
            
            if search_query:
                query += ' AND text LIKE ?'
                params.append(f'%{search_query}%')
            if language_filter:
                query += ' AND language = ?'
                params.append(language_filter)
            if mode_filter:
                query += ' AND reading_mode = ?'
                params.append(mode_filter)
            if favorite_only:
                query += ' AND is_favorite = 1'
                
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
    def delete_generation(self, record_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM voice_generations WHERE id = ?', (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def save_settings(self, settings_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for k, v in settings_dict.items():
                cursor.execute('''
                    INSERT INTO settings (setting_key, setting_value)
                    VALUES (?, ?)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                ''', (k, str(v)))
            conn.commit()
            
    def get_settings(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value FROM settings')
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
            
    def get_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM voice_generations')
            total_generations = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(LENGTH(text)) FROM voice_generations')
            total_chars = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM voice_generations WHERE is_favorite = 1')
            saved_voices = cursor.fetchone()[0]
            
            cursor.execute('SELECT language, COUNT(language) as count FROM voice_generations GROUP BY language ORDER BY count DESC LIMIT 1')
            row = cursor.fetchone()
            most_used_lang = row[0] if row else "N/A"
            
            return {
                "total_generations": total_generations,
                "total_chars": total_chars,
                "saved_voices": saved_voices,
                "most_used_lang": most_used_lang
            }
