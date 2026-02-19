"""
Utility functions for GUI operations
Provides common dialogs, confirmations, and helper functions
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog, QWidget
from PySide6.QtCore import Qt


def confirm_unsaved_changes(parent: QWidget | None = None) -> int:
    """
    Show standardized unsaved changes dialog.
    Returns QMessageBox.Save, Discard, or Cancel
    """
    return QMessageBox.question(
        parent,
        "Unsaved Changes",
        "You have unsaved changes. What do you want to do?",
        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        QMessageBox.Save,
    )


def show_error(parent: QWidget | None, title: str, message: str) -> None:
    """Show an error message dialog."""
    QMessageBox.critical(parent, title, message)


def show_info(parent: QWidget | None, title: str, message: str) -> None:
    """Show an info message dialog."""
    QMessageBox.information(parent, title, message)


def show_warning(parent: QWidget | None, title: str, message: str) -> None:
    """Show a warning message dialog."""
    QMessageBox.warning(parent, title, message)


def confirm_delete(parent: QWidget | None, item_name: str, count: int = 1) -> bool:
    """
    Show standardized delete confirmation.
    Returns True if user confirms deletion.
    """
    item_text = f"'{item_name}'" if count == 1 else f"{count} items"

    reply = QMessageBox.question(
        parent,
        "Confirm Delete",
        f"Delete {item_text}?\n\nThis action cannot be undone.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def input_text(
    parent: QWidget | None,
    title: str,
    label: str,
    default: str = "",
    placeholder: str = "",
) -> tuple[str, bool]:
    """
    Show input dialog and return (text, ok).
    """
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(default)
    if placeholder:
        dialog.setInputMode(QInputDialog.TextInput)

    ok = dialog.exec()
    return dialog.textValue(), bool(ok)


def select_directory(
    parent: QWidget | None,
    title: str = "Select Directory",
    default: Path | str | None = None,
) -> Path | None:
    """Show directory selection dialog."""
    path = QFileDialog.getExistingDirectory(
        parent,
        title,
        str(default) if default else "",
        QFileDialog.ShowDirsOnly,
    )
    return Path(path) if path else None


def format_file_size(size: int) -> str:
    """Format file size in human-readable format."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_file_type_icon(path: Path) -> str:
    """Get emoji icon for file type."""
    if path.suffix == ".md":
        return "📝"
    if path.suffix in {".py", ".js", ".ts", ".cpp", ".c", ".rs"}:
        return "💻"
    if path.suffix in {".json", ".yaml", ".yml", ".toml"}:
        return "⚙️"
    if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg"}:
        return "🖼️"
    return "📄"


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes."""
    if not text:
        return 0
    word_count = len(text.split())
    return max(1, (word_count + words_per_minute - 1) // words_per_minute)
