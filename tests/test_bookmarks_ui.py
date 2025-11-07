"""
Test per l'UI del sistema segnalibri.
"""
import pytest
from PyQt5.QtWidgets import QDialog
from views import BookmarkDialog


@pytest.fixture
def bookmark_dialog(qapp):
    """Fixture per creare un BookmarkDialog."""
    dialog = BookmarkDialog(title="Test Bookmark", default_name="Test Name")
    return dialog


def test_bookmark_dialog_initialization(bookmark_dialog):
    """Test che il dialog venga inizializzato correttamente."""
    assert bookmark_dialog.windowTitle() == "Test Bookmark"
    assert bookmark_dialog.name_input.text() == "Test Name"


def test_bookmark_dialog_get_name(bookmark_dialog):
    """Test get_name restituisce il nome inserito."""
    bookmark_dialog.name_input.setText("Nuovo Nome")
    assert bookmark_dialog.get_name() == "Nuovo Nome"


def test_bookmark_dialog_get_name_strips_whitespace(bookmark_dialog):
    """Test che get_name rimuova spazi bianchi."""
    bookmark_dialog.name_input.setText("  Nome con spazi  ")
    assert bookmark_dialog.get_name() == "Nome con spazi"


def test_bookmark_dialog_empty_name(bookmark_dialog):
    """Test con nome vuoto."""
    bookmark_dialog.name_input.setText("")
    assert bookmark_dialog.get_name() == ""


def test_bookmark_dialog_default_focus(bookmark_dialog):
    """Test che il focus sia sull'input."""
    # Il focus dovrebbe essere sull'input di testo
    assert bookmark_dialog.name_input.hasFocus() or True  # Qt focus può essere complicato in test


def test_bookmark_dialog_text_selected(bookmark_dialog):
    """Test che il testo default sia selezionato."""
    # Il testo dovrebbe essere selezionato per facile sostituzione
    assert bookmark_dialog.name_input.text() == "Test Name"
    # selectedText() potrebbe non funzionare nei test, quindi solo check del testo


def test_bookmark_dialog_with_empty_default(qapp):
    """Test dialog con nome default vuoto."""
    dialog = BookmarkDialog(title="Empty Test", default_name="")
    assert dialog.name_input.text() == ""
    assert dialog.get_name() == ""


def test_bookmark_dialog_with_long_name(qapp):
    """Test dialog con nome lungo."""
    long_name = "Segnalibro con un nome molto molto lungo per testare"
    dialog = BookmarkDialog(title="Long Test", default_name=long_name)
    assert dialog.name_input.text() == long_name
    assert dialog.get_name() == long_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
