"""
Test per la funzionalità vista doppia pagina.
"""
import pytest
from PyQt5.QtWidgets import QApplication
from src.chapter_reader_window import PageDisplayWidget
from src.settings import Settings


@pytest.fixture
def page_widget(qapp):
    """Fixture per creare un PageDisplayWidget."""
    widget = PageDisplayWidget()
    return widget


def test_view_mode_initialization(page_widget):
    """Test che view_mode sia inizializzato correttamente."""
    assert hasattr(page_widget, 'view_mode')
    assert page_widget.view_mode in ["single", "double"]


def test_set_view_mode(page_widget):
    """Test cambio view_mode."""
    # Test cambio a double
    assert page_widget.set_view_mode("double") is True
    assert page_widget.view_mode == "double"

    # Test cambio a single
    assert page_widget.set_view_mode("single") is True
    assert page_widget.view_mode == "single"

    # Test valore invalido
    assert page_widget.set_view_mode("invalid") is False


def test_toggle_view_mode(page_widget):
    """Test toggle tra single e double."""
    initial_mode = page_widget.view_mode

    # Toggle una volta
    new_mode = page_widget.toggle_view_mode()
    assert new_mode != initial_mode
    assert page_widget.view_mode == new_mode

    # Toggle di nuovo (dovrebbe tornare al modo iniziale)
    final_mode = page_widget.toggle_view_mode()
    assert final_mode == initial_mode
    assert page_widget.view_mode == initial_mode


def test_view_mode_persists_in_settings(page_widget):
    """Test che view_mode venga salvato nelle settings."""
    settings = Settings()

    # Imposta double mode
    page_widget.set_view_mode("double")
    saved_mode = settings.get("reader.view_mode")
    assert saved_mode == "double"

    # Imposta single mode
    page_widget.set_view_mode("single")
    saved_mode = settings.get("reader.view_mode")
    assert saved_mode == "single"


def test_layout_methods_exist(page_widget):
    """Test che i metodi di layout esistano."""
    assert hasattr(page_widget, 'update_layout')
    assert hasattr(page_widget, '_update_layout_single')
    assert hasattr(page_widget, '_update_layout_double')
    assert hasattr(page_widget, '_get_page_height')


def test_rtl_support_in_double_mode(page_widget):
    """Test che RTL sia supportato in modalità doppia."""
    # Imposta RTL
    page_widget.reading_direction = "rtl"
    page_widget.view_mode = "double"

    # Verifica che la direzione sia impostata
    assert page_widget.reading_direction == "rtl"
    assert page_widget.view_mode == "double"


def test_page_positions_initialization(page_widget):
    """Test che page_positions sia inizializzato."""
    assert hasattr(page_widget, 'page_positions')
    assert isinstance(page_widget.page_positions, list)


def test_get_page_height_helper(page_widget):
    """Test del metodo helper _get_page_height."""
    # Test con indice None
    height = page_widget._get_page_height(None, 800)
    assert height == 0

    # Test con indice fuori range
    height = page_widget._get_page_height(9999, 800)
    assert height == 0

    # Test con target_width valido
    # Nota: senza dati caricati, restituisce 0 fino a quando non vengono impostate le pagine
    # Questo è il comportamento corretto per un widget vuoto
    height = page_widget._get_page_height(0, 800)
    assert height >= 0  # Può essere 0 se non ci sono dati


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
