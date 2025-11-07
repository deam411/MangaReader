from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt


class SmartTagWidget(QWidget):
    """Widget intelligente per la gestione dei tag con suggerimenti e auto-completamento."""

    # Tag predefiniti essenziali per manga
    PREDEFINED_TAGS = [
        # Generi principali
        "Action", "Adventure", "Comedy", "Drama", "Fantasy",
        "Horror", "Mystery", "Romance", "Sci-Fi", "Slice of Life",
        "Supernatural", "Psychological", "Sports", "Magic"
    ]

    def __init__(self):
        super().__init__()
        self.tags = []  # Lista dei tag correnti
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Label informativo
        info_label = QLabel('Clicca sui tag per selezionarli/deselezionarli')
        info_label.setStyleSheet('color: #888; font-size: 11px; font-style: italic;')
        main_layout.addWidget(info_label)

        # Area scrollabile per i pulsanti di tag
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(80)
        scroll_area.setMaximumHeight(100)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2b2b2b;
            }
        """)

        # Container per i pulsanti tag
        self.tags_container = QWidget()
        self.tags_grid = QGridLayout()
        self.tags_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.tags_grid.setSpacing(3)
        self.tags_grid.setContentsMargins(4, 4, 4, 4)
        self.tags_container.setLayout(self.tags_grid)

        # Crea pulsanti toggle per ogni tag predefinito
        self.tag_buttons = {}
        row, col = 0, 0
        max_cols = 5  # Numero di tag per riga

        for tag_name in self.PREDEFINED_TAGS:
            tag_btn = QPushButton(tag_name)
            tag_btn.setCheckable(True)  # Rendilo toggle
            tag_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 10px;
                    text-align: center;
                    min-width: 60px;
                    max-height: 22px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border-color: #4a9eff;
                }
                QPushButton:checked {
                    background-color: #4a9eff;
                    border-color: #3a7ecc;
                    font-weight: bold;
                }
            """)
            tag_btn.clicked.connect(lambda checked, t=tag_name: self.toggle_tag(t, checked))
            self.tags_grid.addWidget(tag_btn, row, col)
            self.tag_buttons[tag_name] = tag_btn

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        scroll_area.setWidget(self.tags_container)
        main_layout.addWidget(scroll_area)

        # Contatore tag selezionati
        self.counter_label = QLabel('Tag selezionati: 0')
        self.counter_label.setStyleSheet('color: #888; font-size: 11px; font-weight: bold;')
        main_layout.addWidget(self.counter_label)

    def toggle_tag(self, tag_name, checked):
        """Gestisce il toggle di un tag."""
        if checked:
            # Aggiungi tag se non presente
            if tag_name not in self.tags:
                self.tags.append(tag_name)
        else:
            # Rimuovi tag se presente
            if tag_name in self.tags:
                self.tags.remove(tag_name)

        # Aggiorna il contatore
        self.update_counter()

    def update_counter(self):
        """Aggiorna il contatore dei tag selezionati."""
        count = len(self.tags)
        self.counter_label.setText(f'Tag selezionati: {count}')

    def set_tags(self, tags_string):
        """Imposta i tag da una stringa separata da virgole."""
        # Reset tutti i pulsanti
        for tag_name, button in self.tag_buttons.items():
            button.setChecked(False)

        # Aggiorna la lista tags
        self.tags = []
        if tags_string:
            tag_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
            for tag in tag_list:
                self.tags.append(tag)
                # Attiva il pulsante corrispondente se esiste
                if tag in self.tag_buttons:
                    self.tag_buttons[tag].setChecked(True)

        self.update_counter()

    def get_tags_string(self):
        """Ritorna i tag come stringa separata da virgole."""
        return ', '.join(self.tags)

    def clear(self):
        """Rimuove tutti i tag."""
        self.tags = []
        # Deseleziona tutti i pulsanti
        for button in self.tag_buttons.values():
            button.setChecked(False)
        self.update_counter()
