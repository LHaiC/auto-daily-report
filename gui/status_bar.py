"""
Enhanced status bar with multiple information panels
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from PySide6.QtWidgets import QStatusBar, QLabel, QPushButton
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QFont

from styles import ThemeManager


class EnhancedStatusBar(QStatusBar):
    """
    Enhanced status bar with multiple information panels and automatic updates.
    """

    autosave_triggered = Signal()

    def __init__(self, theme_manager: ThemeManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._unsaved_changes = False
        self._file_path = None
        self._update_timer = None

        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        """Initialize UI components."""
        # File info panel
        self.file_label = QLabel("No file")
        self.file_label.setToolTip("Current file path")
        self.addPermanentWidget(self.file_label, 1)

        # Reading stats panel
        self.stats_label = QLabel("📊 0 words • 0 lines")
        self.stats_label.setToolTip("Word and line count")
        self.addPermanentWidget(self.stats_label, 0)

        # Autosave indicator
        self.autosave_label = QLabel("💾")
        self.autosave_label.setToolTip("Auto-save status")
        self.addPermanentWidget(self.autosave_label, 0)

        # Theme toggle
        self.theme_button = QPushButton("🌓")
        self.theme_button.setToolTip("Toggle theme (Ctrl+Shift+T)")
        self.theme_button.setFlat(True)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.addPermanentWidget(self.theme_button, 0)

        # Set font
        font = QFont("monospace", 9)
        font.setStyleHint(QFont.Monospace)
        for widget in [self.file_label, self.stats_label, self.autosave_label]:
            widget.setFont(font)

        self.showMessage("Ready", 2000)

    def update_styles(self):
        """Update styles based on current theme."""
        colors = self.theme_manager.get_colors()
        self.setStyleSheet(f"""
            QStatusBar {{
                background-color: {colors["surface"]};
                color: {colors["text_secondary"]};
                border-top: 1px solid {colors["border"]};
                padding: 6px 12px;
                font-size: 12px;
            }}
            QStatusBar QLabel {{
                color: {colors["text_secondary"]};
                padding: 0 10px;
            }}
            QStatusBar QPushButton {{
                background-color: transparent;
                border: none;
                color: {colors["text_secondary"]};
                padding: 4px 8px;
            }}
            QStatusBar QPushButton:hover {{
                color: {colors["primary"]};
            }}
        """)

    def set_unsaved_changes(self, has_changes: bool):
        """Update unsaved changes indicator."""
        self._unsaved_changes = has_changes
        self.update_file_display()

    def set_file(self, file_path: Optional[str]):
        """Set current file path."""
        self._file_path = file_path
        self.update_file_display()

    def update_file_display(self):
        """Update file label display."""
        if self._file_path:
            import os

            name = os.path.basename(self._file_path)
            status = "•" if self._unsaved_changes else ""
            self.file_label.setText(f"📄 {name} {status}")
            self.file_label.setToolTip(self._file_path)
        else:
            self.file_label.setText(
                "📄 New file" if self._unsaved_changes else "📄 New file •"
            )

    def update_stats(self, text: str):
        """Update word and line count statistics."""
        if not text:
            self.stats_label.setText("📊 0 words • 0 lines")
            return

        word_count = len(text.split())
        line_count = len(text.splitlines())

        # Format with K for thousands
        def format_num(n: int) -> str:
            if n >= 1000:
                return f"{n / 1000:.1f}K"
            return str(n)

        self.stats_label.setText(
            f"📊 {format_num(word_count)} words • {format_num(line_count)} lines"
        )

        # Estimate read time
        read_time = max(1, (word_count + 199) // 200)  # 200 words per minute
        self.stats_label.setToolTip(
            f"Reading time: ~{read_time} minute{'s' if read_time > 1 else ''}"
        )

    def show_autosave(self, success: bool = True):
        """Show autosave status."""
        if success:
            self.autosave_label.setText("✅")
            self.autosave_label.setToolTip(
                f"Auto-saved at {dt.datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            self.autosave_label.setText("❌")
            self.autosave_label.setToolTip("Auto-save failed")

        # Reset after 2 seconds
        from PySide6.QtCore import QTimer

        QTimer.singleShot(2000, self.reset_autosave_indicator)

    def reset_autosave_indicator(self):
        """Reset autosave indicator to default state."""
        self.autosave_label.setText("💾")
        self.autosave_label.setToolTip("Auto-save enabled")

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        current = self.theme_manager.current_theme
        new_theme = "light" if current == "dark" else "dark"
        self.theme_manager.set_theme(new_theme)
        self.update_styles()
        self.theme_button.setToolTip(f"Toggle theme - Current: {new_theme}")
        self.showMessage(f"Switched to {new_theme} theme", 2000)
