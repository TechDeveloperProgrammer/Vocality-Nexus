import os
from typing import Dict, Any
import json
import logging
from flask_babel import Babel
from flask import Flask, request, g

class InternationalizationManager:
    """
    Advanced internationalization management for Vocality Nexus
    Supports dynamic language loading, fallback mechanisms, and extensible translations
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Español',
        'fr': 'Français', 
        'zh': '中文',
        'ar': 'العربية',
        'hi': 'हिन्दी',
        'ja': '日本語',
        'ko': '한국어',
        'ru': 'Русский',
        'pt': 'Português'
    }

    def __init__(self, app: Flask):
        """
        Initialize internationalization with advanced configuration
        
        :param app: Flask application instance
        """
        self.babel = Babel(app)
        self.translations_cache: Dict[str, Dict[str, str]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Configure babel selector
        @self.babel.localeselector
        def get_locale():
            """
            Intelligent locale selection with multiple fallback strategies
            
            Precedence:
            1. Explicit language from request
            2. User's preferred language (if logged in)
            3. Browser's accepted languages
            4. Default language
            """
            # 1. Explicit language from request
            lang = request.args.get('lang')
            if lang and lang in self.SUPPORTED_LANGUAGES:
                return lang
            
            # 2. User's preferred language (placeholder for future authentication integration)
            if hasattr(g, 'user') and hasattr(g.user, 'preferred_language'):
                return g.user.preferred_language
            
            # 3. Browser's accepted languages
            return request.accept_languages.best_match(list(self.SUPPORTED_LANGUAGES.keys()), 'en')

    def load_translations(self, language_code: str) -> Dict[str, str]:
        """
        Load translations for a specific language with caching and error handling
        
        :param language_code: ISO 639-1 language code
        :return: Dictionary of translations
        """
        if language_code in self.translations_cache:
            return self.translations_cache[language_code]
        
        try:
            translations_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'translations', 
                f'{language_code}.json'
            )
            
            with open(translations_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            
            self.translations_cache[language_code] = translations
            return translations
        
        except FileNotFoundError:
            self.logger.warning(f"Translation file not found for language: {language_code}")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in translation file for language: {language_code}")
            return {}

    def translate(self, key: str, language_code: str = 'en', **kwargs) -> str:
        """
        Advanced translation method with interpolation and fallback
        
        :param key: Translation key
        :param language_code: Language code
        :param kwargs: Interpolation variables
        :return: Translated and interpolated string
        """
        translations = self.load_translations(language_code)
        
        # Fallback to English if translation not found
        if key not in translations and language_code != 'en':
            self.logger.info(f"Translation not found for {key} in {language_code}, falling back to English")
            translations = self.load_translations('en')
        
        translation = translations.get(key, key)
        
        # Simple interpolation
        try:
            return translation.format(**kwargs)
        except KeyError as e:
            self.logger.warning(f"Missing interpolation variable: {e}")
            return translation

    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        """
        Retrieve supported languages
        
        :return: Dictionary of language codes and names
        """
        return cls.SUPPORTED_LANGUAGES.copy()

def init_internationalization(app: Flask) -> InternationalizationManager:
    """
    Initialize internationalization for the Flask app
    
    :param app: Flask application instance
    :return: Internationalization manager instance
    """
    return InternationalizationManager(app)
