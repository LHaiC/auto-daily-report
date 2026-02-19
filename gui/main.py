"""
Main entry point for Daily Report Client GUI
Refactored with modular architecture
"""

from __future__ import annotations

import os
import sys
import json
import datetime as dt
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtGui import QFont, QAction, QKeySequence, QIcon
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject

from backend import NoteManager
from styles import ThemeManager
from utils import confirm_unsaved_changes, format_file_size, show_error, show_info
from dialogs import BaseDialog, ProgressMixin
from status_bar import EnhancedStatusBar

# Import manage_env from scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from manage_env import load_env

from components import (
    MarkdownEditor,
    WelcomeDialog,
    FileBrowserDialog,
    SyncDialog,
    GenerateReportDialog,
    GenerateWeeklyDialog,
    EnvSettingsDialog,
)
from PySide6.QtWidgets import QTextEdit

# Ensure GUI directory is in path
sys.path.append(os.path.dirname(__file__))


def load_shortcuts():
    """Load keyboard shortcuts configuration."""
    return {
        "new_file": "Ctrl+N",
        "open_file": "Ctrl+O",
        "save_file": "Ctrl+S",
        "save_as": "Ctrl+Shift+S",
        "close": "Ctrl+W",
        "quit": "Ctrl+Q",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Shift+Z",
        "cut": "Ctrl+X",
        "copy": "Ctrl+C",
        "paste": "Ctrl+V",
        "find": "Ctrl+F",
        "replace": "Ctrl+H",
        "preview_sync": "Ctrl+P",
        "toggle_preview": "F12",
        "generate_report": "Ctrl+G",
        "sync_repo": "Ctrl+Shift+G",
        "browse_scratch": "Ctrl+B",
        "browse_reports": "Ctrl+R",
        "settings": "Ctrl+,",
        "go_home": "Ctrl+H",
        "toggle_theme": "Ctrl+Shift+T",
    }


class MainWindow(QMainWindow):
    def __init__(self, manager: NoteManager, current_file: Path = None):
        super().__init__()
        self.manager = manager
        self.current_file = current_file
        self.has_unsaved_changes = False
        self.is_new_file = False  # Track if file was newly created
        self.theme_manager = ThemeManager("dark")
        self.shortcuts = load_shortcuts()

        # Editor state
        self.last_content = ""
        self.preview_scroll_ratio = 0.0
        self.file_watcher = None

        self.setup_ui()
        self.setup_actions()
        self.setup_shortcuts()
        self.setup_autosave()
        self.setup_file_watcher()

        # Load initial file or show empty editor
        if current_file and current_file.exists():
            self.load_file(current_file)
        else:
            # Show empty editor for new file
            self.editor.setPlainText(f"# Notes for {dt.date.today().isoformat()}\n\n")
            self.status_bar.set_file(None)
            self.status_bar.update_stats("")

    def setup_file_watcher(self):
        """Setup file system watcher for external file changes."""
        from PySide6.QtCore import QFileSystemWatcher

        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.fileChanged.connect(self.on_file_changed)

    def setup_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Daily Report Client")
        self.resize(1400, 900)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # Editor panel
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_toolbar = self.create_editor_toolbar()
        editor_layout.addWidget(editor_toolbar)

        self.editor = MarkdownEditor(self)
        self.editor.textChanged.connect(self.on_content_changed)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        editor_layout.addWidget(self.editor)

        self.splitter.addWidget(editor_panel)

        # Preview panel
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_toolbar = self.create_preview_toolbar()
        preview_layout.addWidget(preview_toolbar)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        preview_layout.addWidget(self.preview)

        self.splitter.addWidget(preview_panel)

        # Set splitter proportions
        self.splitter.setSizes([700, 700])

        # Status bar
        self.status_bar = EnhancedStatusBar(self.theme_manager, self)
        self.setStatusBar(self.status_bar)

        # Load window settings
        self.load_settings()

    def create_editor_toolbar(self):
        """Create toolbar for editor panel."""
        from PySide6.QtWidgets import QToolBar, QLabel, QPushButton

        toolbar = QToolBar("Editor Tools")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar { spacing: 16px; padding: 4px; }
            QToolBar::separator {
                width: 16px;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
                min-width: 36px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
            }
        """)

        # Cursor position
        self.cursor_label = QLabel("📍 1:1")
        self.cursor_label.setStyleSheet("padding: 0 12px; color: #94a3b8;")
        self.cursor_label.setToolTip("Cursor position (line:column)")
        toolbar.addWidget(self.cursor_label)

        toolbar.addSeparator()

        # Editor actions with proper buttons
        bold_btn = QPushButton("B")
        bold_btn.setToolTip("Bold (Ctrl+B)")
        bold_btn.clicked.connect(lambda: self.wrap_selection("**", "**"))
        toolbar.addWidget(bold_btn)

        italic_btn = QPushButton("I")
        italic_btn.setToolTip("Italic (Ctrl+I)")
        italic_btn.setStyleSheet("font-style: italic;")
        italic_btn.clicked.connect(lambda: self.wrap_selection("*", "*"))
        toolbar.addWidget(italic_btn)

        code_btn = QPushButton("<>")
        code_btn.setToolTip("Inline code")
        code_btn.clicked.connect(lambda: self.wrap_selection("`", "`"))
        toolbar.addWidget(code_btn)

        quote_btn = QPushButton("❝")
        quote_btn.setToolTip("Quote")
        quote_btn.clicked.connect(self.insert_quote)
        toolbar.addWidget(quote_btn)

        return toolbar

    def wrap_selection(self, prefix: str, suffix: str):
        """Wrap selected text with prefix/suffix, or insert at cursor if no selection."""
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()

        if selected_text:
            # Wrap selected text
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            # Insert with placeholder
            cursor.insertText(f"{prefix}text{suffix}")
            # Select the placeholder
            cursor.setPosition(cursor.position() - len(suffix) - 4)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, 4)
            self.editor.setTextCursor(cursor)

        self.editor.setFocus()

    def insert_quote(self):
        """Insert a quote block."""
        cursor = self.editor.textCursor()
        cursor.insertText("> ")
        self.editor.setFocus()

    def create_preview_toolbar(self):
        """Create toolbar for preview panel."""
        from PySide6.QtWidgets import QToolBar, QLabel, QCheckBox

        toolbar = QToolBar("Preview Tools")
        toolbar.setMovable(False)

        # Preview toggle
        self.preview_sync = QCheckBox("Sync Scroll")
        self.preview_sync.setChecked(True)
        self.preview_sync.setToolTip("Synchronize editor and preview scrolling")
        toolbar.addWidget(self.preview_sync)

        toolbar.addSeparator()

        # Preview label
        self.preview_label = QLabel("👁️ Preview")
        toolbar.addWidget(self.preview_label)

        return toolbar

    def setup_actions(self):
        """Setup menu actions."""
        from PySide6.QtWidgets import QMenuBar

        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        file_menu.addAction("&Home", self.go_home, QKeySequence("Ctrl+Shift+H"))
        file_menu.addSeparator()
        file_menu.addAction("&New", self.create_new_file, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Open...", self.browse_scratch, QKeySequence("Ctrl+O"))
        file_menu.addAction("&Save", self.save_file, QKeySequence("Ctrl+S"))
        file_menu.addAction(
            "Save &As...", self.save_as_file, QKeySequence("Ctrl+Shift+S")
        )
        file_menu.addSeparator()
        file_menu.addAction("&Close", self.close_file, QKeySequence("Ctrl+W"))
        file_menu.addAction("E&xit", self.close, QKeySequence("Ctrl+Q"))

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        edit_menu.addAction("&Undo", self.editor.undo, QKeySequence("Ctrl+Z"))
        edit_menu.addAction("&Redo", self.editor.redo, QKeySequence("Ctrl+Shift+Z"))
        edit_menu.addSeparator()
        edit_menu.addAction("Cu&t", self.editor.cut, QKeySequence("Ctrl+X"))
        edit_menu.addAction("&Copy", self.editor.copy, QKeySequence("Ctrl+C"))
        edit_menu.addAction("&Paste", self.editor.paste, QKeySequence("Ctrl+V"))
        edit_menu.addSeparator()
        edit_menu.addAction("&Find...", self.find_text, QKeySequence("Ctrl+F"))

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        tools_menu.addAction(
            "&Generate Report", self.generate_report, QKeySequence("Ctrl+G")
        )
        tools_menu.addAction(
            "&Sync Repository", self.sync_repository, QKeySequence("Ctrl+Shift+G")
        )
        tools_menu.addSeparator()
        tools_menu.addAction(
            "Browse &Scratch", self.browse_scratch, QKeySequence("Ctrl+B")
        )
        tools_menu.addAction(
            "Browse &Reports", self.browse_reports, QKeySequence("Ctrl+R")
        )
        tools_menu.addSeparator()
        tools_menu.addAction("&Settings...", self.open_settings, QKeySequence("Ctrl+,"))

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&Keyboard Shortcuts", self.show_shortcuts)
        help_menu.addAction("&About", self.show_about)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Editor-specific shortcuts
        self.editor.add_shortcut("Ctrl+/", lambda: self.insert_text("<!-- -->", 5, 7))
        self.editor.add_shortcut(
            "Ctrl+L", lambda: self.insert_text("[link](url)", 1, 7)
        )
        self.editor.add_shortcut("Ctrl+K", lambda: self.insert_text("`code`", 1, 5))

        # Preview toggle
        from PySide6.QtGui import QShortcut

        QShortcut(QKeySequence("F12"), self).activated.connect(self.toggle_preview)

    def setup_autosave(self):
        """Setup auto-save timer."""
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)  # 30 seconds

    def load_settings(self):
        """Load saved window settings."""
        config_path = Path.home() / ".daily_report_client.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))

                # Restore window geometry
                if "geometry" in data:
                    self.restoreGeometry(bytes.fromhex(data["geometry"]))
                if "window_state" in data:
                    self.restoreState(bytes.fromhex(data["window_state"]))
                if "splitter_state" in data:
                    self.splitter.restoreState(bytes.fromhex(data["splitter_state"]))
            except Exception:
                pass

    def save_settings(self):
        """Save window settings."""
        config_path = Path.home() / ".daily_report_client.json"
        data = {
            "theme": self.theme_manager.current_theme,
            "geometry": self.saveGeometry().toHex().data().decode(),
            "window_state": self.saveState().toHex().data().decode(),
            "splitter_state": self.splitter.saveState().toHex().data().decode(),
        }
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def on_content_changed(self):
        """Handle editor content changes."""
        current_content = self.editor.toPlainText()

        if current_content == self.last_content:
            return

        self.has_unsaved_changes = True
        self.last_content = current_content

        # Update statistics
        self.status_bar.update_stats(current_content)

        # Update preview with debounce
        if hasattr(self, "_preview_timer"):
            self._preview_timer.stop()

        from PySide6.QtCore import QTimer

        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self.update_preview)
        self._preview_timer.start(500)  # Update after 500ms

    def update_cursor_position(self):
        """Update cursor position display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_label.setText(f"📍 {line}:{column}")

    def create_new_file(self):
        """Create a new file."""
        if self.has_unsaved_changes:
            reply = confirm_unsaved_changes(self)
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        # Create new file
        today = dt.date.today().isoformat()
        default_name = f"{today}-note.md"
        path, ok = QInputDialog.getText(
            self,
            "New File",
            "File name:",
            text=default_name,
        )
        if ok and path:
            full_path = Path(self.manager.scratch_dir) / path
            full_path.write_text(f"# {path}\n\n", encoding="utf-8")
            self.load_file(full_path)

    def load_file(self, path: Path, is_new: bool = False):
        """Load a file into editor."""
        try:
            # Stop watching previous file
            if self.current_file and self.file_watcher:
                self.file_watcher.removePath(str(self.current_file))

            content = path.read_text(encoding="utf-8")
            self.editor.setPlainText(content)
            self.current_file = path
            self.last_content = content
            self.has_unsaved_changes = False
            self.is_new_file = is_new

            # Watch the file for external changes
            if self.file_watcher:
                self.file_watcher.addPath(str(path))

            # Update UI
            self.status_bar.set_file(str(path))
            self.status_bar.update_stats(content)
            self.status_bar.showMessage(f"Loaded: {path.name}", 3000)
            self.update_preview()
        except Exception as e:
            show_error(self, "Load Error", f"Failed to load file: {e}")

    def on_file_changed(self, path: str):
        """Handle external file changes."""
        if self.has_unsaved_changes:
            # User has unsaved changes, don't auto-reload
            return

        reply = QMessageBox.question(
            self,
            "File Changed",
            f"The file has been modified externally. Do you want to reload it?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.load_file(Path(path))

    def save_file(self):
        """Save current file."""
        if not self.current_file:
            return self.save_as_file()

        try:
            content = self.editor.toPlainText()
            self.current_file.write_text(content, encoding="utf-8")
            self.has_unsaved_changes = False
            self.last_content = content

            self.status_bar.showMessage(f"Saved: {self.current_file.name}", 3000)
            self.status_bar.set_unsaved_changes(False)
        except Exception as e:
            show_error(self, "Save Error", f"Failed to save file: {e}")

    def save_as_file(self):
        """Save as new file."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            str(self.current_file) if self.current_file else "",
            "Markdown Files (*.md)",
        )
        if path:
            self.current_file = Path(path)
            self.save_file()

    def close_file(self):
        """Close current file."""
        if self.has_unsaved_changes:
            reply = confirm_unsaved_changes(self)
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Discard:
                # Delete newly created file if user chooses to discard changes
                if (
                    self.is_new_file
                    and self.current_file
                    and self.current_file.exists()
                ):
                    try:
                        self.current_file.unlink()
                    except Exception:
                        pass
            elif reply == QMessageBox.Cancel:
                return

        self.editor.clear()
        self.current_file = None
        self.has_unsaved_changes = False
        self.is_new_file = False
        self.status_bar.set_file(None)

    def go_home(self):
        """Return to welcome screen."""
        from components import WelcomeDialog

        if self.has_unsaved_changes:
            reply = confirm_unsaved_changes(self)
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Discard:
                # Delete newly created file if user chooses to discard changes
                if (
                    self.is_new_file
                    and self.current_file
                    and self.current_file.exists()
                ):
                    try:
                        self.current_file.unlink()
                    except Exception:
                        pass
            elif reply == QMessageBox.Cancel:
                return

        dialog = WelcomeDialog(self.manager, self)
        dialog.fileSelected.connect(self.load_file)
        dialog.createNew.connect(self.on_create_new_from_welcome)
        dialog.exec()

    def on_create_new_from_welcome(self, name: str, date_str: str):
        """Handle new file creation from welcome dialog."""
        try:
            path = self.manager.create_scratch_note(name, date_str)
            self.load_file(path, is_new=True)
        except Exception as e:
            show_error(self, "Error", f"Failed to create note: {e}")

    def autosave(self):
        """Auto-save current file."""
        if not self.has_unsaved_changes or not self.current_file:
            return

        try:
            content = self.editor.toPlainText()
            self.current_file.write_text(content, encoding="utf-8")
            self.status_bar.show_autosave(True)
        except Exception:
            self.status_bar.show_autosave(False)

    def insert_text(self, text: str, select_start: int = 0, select_end: int = 0):
        """Insert text at cursor position."""
        cursor = self.editor.textCursor()
        cursor.insertText(text)

        # Select part of inserted text (for editing)
        if select_start != select_end:
            cursor.setPosition(cursor.position() - len(text) + select_start)
            from PySide6.QtGui import QTextCursor

            cursor.movePosition(
                QTextCursor.Right, QTextCursor.KeepAnchor, select_end - select_start
            )
            self.editor.setTextCursor(cursor)

        self.editor.setFocus()  # Keep focus on editor

    def find_text(self):
        """Show find dialog."""
        text, ok = QInputDialog.getText(self, "Find", "Search for:")
        if ok and text:
            self.editor.find(text)

    def update_preview(self):
        """Update Markdown preview."""
        import markdown

        md_text = self.editor.toPlainText()
        html = markdown.markdown(
            md_text, extensions=["fenced_code", "tables", "nl2br", "sane_lists"]
        )

        css = self.theme_manager.get_markdown_preview_css()
        self.preview.setHtml(css + html)

    def toggle_preview(self):
        """Toggle preview panel visibility."""
        preview_panel = self.splitter.widget(1)
        preview_panel.setVisible(not preview_panel.isVisible())

    def browse_scratch(self):
        """Browse scratch files."""
        dialog = FileBrowserDialog(self.manager, "scratch", self)
        dialog.fileSelected.connect(self.load_file)
        dialog.exec()

    def browse_reports(self):
        """Browse generated reports."""
        dialog = FileBrowserDialog(self.manager, "reports", self)
        dialog.fileSelected.connect(self.load_file)
        dialog.exec()

    def generate_report(self):
        """Generate daily report."""
        dialog = GenerateReportDialog(self.manager, self.current_file, self)
        dialog.exec()

    def sync_repository(self):
        """Sync with Git repository."""
        dialog = SyncDialog(self.manager, self)
        dialog.exec()

    def open_settings(self):
        """Open settings dialog."""
        dialog = EnvSettingsDialog(self)
        dialog.exec()

    def show_shortcuts(self):
        """Show keyboard shortcuts help."""
        shortcuts_html = ""
        for action, shortcut in self.shortcuts.items():
            action_name = action.replace("_", " ").title()
            shortcuts_html += (
                f"<tr><td><b>{action_name}</b></td><td>{shortcut}</td></tr>"
            )

        html = f"""
        <h3>⌨️ Keyboard Shortcuts</h3>
        <table width="100%" cellpadding="5">
            {shortcuts_html}
        </table>
        <p><small>Press <b>F12</b> to toggle preview panel</small></p>
        """

        show_info(self, "Keyboard Shortcuts", html)

    def show_about(self):
        """Show about dialog."""
        show_info(
            self,
            "About Daily Report Client",
            "Daily Report Client\n\nA modern GUI for managing technical journals and daily reports.\n\nBuilt with PySide6.",
        )

    def closeEvent(self, event):
        """Handle window close event."""
        if self.has_unsaved_changes:
            reply = confirm_unsaved_changes(self)
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Discard:
                # Delete newly created file if user chooses to discard changes
                if (
                    self.is_new_file
                    and self.current_file
                    and self.current_file.exists()
                ):
                    try:
                        self.current_file.unlink()
                    except Exception:
                        pass  # Best effort deletion
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        # Save settings
        self.save_settings()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set application style
    theme_manager = ThemeManager("dark")
    app.setStyleSheet(theme_manager.get_app_stylesheet())

    # Set font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize backend
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = NoteManager(repo_root)

    # Show welcome dialog first
    from components import WelcomeDialog

    welcome = WelcomeDialog(manager)
    welcome.setModal(False)  # Allow interaction with main window after

    current_file = None

    def on_file_selected(path):
        nonlocal current_file
        current_file = path

    def on_create_new(name, date_str):
        nonlocal current_file
        try:
            current_file = manager.create_scratch_note(name, date_str)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(None, "Error", f"Failed to create note: {e}")

    welcome.fileSelected.connect(on_file_selected)
    welcome.createNew.connect(on_create_new)

    if welcome.exec() != welcome.accepted:
        return

    if not current_file:
        return

    # Create main window with selected file
    window = MainWindow(manager, current_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
