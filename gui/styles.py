"""
Theme system for Daily Report Client
Supports light/dark theme switching and consistent styling across all UI components
"""

from __future__ import annotations

from typing import Dict, Any
from PySide6.QtCore import QObject


class ThemeManager(QObject):
    """Manages application themes and provides consistent styling."""

    THEMES = {
        "dark": {
            "name": "Dark (Makise Kurisu)",
            "colors": {
                "primary": "#38bdf8",
                "primary_dark": "#0ea5e9",
                "primary_dim": "rgba(56, 189, 248, 0.1)",
                "success": "#4ade80",
                "warning": "#fbbf24",
                "error": "#f87171",
                "background": "#0f172a",
                "surface": "#1e293b",
                "surface_bright": "#334155",
                "text": "#f8fafc",
                "text_secondary": "#94a3b8",
                "text_muted": "#64748b",
                "border": "#334155",
                "input_bg": "#020617",
            },
        },
        "light": {
            "name": "Light",
            "colors": {
                "primary": "#0ea5e9",
                "primary_dark": "#0284c7",
                "primary_dim": "rgba(14, 165, 233, 0.1)",
                "success": "#16a34a",
                "warning": "#eab308",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f8fafc",
                "surface_bright": "#f1f5f9",
                "text": "#0f172a",
                "text_secondary": "#475569",
                "text_muted": "#64748b",
                "border": "#e2e8f0",
                "input_bg": "#ffffff",
            },
        },
    }

    def __init__(self, theme: str = "dark"):
        super().__init__()
        self.current_theme = theme
        self._cached_styles: Dict[str, str] = {}

    def set_theme(self, theme: str):
        """Switch to a different theme."""
        if theme in self.THEMES:
            self.current_theme = theme
            self._cached_styles.clear()

    def get_color(self, key: str) -> str:
        """Get a color value from current theme."""
        return self.THEMES[self.current_theme]["colors"][key]

    def get_colors(self) -> Dict[str, str]:
        """Get all colors for current theme."""
        return self.THEMES[self.current_theme]["colors"].copy()

    def get_button_style(
        self,
        variant: str = "primary",
        hover_effect: bool = True,
        disabled_style: bool = True,
    ) -> str:
        """Generate button stylesheet."""
        cache_key = f"btn_{variant}_{hover_effect}_{disabled_style}"
        if cache_key in self._cached_styles:
            return self._cached_styles[cache_key]

        colors = self.get_colors()

        if variant == "primary":
            bg = colors["primary"]
            bg_hover = colors["primary_dark"]
            text_color = colors["background"]
        elif variant == "secondary":
            bg = "transparent"
            bg_hover = colors["primary_dim"]
            text_color = colors["primary"]
        elif variant == "danger":
            bg = colors["error"]
            bg_hover = colors["error"]
            text_color = colors["text"]
        elif variant == "success":
            bg = colors["success"]
            bg_hover = colors["success"]
            text_color = colors["text"]
        else:
            bg = colors["surface"]
            bg_hover = colors["surface_bright"]
            text_color = colors["text"]

        style = f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 14px;
            }}
        """

        if hover_effect:
            style += f"""
                QPushButton:hover {{
                    background-color: {bg_hover};
                }}
            """

        if disabled_style:
            style += f"""
                QPushButton:disabled {{
                    background-color: {colors["border"]};
                    color: {colors["text_muted"]};
                }}
            """

        if variant == "secondary":
            style = style.replace(
                "border: none;", f"border: 1px solid {colors['primary']};"
            ).replace(
                "background-color: transparent;",
                f"background-color: transparent; border: 2px solid {colors['primary']};",
            )

        self._cached_styles[cache_key] = style
        return style

    def get_input_style(self) -> str:
        """Generate input field stylesheet."""
        cache_key = "input"
        if cache_key in self._cached_styles:
            return self._cached_styles[cache_key]

        colors = self.get_colors()
        style = f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors["input_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 10px;
                color: {colors["text"]};
                selection-background-color: {colors["primary"]};
                selection-color: {colors["input_bg"]};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {colors["primary"]};
                outline: none;
            }}
        """
        self._cached_styles[cache_key] = style
        return style

    def get_table_style(self) -> str:
        """Generate table widget stylesheet."""
        cache_key = "table"
        if cache_key in self._cached_styles:
            return self._cached_styles[cache_key]

        colors = self.get_colors()
        style = f"""
            QTableWidget {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                gridline-color: {colors["border"]};
                color: {colors["text"]};
                selection-background-color: {colors["primary_dim"]};
                selection-color: {colors["primary"]};
            }}
            QHeaderView::section {{
                background-color: {colors["background"]};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {colors["primary"]};
                font-weight: bold;
                color: {colors["primary"]};
            }}
        """
        self._cached_styles[cache_key] = style
        return style

    def get_dialog_style(self) -> str:
        """Generate dialog base stylesheet."""
        cache_key = "dialog"
        if cache_key in self._cached_styles:
            return self._cached_styles[cache_key]

        colors = self.get_colors()
        style = f"""
            QDialog {{
                background-color: {colors["background"]};
            }}
            QLabel {{
                color: {colors["text"]};
            }}
        """
        self._cached_styles[cache_key] = style
        return style

    def get_app_stylesheet(self) -> str:
        """Generate application-wide stylesheet."""
        colors = self.get_colors()
        return f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            QWidget {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
            QToolBar {{
                background-color: {colors["surface"]};
                border-bottom: 1px solid {colors["border"]};
                spacing: 10px;
                padding: 5px;
            }}
            QToolButton {{
                background-color: transparent;
                border-radius: 4px;
                color: {colors["text"]};
                padding: 6px;
            }}
            QToolButton:hover {{
                background-color: {colors["primary_dim"]};
                color: {colors["primary"]};
            }}
            QStatusBar {{
                background-color: {colors["surface"]};
                color: {colors["text_secondary"]};
            }}
            QSplitter::handle {{
                background-color: {colors["border"]};
                width: 2px;
            }}
            QScrollBar:vertical {{
                background: {colors["background"]};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors["surface_bright"]};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

    def get_markdown_preview_css(self) -> str:
        """Generate CSS for Markdown preview with theme colors."""
        colors = self.get_colors()
        return f"""
            <style>
                body {{
                    font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: {colors["text"]};
                    background-color: {colors["surface"]};
                    font-size: 14px;
                    padding: 16px;
                    margin: 0;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: {colors["primary"]};
                    font-weight: 600;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                h1 {{ border-bottom: 1px solid {colors["border"]}; padding-bottom: 10px; }}
                code {{
                    background-color: {colors["primary_dim"]};
                    color: {colors["primary"]};
                    font-family: "JetBrains Mono", Consolas, monospace;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-size: 0.9em;
                }}
                pre {{
                    background-color: {colors["background"]};
                    border: 1px solid {colors["border"]};
                    padding: 15px;
                    border-radius: 8px;
                    overflow-x: auto;
                    margin: 10px 0;
                }}
                pre code {{
                    background-color: transparent;
                    color: {colors["text"]};
                    padding: 0;
                }}
                blockquote {{
                    border-left: 4px solid {colors["primary"]};
                    margin: 0;
                    padding-left: 15px;
                    color: {colors["text_secondary"]};
                    background-color: {colors["primary_dim"]};
                    padding: 10px 15px;
                    border-radius: 4px;
                }}
                a {{ color: {colors["primary"]}; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th {{ 
                    background-color: {colors["background"]}; 
                    color: {colors["primary"]};
                    text-align: left; 
                    padding: 10px;
                    border-bottom: 2px solid {colors["border"]};
                }}
                td {{ 
                    padding: 10px; 
                    border-bottom: 1px solid {colors["border"]}; 
                }}
                tr:hover {{ background-color: {colors["primary_dim"]}; }}
                hr {{ border: none; border-top: 1px solid {colors["border"]}; margin: 20px 0; }}
                ul, ol {{ padding-left: 20px; }}
                img {{ max-width: 100%; border-radius: 4px; }}
            </style>
        """
