# CLAUDE.md - AI Assistant Guide for MangaReader

**Last Updated**: 2025-11-14
**Version**: 0.5.0
**Codebase**: Python 3.8+, PyQt5, SQLite

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Codebase Structure](#codebase-structure)
4. [Development Workflows](#development-workflows)
5. [Key Architectural Patterns](#key-architectural-patterns)
6. [Testing Guidelines](#testing-guidelines)
7. [Code Quality Standards](#code-quality-standards)
8. [Database Schema](#database-schema)
9. [Plugin System](#plugin-system)
10. [Common Tasks & Patterns](#common-tasks--patterns)
11. [Security Considerations](#security-considerations)
12. [Git Workflow](#git-workflow)
13. [Build & Release](#build--release)
14. [Important Conventions](#important-conventions)

---

## Project Overview

**MangaReader** is a cross-platform desktop application for reading and managing manga libraries. It's a mature, production-ready application with:

- **142 Python files**, ~18,500 lines of code
- **Multi-platform support**: Windows, macOS, Linux
- **Custom file format**: `.manga` files (SQLite-based)
- **Extensive plugin system** with 15+ hook events
- **80% test coverage** on core workflows
- **Security-hardened** with comprehensive input validation
- **Performance-optimized** (3-5x database improvements)

**Key Features**:
- Full-screen manga reader with zoom/pan
- Library management (grid/list view)
- Plugin system for extensibility
- Statistics tracking and export
- Auto-update from GitHub releases
- Internationalization (EN, IT)
- Custom themes (Dark/Light/System)

---

## Technology Stack

### Core Technologies

```python
# Primary Stack
Language: Python 3.8+ (configured for 3.9+)
GUI Framework: PyQt5 (>=5.15.0)
Database: SQLite3 (WAL mode, embedded)
Image Processing: Pillow (>=9.0.0)
Build Tool: PyInstaller
```

### Development Tools

```bash
# Testing
pytest              # Test runner
pytest-qt           # Qt testing
pytest-cov          # Coverage reporting
pytest-xdist        # Parallel test execution

# Code Quality
black               # Code formatter
pylint              # Linter
mypy                # Type checking
flake8              # Style guide enforcement

# Documentation
sphinx              # Documentation generation
sphinx-rtd-theme    # Read the Docs theme
```

### Additional Libraries

- `rarfile` - CBR archive support
- `urllib` - GitHub API integration
- `json` - Configuration and i18n
- `sqlite3` - Database operations

---

## Codebase Structure

### Root Directory

```
MangaReader/
├── main.py                      # Application entry point
├── views.py                     # Main UI views (backward compatibility)
├── database_legacy_root.py      # Legacy database for migration
├── src/                         # Main source code
├── tests/                       # Test suite (23 files)
├── plugins/                     # Plugin system
├── BuildTools/                  # Build scripts and specs
├── assets/                      # Icons and resources
├── .github/workflows/           # CI/CD configuration
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── [documentation files]
```

### Source Code Organization (`src/`)

#### Core Modules

```
src/
├── database/                    # Modular database layer (v0.2.0)
│   ├── connection.py            # Schema, indices, migrations
│   ├── manager.py               # Facade pattern for backward compatibility
│   ├── metadata_manager.py      # Manga metadata CRUD
│   ├── chapter_manager.py       # Volumes, chapters, pages
│   ├── bookmark_manager.py      # Bookmark operations
│   ├── history_manager.py       # Reading history tracking
│   └── statistics_manager.py    # Stats and analytics
│
├── settings.py                  # Singleton settings manager (JSON)
├── constants.py                 # Centralized constants (150 lines)
├── paths.py                     # Cross-platform path resolution
├── exceptions.py                # Custom exception hierarchy (13+)
├── logger.py                    # Centralized logging with rotation
├── cache_manager.py             # LRU cache for covers
├── updater.py                   # Auto-update from GitHub
│
├── views/                       # UI components (9 files)
│   ├── library_view.py          # Library grid/list view
│   ├── manga_view.py            # Manga details view
│   ├── volume_view.py           # Volume/chapter selection
│   ├── reader_view.py           # Full-screen reader
│   ├── dialogs.py               # UI dialogs
│   ├── widgets.py               # Custom widgets
│   └── virtual_list_view.py     # Virtualized list for performance
│
├── settings_tabs/               # Settings dialog tabs (9 tabs)
├── i18n/                        # Internationalization
│   ├── translator.py            # i18n manager
│   └── locales/                 # Translation files (en.json, it.json)
│
├── utils/                       # Helper modules
│   ├── validation.py            # Input sanitization (9 validators)
│   ├── security.py              # Security utilities
│   ├── image_converter.py       # Threaded image conversion
│   ├── cache_stats.py           # Cache performance analysis
│   └── theme_validator.py       # Theme schema validation
│
├── stats/                       # Statistics system
├── collections/                 # Collection management
├── backup/                      # Backup and restore
├── importers/                   # Archive import (CBZ/CBR)
├── creator/                     # Manga creator application
├── metadata/                    # Metadata fetching
├── repositories/                # Data access abstraction
│
├── theme_manager.py             # Theme generation and application
├── themes.json                  # Dark/Light theme definitions
├── settings_dialog.py           # Main settings dialog
├── chapter_reader_window.py     # Advanced reader with zoom/pan
└── tag_widget.py                # Smart tag selection widget
```

### Plugin System

```
plugins/
├── plugin_base.py               # Base class with 15+ hooks
├── plugin_manager.py            # Auto-discovery and lifecycle
└── available/                   # Plugin directory
    └── example_plugin/          # Example plugin
```

### Tests

```
tests/
├── conftest.py                  # Pytest fixtures
├── test_database.py             # Database operations
├── test_settings.py             # Settings management
├── test_paths.py                # Path resolution
├── test_security_*.py           # Security tests
├── test_integration_*.py        # Integration tests
└── test_performance_*.py        # Performance benchmarks
```

---

## Development Workflows

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/deam411/MangaReader.git
cd MangaReader

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run application in development mode
python main.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run only fast tests (skip slow tests)
pytest -m "not slow"

# Run specific test file
pytest tests/test_database.py -v

# Run with custom script
python run_all_tests.py
python run_all_tests.py --quick
```

### Code Quality Checks

```bash
# Format code with Black
black src/ main.py views.py

# Check style with Pylint
pylint src/ main.py views.py

# Type checking with mypy
mypy src/

# Style guide with flake8
flake8 src/ main.py views.py
```

### Building Executables

**Windows:**
```cmd
cd BuildTools
build.bat
# Output: dist/MangaReader.exe (~58 MB)
```

**macOS:**
```bash
cd BuildTools
chmod +x build_mac.sh
./build_mac.sh
hdiutil create -volname "Manga Reader" -srcfolder dist/MangaReader.app -ov -format UDZO dist/MangaReader.dmg
# Output: dist/MangaReader.dmg (~65 MB)
```

**Linux:**
```bash
cd BuildTools
chmod +x build_linux.sh
./build_linux.sh
# Output: dist/MangaReader (~70 MB)
```

---

## Key Architectural Patterns

### Design Patterns in Use

1. **Singleton Pattern**
   - `Settings` class for global configuration
   - Ensures single instance across application

2. **Facade Pattern**
   - `MangaDatabaseManager` wraps specialized managers
   - Maintains backward compatibility while improving modularity

3. **Repository Pattern**
   - `repositories/` for data access abstraction
   - Separates data access logic from business logic

4. **MVC-like Architecture**
   - Model: `database/` modules
   - View: `views/` modules
   - Controller: Business logic in main classes

5. **Observer Pattern**
   - Qt signals/slots for component communication
   - Plugin system hooks for event notifications

6. **Factory Pattern**
   - Theme generation from JSON configurations
   - Dynamic UI element creation

7. **Context Manager**
   - Resource management (DB connections, thread pools)
   - Automatic cleanup and error handling

8. **Strategy Pattern**
   - Plugin hooks for extensibility
   - Configurable behavior through plugins

9. **LRU Cache**
   - Memory-efficient image caching
   - Configurable cache size (50-200 images)

10. **Thread Pool**
    - Parallel image conversion
    - Non-blocking UI operations

### Exception Hierarchy

```python
MangaReaderError (base)
├── DatabaseError
│   ├── DatabaseConnectionError
│   ├── DatabaseSchemaError
│   └── DatabaseQueryError
├── ImportError
│   ├── ArchiveFormatError
│   └── MetadataError
├── ValidationError
│   ├── FileSizeError
│   └── FileFormatError
├── CacheError
├── SettingsError
│   ├── SettingsLoadError
│   └── SettingsSaveError
└── ReaderError
    ├── PageLoadError
    └── ChapterNotFoundError
```

**Usage Pattern**:
```python
from src.exceptions import DatabaseError, ValidationError

try:
    # Database operation
    db.save_metadata(title, author)
except ValidationError as e:
    logger.error(f"Invalid input: {e}")
    # Handle validation error
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    # Handle database error
```

### Application Flow

```
1. main.py (Entry point)
   ↓
2. Initialize QApplication
   ↓
3. Apply theme from settings
   ↓
4. Create MangaReader(QMainWindow)
   ↓
5. Initialize PluginManager and load plugins
   ↓
6. Create 4 views (Library, Manga, Volume, Reader)
   ↓
7. Setup keyboard shortcuts
   ↓
8. Trigger plugin on_startup hooks
   ↓
9. Show fullscreen window

Navigation Flow:
LibraryView (0) → MangaView (1) → VolumeView (2) → ReaderView (3)
```

---

## Testing Guidelines

### Test Organization

Tests are organized into categories:

1. **Unit Tests**
   - Database operations
   - Settings management
   - Path resolution
   - Validation functions

2. **Integration Tests**
   - Complete workflows
   - Multi-component interactions
   - Database + UI integration

3. **Performance Tests**
   - Benchmarks
   - Cache efficiency
   - Database query speed

4. **Security Tests**
   - Input validation
   - XSS prevention
   - SQL injection protection
   - Path traversal protection

5. **UI Tests**
   - Theme validation
   - Widget behavior
   - View navigation

### Writing Tests

**Basic Test Structure**:
```python
# tests/test_example.py
import pytest
from src.database.manager import MangaDatabaseManager

def test_manga_creation(temp_dir):
    """Test creating a new manga file."""
    # Arrange
    db = MangaDatabaseManager(temp_dir / "test.manga")

    # Act
    db.save_metadata("Test Manga", "Test Author", "Description")

    # Assert
    metadata = db.get_metadata()
    assert metadata['title'] == "Test Manga"
    assert metadata['author'] == "Test Author"
```

**Using Fixtures** (from `conftest.py`):
```python
def test_with_fixtures(temp_dir, sample_image_path, qapp):
    """Test using multiple fixtures."""
    # temp_dir: Temporary directory for test files
    # sample_image_path: Path to test image
    # qapp: QApplication instance
    pass
```

**Test Markers**:
```python
@pytest.mark.slow
def test_large_library():
    """Test with 1000+ manga (slow)."""
    pass

@pytest.mark.integration
def test_full_import_workflow():
    """Integration test for import workflow."""
    pass

@pytest.mark.ui
def test_theme_application(qapp):
    """UI test requiring QApplication."""
    pass
```

### Coverage Requirements

- **Target**: 80%+ on core workflows
- **Core modules must have**: Database, Settings, Validation
- **Optional coverage**: UI views (harder to test)

---

## Code Quality Standards

### Type Hints

All new code should include type hints:

```python
from typing import Optional, List, Dict, Tuple
from pathlib import Path

def save_metadata(
    self,
    title: str,
    author: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> bool:
    """Save manga metadata to database.

    Args:
        title: Manga title
        author: Author name
        description: Optional description
        tags: Optional list of tags

    Returns:
        True if successful, False otherwise

    Raises:
        ValidationError: If title or author is invalid
        DatabaseError: If database operation fails
    """
    pass
```

### Docstrings

Follow NumPy/Google style:

```python
def calculate_cache_hit_rate(self) -> float:
    """Calculate the cache hit rate percentage.

    The hit rate is calculated as:
        hits / (hits + misses) * 100

    Returns:
        Hit rate as a percentage (0-100)

    Examples:
        >>> manager.calculate_cache_hit_rate()
        85.5
    """
    pass
```

### Code Formatting

- **Formatter**: Black (line length: 88)
- **Style Guide**: PEP 8
- **Import Order**: Standard, third-party, local

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
from PyQt5.QtWidgets import QWidget
from PIL import Image

# Local
from src.database.manager import MangaDatabaseManager
from src.settings import Settings
```

### Naming Conventions

```python
# Classes: PascalCase
class MangaReader:
    pass

# Functions/Methods: snake_case
def load_manga_list():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_CACHE_SIZE = 200
DEFAULT_THEME = "dark"

# Private members: leading underscore
class Example:
    def __init__(self):
        self._internal_state = {}

    def _helper_method(self):
        pass
```

### Logging

Use centralized logger:

```python
from src.logger import get_logger

logger = get_logger(__name__)

# Log levels
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
logger.critical("Critical error")
```

**Log Location**:
- Windows: `%LOCALAPPDATA%\MangaReader\manga_reader.log`
- Unix: `~/.mangareader/manga_reader.log`
- **Rotation**: 10MB max, 5 backups

---

## Database Schema

### Schema Version: 4

The database uses SQLite with WAL mode for concurrent access.

### Tables

#### 1. metadata
```sql
CREATE TABLE metadata (
    title TEXT NOT NULL,
    author TEXT,
    description TEXT,
    language TEXT,
    cover BLOB,
    year INTEGER,
    tags TEXT  -- JSON array
)
```

#### 2. volumes
```sql
CREATE TABLE volumes (
    id INTEGER PRIMARY KEY,
    name TEXT,
    order_index INTEGER,
    cover BLOB
)
```

#### 3. chapters
```sql
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    name TEXT,
    order_index INTEGER,
    description TEXT,
    volume_id INTEGER,
    FOREIGN KEY (volume_id) REFERENCES volumes(id)
)
```

#### 4. pages
```sql
CREATE TABLE pages (
    chapter_id INTEGER,
    page_number INTEGER,
    image_data BLOB,
    width INTEGER,      -- v3: Page dimensions
    height INTEGER,     -- v3: Page dimensions
    PRIMARY KEY (chapter_id, page_number),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
)
```

#### 5. history
```sql
CREATE TABLE history (
    user TEXT,
    chapter_id INTEGER,
    page_number INTEGER,
    timestamp INTEGER,
    notes TEXT,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
)
```

#### 6. bookmarks
```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER,
    page_number INTEGER,
    name TEXT,
    timestamp INTEGER,
    category TEXT,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
)
```

#### 7. collections
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created_at INTEGER
)
```

#### 8. collection_manga
```sql
CREATE TABLE collection_manga (
    collection_id INTEGER,
    manga_path TEXT,
    added_at INTEGER,
    PRIMARY KEY (collection_id, manga_path),
    FOREIGN KEY (collection_id) REFERENCES collections(id)
)
```

#### 9. reading_sessions (v4)
```sql
CREATE TABLE reading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manga_path TEXT,
    chapter_id INTEGER,
    session_start INTEGER,
    session_end INTEGER,
    pages_read INTEGER,
    session_date TEXT,  -- YYYY-MM-DD format
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
)
```

### Performance Indexes (9 total)

```sql
CREATE INDEX idx_volumes_order ON volumes(order_index);
CREATE INDEX idx_chapters_volume ON chapters(volume_id);
CREATE INDEX idx_chapters_order ON chapters(order_index);
CREATE INDEX idx_pages_chapter ON pages(chapter_id, page_number);
CREATE INDEX idx_history_user ON history(user);
CREATE INDEX idx_history_timestamp ON history(timestamp);
CREATE INDEX idx_history_chapter ON history(chapter_id);
CREATE INDEX idx_bookmarks_chapter ON bookmarks(chapter_id);
CREATE INDEX idx_reading_sessions_manga ON reading_sessions(manga_path);
```

### Database Migrations

When updating schema:

1. Increment schema version in `connection.py`
2. Add migration logic in `_migrate_schema()`
3. Test migration with existing .manga files
4. Document changes in CHANGELOG.md

**Example Migration**:
```python
def _migrate_schema(self, old_version: int, new_version: int):
    """Migrate database from old to new version."""
    if old_version < 3 and new_version >= 3:
        # Add page dimensions (v3)
        self.cursor.execute("""
            ALTER TABLE pages
            ADD COLUMN width INTEGER DEFAULT NULL
        """)
        self.cursor.execute("""
            ALTER TABLE pages
            ADD COLUMN height INTEGER DEFAULT NULL
        """)
```

### Database Access Patterns

**Always use the facade**:
```python
from src.database.manager import MangaDatabaseManager

# Create/open manga file
db = MangaDatabaseManager("path/to/manga.manga")

# Save metadata
db.save_metadata("Title", "Author", "Description", tags=["action", "adventure"])

# Get metadata
metadata = db.get_metadata()

# Add volume
volume_id = db.add_volume("Volume 1")

# Add chapter
chapter_id = db.add_chapter(volume_id, "Chapter 1")

# Add pages
for i, image_path in enumerate(image_paths):
    with Image.open(image_path) as img:
        db.add_page(chapter_id, i + 1, img)

# Close connection
db.close()
```

**Use specialized managers for specific operations**:
```python
from src.database.bookmark_manager import BookmarkManager

bm = BookmarkManager(connection)
bm.add_bookmark(chapter_id, page_number, "Favorite Scene")
bookmarks = bm.get_all_bookmarks()
```

---

## Plugin System

### Plugin Architecture

Plugins extend functionality through **15+ hook events**:

#### Lifecycle Hooks
- `on_startup()` - Called when application starts
- `on_shutdown()` - Called before application exits

#### Import/Export Hooks
- `pre_import(context)` - Before manga import
- `post_import(context)` - After successful import
- `pre_export(context)` - Before manga export
- `post_export(context)` - After successful export

#### Reading Hooks
- `pre_page_load(context)` - Before loading page
- `post_page_load(context)` - After page loaded
- `on_chapter_change(context)` - When changing chapters

#### Library Hooks
- `on_library_refresh(context)` - When library refreshed
- `on_manga_added(context)` - When manga added
- `on_manga_deleted(context)` - When manga deleted

#### UI Hooks
- `custom_menu_item()` - Add custom menu items
- `custom_toolbar_button()` - Add toolbar buttons

### Creating a Plugin

**1. Create plugin directory**:
```
plugins/available/my_plugin/
├── __init__.py
└── plugin.py
```

**2. Implement plugin class**:
```python
# plugins/available/my_plugin/plugin.py
from plugins.plugin_base import PluginBase, PluginMetadata

class MyPlugin(PluginBase):
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        return PluginMetadata(
            name="My Plugin",
            version="1.0.0",
            author="Your Name",
            description="Does something useful"
        )

    def get_config_schema(self) -> dict:
        """Configuration schema for plugin settings."""
        return {
            'enable_notifications': {
                'type': 'bool',
                'default': True,
                'description': 'Enable notifications'
            },
            'api_key': {
                'type': 'str',
                'default': '',
                'description': 'API key for external service'
            },
            'check_interval': {
                'type': 'int',
                'default': 60,
                'description': 'Check interval in seconds'
            }
        }

    def on_manga_added(self, context: dict):
        """Called when manga is added to library."""
        manga_path = context.get('manga_path')
        logger.info(f"New manga added: {manga_path}")

        # Get plugin config
        if self.config.get('enable_notifications'):
            self._send_notification(f"New manga: {manga_path}")

    def _send_notification(self, message: str):
        """Send notification (example)."""
        pass
```

**3. Plugin auto-discovery**:
Plugins in `plugins/available/` are automatically discovered and loaded on startup.

**4. Plugin configuration**:
Users can configure plugins via Settings > Plugins tab.

### Plugin Best Practices

1. **Error Handling**: Always catch exceptions in hooks
2. **Performance**: Don't block UI thread
3. **Logging**: Use `get_logger(__name__)`
4. **Configuration**: Provide sensible defaults
5. **Documentation**: Document hook behavior

---

## Common Tasks & Patterns

### Adding a New Feature

1. **Plan the feature** (write todos if complex)
2. **Check existing code** for similar patterns
3. **Update database schema** if needed (increment version)
4. **Implement core logic** in appropriate module
5. **Add UI components** if needed
6. **Write tests** for new functionality
7. **Update documentation** (README, CHANGELOG)
8. **Test on multiple platforms** if UI changes
9. **Create PR** with descriptive title and summary

### Adding a New Setting

```python
# 1. Add to Settings class (src/settings.py)
DEFAULT_SETTINGS = {
    'my_new_setting': 'default_value'
}

# 2. Add UI in settings tab (src/settings_tabs/)
class MySettingsTab(QWidget):
    def __init__(self):
        # ... UI setup
        self.my_checkbox = QCheckBox("Enable feature")

    def save_settings(self):
        settings = Settings()
        settings.set('my_new_setting', self.my_checkbox.isChecked())

# 3. Use setting in code
settings = Settings()
if settings.get('my_new_setting'):
    # Feature enabled
    pass
```

### Adding Database Migration

```python
# src/database/connection.py
SCHEMA_VERSION = 5  # Increment

def _migrate_schema(self, old_version: int, new_version: int):
    """Migrate database schema."""
    if old_version < 5 and new_version >= 5:
        # Add new column
        self.cursor.execute("""
            ALTER TABLE my_table
            ADD COLUMN new_field TEXT DEFAULT NULL
        """)
        logger.info("Migrated schema to v5")
```

### Adding UI View

```python
# src/views/my_view.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add widgets
        label = QLabel("My View")
        layout.addWidget(label)
```

### Adding i18n Translation

```json
// src/i18n/locales/en.json
{
    "my_feature": {
        "title": "My Feature",
        "description": "This is my feature",
        "button_text": "Click Me"
    }
}
```

```python
# Use in code
from src.i18n.translator import Translator

translator = Translator()
title = translator.translate("my_feature.title")
```

---

## Security Considerations

### Input Validation

**Always validate user input** using validation utilities:

```python
from src.utils.validation import (
    sanitize_filename,
    validate_text_input,
    validate_file_size,
    is_safe_path
)

# Sanitize filename (prevent path traversal)
safe_filename = sanitize_filename(user_input)

# Validate text input (prevent XSS)
if not validate_text_input(user_description):
    raise ValidationError("Invalid input detected")

# Validate file size (prevent DoS)
if not validate_file_size(file_path, max_size=50*1024*1024):  # 50MB
    raise FileSizeError("File too large")

# Check path is safe (prevent directory traversal)
if not is_safe_path(base_dir, file_path):
    raise SecurityError("Unsafe path detected")
```

### SQL Injection Prevention

**Always use parameterized queries**:

```python
# GOOD - Parameterized query
cursor.execute(
    "SELECT * FROM metadata WHERE title = ?",
    (user_input,)
)

# BAD - String interpolation (SQL injection!)
cursor.execute(
    f"SELECT * FROM metadata WHERE title = '{user_input}'"
)
```

### Path Traversal Prevention

```python
from pathlib import Path

def is_safe_path(base_dir: Path, file_path: Path) -> bool:
    """Check if file_path is within base_dir."""
    try:
        base_dir = base_dir.resolve()
        file_path = file_path.resolve()
        return file_path.is_relative_to(base_dir)
    except (ValueError, OSError):
        return False
```

### Security Checklist

When implementing new features:

- [ ] Validate all user input
- [ ] Sanitize filenames before file operations
- [ ] Use parameterized SQL queries
- [ ] Check file sizes before processing
- [ ] Verify paths don't escape base directory
- [ ] Escape HTML if displaying user content
- [ ] Use try/except for error handling
- [ ] Log security events
- [ ] Test with malicious input

---

## Git Workflow

### Branch Naming

```bash
# Feature branches
claude/feature-name-sessionid

# Bug fix branches
claude/bugfix-name-sessionid

# Current branch (example)
claude/claude-md-mhz3svlzhnxdtz6x-01Wi3fVrcZqhWJUv5coo9QqX
```

### Commit Message Format

Follow conventional commits:

```
Type: Brief description (50 chars or less)

Detailed explanation if needed. Wrap at 72 characters.
- Can include bullet points
- Explain the why, not the what

Examples:
Feature: Add statistics export to CSV and JSON
Fix: Prevent crash when loading corrupted manga files
Config: Reduce page spacing to 40px
Refactor: Split database into specialized managers
Test: Add security validation tests
Docs: Update README with new shortcuts
```

**Types**:
- `Feature:` - New feature
- `Fix:` - Bug fix
- `Config:` - Configuration change
- `Refactor:` - Code restructuring
- `Test:` - Add/update tests
- `Docs:` - Documentation
- `Version:` - Version bump
- `Build:` - Build system changes
- `CI:` - CI/CD changes

### Creating a Pull Request

1. **Ensure all tests pass**: `pytest`
2. **Format code**: `black src/ main.py views.py`
3. **Commit changes**: Use descriptive commit messages
4. **Push branch**: `git push -u origin branch-name`
5. **Create PR** with:
   - Clear title
   - Summary of changes
   - Test plan
   - Screenshots (if UI changes)

**PR Template**:
```markdown
## Summary
- Brief description of changes
- Why this change is needed

## Changes Made
- Specific change 1
- Specific change 2

## Test Plan
- [ ] All tests pass
- [ ] Tested on Windows/macOS/Linux
- [ ] No performance regression
- [ ] UI looks correct

## Screenshots
(if applicable)
```

### Recent Commits Pattern

Recent commits show the project patterns:
```
61d2578 - Merge pull request #88 (21 hours ago)
29ca5db - Fix: Migliorata progress bar e rimosso styling hardcoded
2907341 - Feature: Tab Manutenzione Database nelle impostazioni
cbaf952 - Version: Bump to 0.5.0
babbdf2 - Feature: UI Statistiche di lettura con design moderno
d3d85a1 - Feature: Tracking statistiche lettura nel reader (DB v4)
```

---

## Build & Release

### CI/CD Pipeline

GitHub Actions builds for all platforms on:
- Push to `main` or `master`
- Pull requests
- Tags matching `v*`
- Manual dispatch

**Workflow**: `.github/workflows/build.yml`

**Jobs**:
1. `build-windows` - Python 3.11 on windows-latest
2. `build-macos` - Python 3.11 on macos-latest
3. `build-linux` - Python 3.11 on ubuntu-latest
4. `create-release` - Auto-release on version tags

**Artifacts**:
- Retention: 90 days
- Automatic release on `v*` tags

### Release Process

1. **Update version** in code (bump to new version)
2. **Update CHANGELOG.md** with changes
3. **Update README.md** version badge
4. **Commit changes**: `Version: Bump to X.Y.Z`
5. **Create tag**: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
6. **Push tag**: `git push origin vX.Y.Z`
7. **GitHub Actions** automatically creates release

### Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Examples:
- `0.5.0` - Current version
- `0.5.1` - Bug fix release
- `0.6.0` - New feature release
- `1.0.0` - First stable release

---

## Important Conventions

### File Paths

**Always use `pathlib.Path`** for cross-platform compatibility:

```python
from pathlib import Path
from src.paths import get_data_dir, get_base_path

# Get application data directory
data_dir = get_data_dir()  # %LOCALAPPDATA%\MangaReader or ~/.mangareader

# Get base path (works in frozen and unfrozen mode)
base_path = get_base_path()

# Build paths
manga_path = data_dir / "manga" / "my_manga.manga"
settings_path = data_dir / "settings.json"
```

### Settings Access

**Use singleton pattern**:

```python
from src.settings import Settings

# Get settings instance (always same instance)
settings = Settings()

# Get setting
theme = settings.get('theme', default='dark')
cache_size = settings.get('cache_size', default=100)

# Set setting (auto-saves to JSON)
settings.set('theme', 'light')
settings.set('cache_size', 200)
```

### Logging Pattern

```python
from src.logger import get_logger

logger = get_logger(__name__)  # Use module name

# Log at appropriate level
logger.debug(f"Cache hit: {key}")
logger.info(f"Loaded {count} manga from library")
logger.warning(f"Deprecated setting: {old_setting}")
logger.error(f"Failed to load manga: {path}", exc_info=True)
logger.critical(f"Database corrupted: {db_path}")
```

### Constants Usage

**Never use magic numbers**:

```python
# BAD
if cache_size > 200:
    pass

# GOOD
from src.constants import MAX_CACHE_SIZE

if cache_size > MAX_CACHE_SIZE:
    pass
```

### Error Handling

**Use custom exceptions**:

```python
from src.exceptions import DatabaseError, ValidationError

try:
    db.save_metadata(title, author)
except ValidationError as e:
    logger.error(f"Invalid input: {e}")
    show_error_dialog("Invalid manga information")
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    show_error_dialog("Failed to save manga")
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    show_error_dialog("An unexpected error occurred")
```

### Threading Best Practices

**Never block UI thread**:

```python
from PyQt5.QtCore import QThread, pyqtSignal

class ImportThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """Run in background thread."""
        try:
            # Long-running operation
            for i in range(100):
                # Do work
                self.progress.emit(i)
            self.finished.emit(True)
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            self.finished.emit(False)

# Usage
thread = ImportThread(file_path)
thread.progress.connect(update_progress_bar)
thread.finished.connect(on_import_finished)
thread.start()
```

### Qt Signals Pattern

```python
from PyQt5.QtCore import pyqtSignal

class MyWidget(QWidget):
    # Define signals
    manga_selected = pyqtSignal(str)  # manga_path
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self):
        super().__init__()

    def select_manga(self, manga_path: str):
        """Select manga and emit signal."""
        # Validate
        if not Path(manga_path).exists():
            self.error_occurred.emit("Manga file not found")
            return

        # Emit signal
        self.manga_selected.emit(manga_path)

# Connect signals
widget.manga_selected.connect(on_manga_selected)
widget.error_occurred.connect(show_error_dialog)
```

### Resource Management

**Use context managers**:

```python
from src.database.manager import MangaDatabaseManager

# GOOD - Automatic cleanup
with MangaDatabaseManager(manga_path) as db:
    metadata = db.get_metadata()
    # Database closed automatically

# GOOD - Manual cleanup
db = MangaDatabaseManager(manga_path)
try:
    metadata = db.get_metadata()
finally:
    db.close()
```

---

## Performance Considerations

### Database Optimization

- **Use indexes** for frequently queried columns
- **Batch operations** when possible
- **Use WAL mode** for concurrent reads
- **Cache query results** when appropriate

```python
# BAD - Multiple queries
for manga_id in manga_ids:
    metadata = db.get_metadata(manga_id)  # N queries

# GOOD - Single query
metadata_list = db.get_metadata_batch(manga_ids)  # 1 query
```

### Image Handling

- **Use threading** for image conversion
- **Cache frequently accessed images**
- **Lazy load images** when scrolling
- **Preload next/prev pages** in reader

```python
from src.utils.image_converter import ImageConverterPool

# Use thread pool for parallel conversion
with ImageConverterPool() as pool:
    for image_path in image_paths:
        pool.convert_image(image_path)
```

### UI Performance

- **Use virtual lists** for large collections
- **Debounce search input** (300ms delay)
- **Show progress indicators** for long operations
- **Update UI incrementally** (not all at once)

---

## Troubleshooting Common Issues

### Issue: Tests failing on CI but passing locally

**Solution**: Check Python version and dependencies
```bash
# Ensure same Python version as CI (3.11)
python --version

# Reinstall dependencies
pip install -r requirements-dev.txt --force-reinstall
```

### Issue: Database locked error

**Solution**: Ensure proper connection cleanup
```python
# Always close connections
try:
    db = MangaDatabaseManager(path)
    # operations
finally:
    db.close()
```

### Issue: Import failing with "Module not found"

**Solution**: Check PYTHONPATH and imports
```python
# Ensure project root in path (in main.py)
import sys
import os
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

### Issue: UI freezing during long operation

**Solution**: Move to background thread
```python
# Move heavy operation to QThread
thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.process)
worker.finished.connect(thread.quit)
thread.start()
```

---

## Quick Reference

### Key Files to Know

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `src/database/manager.py` | Database facade |
| `src/settings.py` | Settings management |
| `src/constants.py` | All constants |
| `src/exceptions.py` | Exception hierarchy |
| `src/logger.py` | Logging setup |
| `tests/conftest.py` | Test fixtures |
| `.github/workflows/build.yml` | CI/CD pipeline |

### Essential Commands

```bash
# Development
python main.py                      # Run application
pytest                              # Run tests
pytest --cov=src --cov-report=html # Coverage report
black src/ main.py views.py         # Format code

# Build
cd BuildTools && build.bat          # Windows build
cd BuildTools && ./build_mac.sh     # macOS build
cd BuildTools && ./build_linux.sh   # Linux build

# Git
git status                          # Check status
git add .                           # Stage changes
git commit -m "Type: Message"       # Commit
git push -u origin branch-name      # Push
```

### Keyboard Shortcuts (User-facing)

| Shortcut | Action |
|----------|--------|
| F1 | Show shortcuts panel |
| F5 | Refresh library |
| F11 | Toggle fullscreen |
| Ctrl+F | Search focus |
| Ctrl+I | Import manga |
| Ctrl+E | Export manga |
| Ctrl+N | New manga / Night mode (reader) |
| Ctrl+D | Toggle double-page view |
| Ctrl+B | Add bookmark |
| Backspace | Navigate back |
| Esc | Exit |
| ↑/↓ | Zoom in/out (reader) |

---

## Additional Resources

### Documentation Files

- `README.md` - User documentation
- `CHANGELOG.md` - Version history
- `DEVELOPMENT_SUMMARY.md` - v0.1.0 development details
- `PLUGIN_INTEGRATION.md` - Plugin system details
- `TESTS_ADDED.md` - Testing documentation
- `GITHUB_SETUP.md` - GitHub Actions setup

### External Links

- **Repository**: https://github.com/deam411/MangaReader
- **Issues**: https://github.com/deam411/MangaReader/issues
- **Releases**: https://github.com/deam411/MangaReader/releases
- **Actions**: https://github.com/deam411/MangaReader/actions

---

## AI Assistant Guidelines

When working on this codebase:

1. **Always read context** before making changes
2. **Follow existing patterns** (don't reinvent)
3. **Test your changes** (run pytest)
4. **Update documentation** when needed
5. **Use type hints** and docstrings
6. **Handle errors properly** (custom exceptions)
7. **Log important events** (use logger)
8. **Validate user input** (security first)
9. **Commit with clear messages** (conventional commits)
10. **Ask for clarification** when uncertain

### When Adding Features

- [ ] Check if similar feature exists
- [ ] Plan database changes (if needed)
- [ ] Write tests first (TDD when possible)
- [ ] Implement with error handling
- [ ] Update documentation
- [ ] Test on multiple platforms (if UI)
- [ ] Create PR with summary

### When Fixing Bugs

- [ ] Reproduce the issue
- [ ] Write test that fails
- [ ] Fix the issue
- [ ] Verify test passes
- [ ] Check for similar issues
- [ ] Update CHANGELOG if user-facing

### Code Review Checklist

- [ ] Code follows project conventions
- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black`)
- [ ] Type hints present
- [ ] Docstrings clear
- [ ] Error handling proper
- [ ] Security considerations addressed
- [ ] Performance acceptable
- [ ] Documentation updated

---

**Last Updated**: 2025-11-14
**Maintainer**: deam411
**License**: MIT

---

*This document is maintained for AI assistants working on the MangaReader codebase. Keep it updated as the project evolves.*
