"""
Controllers package - Business logic layer.

Separa la logica di business dalle views seguendo il pattern MVC.
"""

from .library_controller import LibraryController
from .import_export_controller import ImportExportController
from .update_controller import UpdateController
from .collection_controller import CollectionController

__all__ = [
    'LibraryController',
    'ImportExportController',
    'UpdateController',
    'CollectionController',
]
