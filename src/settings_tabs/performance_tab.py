"""
Tab impostazioni performance: cache e preload.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QGroupBox, QCheckBox, QSpinBox)
from ..settings import Settings


class PerformanceTab(QWidget):
    """Tab per impostazioni performance (cache + preload)."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Gruppo Cache
        cache_group = QGroupBox("Cache Immagini")
        cache_layout = QVBoxLayout()

        # Cache size
        cache_size_layout = QHBoxLayout()
        cache_size_label = QLabel("Dimensione cache (numero immagini):")
        cache_size_layout.addWidget(cache_size_label)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setMinimum(10)
        self.cache_size_spin.setMaximum(200)
        self.cache_size_spin.setValue(self.settings.get("performance.image_cache_size", 50))
        cache_size_layout.addWidget(self.cache_size_spin)
        cache_size_layout.addStretch()

        cache_layout.addLayout(cache_size_layout)

        # Lazy loading
        self.lazy_loading_check = QCheckBox("Abilita lazy loading")
        self.lazy_loading_check.setChecked(self.settings.get("performance.lazy_loading", True))
        cache_layout.addWidget(self.lazy_loading_check)

        # Preload pages
        preload_layout = QHBoxLayout()
        preload_label = QLabel("Pagine da precaricare:")
        preload_layout.addWidget(preload_label)

        self.preload_spin = QSpinBox()
        self.preload_spin.setMinimum(0)
        self.preload_spin.setMaximum(10)
        self.preload_spin.setValue(self.settings.get("performance.preload_pages", 2))
        preload_layout.addWidget(self.preload_spin)
        preload_layout.addStretch()

        cache_layout.addLayout(preload_layout)

        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)

        layout.addStretch()
        self.setLayout(layout)

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        return {
            "performance.image_cache_size": self.cache_size_spin.value(),
            "performance.lazy_loading": self.lazy_loading_check.isChecked(),
            "performance.preload_pages": self.preload_spin.value()
        }
