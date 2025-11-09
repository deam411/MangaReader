"""
Test suite completa per il sistema i18n Translator (v0.3.0).

Verifica caricamento traduzioni, switch lingua e fallback.
"""
import pytest
import os
import json
import tempfile
from src.i18n.translator import TranslationManager


class TestTranslator:
    """Test suite per TranslationManager."""

    @pytest.fixture
    def temp_locales_dir(self, tmp_path):
        """Crea directory locales temporanea con file di traduzione."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        # Crea file en.json
        en_translations = {
            "app_name": "Manga Reader",
            "library": "Library",
            "search": "Search manga...",
            "settings": "Settings",
            "import": "Import"
        }

        with open(locales_dir / "en.json", "w", encoding="utf-8") as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)

        # Crea file it.json
        it_translations = {
            "app_name": "Manga Reader",
            "library": "Libreria",
            "search": "Cerca manga...",
            "settings": "Impostazioni",
            "import": "Importa"
        }

        with open(locales_dir / "it.json", "w", encoding="utf-8") as f:
            json.dump(it_translations, f, ensure_ascii=False, indent=2)

        # Crea file es.json
        es_translations = {
            "app_name": "Manga Reader",
            "library": "Biblioteca",
            "search": "Buscar manga...",
            "settings": "Configuración",
            "import": "Importar"
        }

        with open(locales_dir / "es.json", "w", encoding="utf-8") as f:
            json.dump(es_translations, f, ensure_ascii=False, indent=2)

        yield str(locales_dir)

    @pytest.fixture
    def translator(self, temp_locales_dir, monkeypatch):
        """Crea istanza TranslationManager con directory locales temporanea."""
        translator = TranslationManager()

        # Override locales_dir
        translator.locales_dir = temp_locales_dir
        translator._load_all_translations()

        return translator

    def test_initialization(self, translator):
        """Test inizializzazione TranslationManager."""
        assert translator.current_language == 'en'
        assert len(translator.translations) > 0

    def test_load_all_translations(self, translator):
        """Test caricamento di tutte le traduzioni disponibili."""
        # Dovrebbe aver caricato en, it, es
        assert 'en' in translator.translations
        assert 'it' in translator.translations
        assert 'es' in translator.translations

    def test_get_translation_english(self, translator):
        """Test recupero traduzione in inglese."""
        translator.set_language('en')

        assert translator.get('library') == "Library"
        assert translator.get('search') == "Search manga..."
        assert translator.get('settings') == "Settings"

    def test_get_translation_italian(self, translator):
        """Test recupero traduzione in italiano."""
        translator.set_language('it')

        assert translator.get('library') == "Libreria"
        assert translator.get('search') == "Cerca manga..."
        assert translator.get('settings') == "Impostazioni"

    def test_get_translation_spanish(self, translator):
        """Test recupero traduzione in spagnolo."""
        translator.set_language('es')

        assert translator.get('library') == "Biblioteca"
        assert translator.get('search') == "Buscar manga..."
        assert translator.get('settings') == "Configuración"

    def test_set_language_valid(self, translator):
        """Test cambio lingua valido."""
        result = translator.set_language('it')
        assert result is True
        assert translator.current_language == 'it'

        result = translator.set_language('es')
        assert result is True
        assert translator.current_language == 'es'

    def test_set_language_invalid(self, translator):
        """Test cambio lingua con codice non esistente."""
        original_lang = translator.current_language

        result = translator.set_language('fr')  # Non caricato
        assert result is False
        assert translator.current_language == original_lang  # Non cambiato

    def test_get_missing_key_fallback(self, translator):
        """Test fallback per chiave mancante."""
        translator.set_language('en')

        # Chiave non esistente
        result = translator.get('nonexistent_key')

        # Dovrebbe tornare la chiave stessa come fallback
        assert result == 'nonexistent_key'

    def test_get_missing_key_with_default(self, translator):
        """Test fallback con valore di default specificato."""
        translator.set_language('en')

        result = translator.get('missing_key', default='Default Value')
        assert result == 'Default Value'

    def test_get_all_available_languages(self, translator):
        """Test recupero lingue disponibili."""
        languages = translator.get_available_languages()

        assert 'en' in languages
        assert 'it' in languages
        assert 'es' in languages
        assert len(languages) == 3

    def test_translation_persistence_after_language_switch(self, translator):
        """Test che le traduzioni persistano dopo cambio lingua."""
        # Imposta italiano
        translator.set_language('it')
        assert translator.get('library') == "Libreria"

        # Cambia in inglese
        translator.set_language('en')
        assert translator.get('library') == "Library"

        # Torna a italiano - dovrebbe ancora funzionare
        translator.set_language('it')
        assert translator.get('library') == "Libreria"

    def test_empty_translation_file(self, tmp_path, monkeypatch):
        """Test caricamento file di traduzione vuoto."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        # File vuoto
        with open(locales_dir / "empty.json", "w") as f:
            json.dump({}, f)

        translator = TranslationManager()
        translator.locales_dir = str(locales_dir)
        translator._load_all_translations()

        # Dovrebbe caricarsi senza errori
        assert 'empty' in translator.translations
        assert translator.translations['empty'] == {}

    def test_malformed_json_file(self, tmp_path, monkeypatch):
        """Test gestione file JSON malformato."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        # File JSON malformato
        with open(locales_dir / "bad.json", "w") as f:
            f.write("{ this is not valid json }")

        translator = TranslationManager()
        translator.locales_dir = str(locales_dir)

        # Dovrebbe gestire l'errore gracefully
        translator._load_all_translations()

        # Non dovrebbe aver caricato il file malformato
        assert 'bad' not in translator.translations or translator.translations['bad'] == {}

    def test_get_current_language(self, translator):
        """Test recupero lingua corrente."""
        translator.set_language('it')
        assert translator.get_current_language() == 'it'

        translator.set_language('en')
        assert translator.get_current_language() == 'en'

    def test_has_translation(self, translator):
        """Test verifica esistenza traduzione per chiave."""
        translator.set_language('en')

        assert translator.has_translation('library') is True
        assert translator.has_translation('search') is True
        assert translator.has_translation('nonexistent') is False

    def test_unicode_translations(self, tmp_path):
        """Test supporto caratteri unicode nelle traduzioni."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        # Traduzioni con unicode (giapponese, cinese, etc)
        ja_translations = {
            "app_name": "マンガリーダー",
            "library": "ライブラリ",
            "search": "検索..."
        }

        with open(locales_dir / "ja.json", "w", encoding="utf-8") as f:
            json.dump(ja_translations, f, ensure_ascii=False, indent=2)

        translator = TranslationManager()
        translator.locales_dir = str(locales_dir)
        translator._load_all_translations()
        translator.set_language('ja')

        assert translator.get('app_name') == "マンガリーダー"
        assert translator.get('library') == "ライブラリ"

    def test_translation_with_special_characters(self, tmp_path):
        """Test traduzioni con caratteri speciali."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        special_translations = {
            "message": "Hello \"World\"!",
            "path": "C:\\Users\\Documents",
            "code": "print('test')"
        }

        with open(locales_dir / "special.json", "w", encoding="utf-8") as f:
            json.dump(special_translations, f, ensure_ascii=False, indent=2)

        translator = TranslationManager()
        translator.locales_dir = str(locales_dir)
        translator._load_all_translations()
        translator.set_language('special')

        assert translator.get('message') == "Hello \"World\"!"
        assert translator.get('path') == "C:\\Users\\Documents"
        assert translator.get('code') == "print('test')"

    def test_get_with_formatting(self, translator):
        """Test traduzioni con placeholder per formattazione."""
        # Simula traduzione con placeholder
        translator.translations['en']['welcome'] = "Welcome, {username}!"

        result = translator.get('welcome')
        # Dovrebbe tornare la stringa con placeholder non sostituito
        assert result == "Welcome, {username}!"

        # L'utente dovrà formattarla con .format()
        formatted = result.format(username="John")
        assert formatted == "Welcome, John!"

    def test_reload_translations(self, translator, temp_locales_dir):
        """Test ricaricamento traduzioni dopo modifica file."""
        # Modifica file it.json
        it_file = os.path.join(temp_locales_dir, "it.json")

        new_translations = {
            "app_name": "Manga Reader",
            "library": "Biblioteca Modificata",  # Modificato
            "search": "Cerca manga...",
            "settings": "Impostazioni",
            "import": "Importa",
            "new_key": "Nuovo Valore"  # Aggiunto
        }

        with open(it_file, "w", encoding="utf-8") as f:
            json.dump(new_translations, f, ensure_ascii=False, indent=2)

        # Ricarica traduzioni
        translator._load_all_translations()
        translator.set_language('it')

        # Verifica modifiche
        assert translator.get('library') == "Biblioteca Modificata"
        assert translator.get('new_key') == "Nuovo Valore"

    def test_case_sensitive_keys(self, translator):
        """Test che le chiavi siano case-sensitive."""
        translator.set_language('en')

        # Aggiungi traduzioni con case diverso
        translator.translations['en']['Library'] = "Upper Library"
        translator.translations['en']['library'] = "Lower Library"

        assert translator.get('Library') == "Upper Library"
        assert translator.get('library') == "Lower Library"

    def test_empty_string_translation(self, tmp_path):
        """Test traduzione con stringa vuota."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        translations = {
            "empty": "",
            "normal": "Normal text"
        }

        with open(locales_dir / "test.json", "w", encoding="utf-8") as f:
            json.dump(translations, f)

        translator = TranslationManager()
        translator.locales_dir = str(locales_dir)
        translator._load_all_translations()
        translator.set_language('test')

        # Stringa vuota è valida
        assert translator.get('empty') == ""
        assert translator.get('normal') == "Normal text"

    def test_nested_keys_not_supported(self, translator):
        """Test che chiavi annidate non siano supportate (flat structure)."""
        # Il sistema usa struttura flat, non annidamenti
        translator.translations['en']['user.name'] = "User Name"

        # Deve accedere con chiave completa
        assert translator.get('user.name') == "User Name"

        # Non con accesso annidato
        assert translator.get('user') != {'name': 'User Name'}

    def test_language_code_normalization(self, translator):
        """Test normalizzazione codici lingua."""
        # Test con codici sia lowercase che uppercase
        translator.set_language('EN')
        # Dovrebbe normalizzare a lowercase se implementato
        # Per ora assumiamo case-sensitive

    def test_get_all_translations_for_current_language(self, translator):
        """Test recupero tutte le traduzioni per lingua corrente."""
        translator.set_language('it')

        all_translations = translator.get_all()

        assert 'library' in all_translations
        assert all_translations['library'] == "Libreria"
        assert all_translations['search'] == "Cerca manga..."

    def test_translation_count(self, translator):
        """Test conteggio traduzioni per lingua."""
        translator.set_language('en')

        translations = translator.get_all()
        count = len(translations)

        # Dovrebbe avere almeno le chiavi che abbiamo definito
        assert count >= 5  # app_name, library, search, settings, import

    def test_multiple_translator_instances(self, temp_locales_dir):
        """Test multiple istanze TranslationManager indipendenti."""
        translator1 = TranslationManager()
        translator1.locales_dir = temp_locales_dir
        translator1._load_all_translations()

        translator2 = TranslationManager()
        translator2.locales_dir = temp_locales_dir
        translator2._load_all_translations()

        # Cambio lingua su una non dovrebbe influenzare l'altra
        translator1.set_language('en')
        translator2.set_language('it')

        assert translator1.get('library') == "Library"
        assert translator2.get('library') == "Libreria"
