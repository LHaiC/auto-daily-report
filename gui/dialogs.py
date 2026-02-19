"""
Base dialog classes with common functionality
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt

from styles import ThemeManager
from utils import escape_html


class BaseDialog(QDialog):
    """
    Base class for all dialogs with consistent styling and layout.
    """

    def __init__(self, theme_manager: ThemeManager, title: str = "", parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle(title)
        self.setModal(True)

        # Default size
        self.resize(600, 400)

        self.setup_base_ui()
        self.apply_styles()

    def setup_base_ui(self):
        """Set up the base layout structure."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(24, 24, 24, 24)

        # Header section
        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(8)

        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet(self._get_header_style())
        self.header_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(self._get_subtitle_style())
        self.subtitle_label.hide()
        self.header_layout.addWidget(self.subtitle_label)

        self.main_layout.addLayout(self.header_layout)

        # Content area
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout, 1)

        # Button area
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.main_layout.addLayout(self.button_layout)

    def set_title(self, title: str):
        """Set dialog title."""
        self.setWindowTitle(title)
        self.title_label.setText(title)

    def set_subtitle(self, subtitle: str):
        """Set dialog subtitle/description."""
        self.subtitle_label.setText(escape_html(subtitle))
        self.subtitle_label.setVisible(bool(subtitle))

    def add_button(
        self, text: str, callback=None, variant: str = "primary", default: bool = False
    ) -> QPushButton:
        """Add a button to the dialog button area."""
        from PySide6.QtWidgets import QDialogButtonBox

        btn = QPushButton(text)
        btn.clicked.connect(callback or self.reject)

        if variant == "primary":
            btn.setDefault(True)
        elif variant == "danger":
            btn.setStyleSheet(self.theme_manager.get_button_style("danger"))
        elif variant == "secondary":
            btn.setStyleSheet(self.theme_manager.get_button_style("secondary"))

        if default:
            btn.setDefault(True)

        self.button_layout.addWidget(btn)
        return btn

    def apply_styles(self):
        """Apply theme styles to the dialog."""
        self.setStyleSheet(self.theme_manager.get_dialog_style())

    def _get_header_style(self) -> str:
        """Get header label style."""
        colors = self.theme_manager.get_colors()
        return f"""
            font-size: 20px;
            font-weight: bold;
            color: {colors["text"]};
            padding-bottom: 8px;
            border-bottom: 1px solid {colors["border"]};
        """

    def _get_subtitle_style(self) -> str:
        """Get subtitle label style."""
        colors = self.theme_manager.get_colors()
        return f"""
            font-size: 13px;
            color: {colors["text_secondary"]};
            padding-top: 4px;
        """


class ProgressMixin:
    """Mixin to add progress indication to dialogs."""

    def __init__(self):
        self._progress_label: Optional[QLabel] = None

    def setup_progress_ui(self, text: str = ""):
        """Set up progress indicator UI elements."""
        self._progress_label = QLabel(text or "Ready")
        self._progress_label.setAlignment(Qt.AlignCenter)
        self._progress_label.setStyleSheet("padding: 20px; font-size: 14px;")
        self.content_layout.addWidget(self._progress_label)

    def show_progress(self, text: str, status: str = "pending"):
        """Update progress message."""
        if not self._progress_label:
            self.setup_progress_ui()

        from styles import ThemeManager

        colors = getattr(self, "theme_manager", ThemeManager("dark")).get_colors()

        if status == "success":
            color = colors["success"]
        elif status == "error":
            color = colors["error"]
            self._progress_label.setText(f"❌ {text}")
        elif status == "running":
            color = colors["primary"]
            self._progress_label.setText(f"⏳ {text}")
        else:
            color = colors["text_secondary"]
            self._progress_label.setText(text)

        self._progress_label.setStyleSheet(
            f"padding: 20px; font-size: 14px; color: {color};"
        )

    def show_success(self, text: str, message: str = ""):
        """Show success message."""
        self.show_progress(f"✅ {text}", "success")

    def show_error(self, text: str):
        """Show error message."""
        self.show_progress(f"❌ {text}", "error")


class FormMixin:
    """Mixin for forms with labels and inputs."""

    def create_form_row(self, label_text: str, widget, stretch_label: bool = False):
        """Create a form row with label and input."""
        from PySide6.QtWidgets import QHBoxLayout, QLabel

        colors = self.theme_manager.get_colors()

        row = QHBoxLayout()
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 12px;")
        if stretch_label:
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setMinimumWidth(100)
        row.addWidget(label, 0 if not stretch_label else 0)

        row.addWidget(widget, 1)

        return row
