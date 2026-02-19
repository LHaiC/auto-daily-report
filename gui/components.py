"""
UI Components for Daily Report Client
This module contains all dialog and widget components
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QProgressDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QFrame,
)
from PySide6.QtGui import QFont, QAction, QKeySequence, QTextCursor
from PySide6.QtCore import Qt, Signal, QThread

from backend import NoteManager
from styles import ThemeManager
from utils import confirm_delete, format_file_size, show_error, show_info
from manage_env import load_env


class MarkdownEditor(QPlainTextEdit):
    """Enhanced Markdown editor with syntax highlighting-like features."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setUndoRedoEnabled(True)

        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        self.setup_styles()

    def setup_styles(self):
        """Setup editor styles."""
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e293b;
                border: none;
                padding: 16px;
                color: #f8fafc;
                font-family: "JetBrains Mono", monospace;
                font-size: 13px;
                line-height: 1.4;
            }
        """)

    def add_shortcut(self, key_sequence: str, callback):
        """Add keyboard shortcut."""
        from PySide6.QtGui import QShortcut

        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.activated.connect(callback)


class WelcomeDialog(QDialog):
    """Welcome dialog for creating or opening files."""

    fileSelected = Signal(Path)
    createNew = Signal(str, str)

    def __init__(self, manager: NoteManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Daily Report Client - Welcome")
        self.resize(900, 650)

        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        title = QLabel("🚀 Daily Report Client")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #38bdf8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Create, manage, and generate your technical reports")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Content area
        content = QHBoxLayout()
        content.setSpacing(24)

        # Left: Create new
        left = QFrame()
        left.setFrameStyle(QFrame.Box)
        left.setStyleSheet("QFrame { border: 1px solid #334155; border-radius: 12px; }")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(16)

        create_title = QLabel("✨ Create New Note")
        create_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #38bdf8;"
        )
        left_layout.addWidget(create_title)

        # Name input
        name_label = QLabel("Note Title:")
        name_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        left_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., LLM Research, Bug Fix Session...")
        left_layout.addWidget(self.name_input)

        # Date input
        date_label = QLabel("Date:")
        date_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        left_layout.addWidget(date_label)

        self.date_input = QLineEdit()
        self.date_input.setText(dt.date.today().isoformat())
        left_layout.addWidget(self.date_input)

        left_layout.addStretch()

        create_btn = QPushButton("📝 Create Note")
        create_btn.clicked.connect(self.on_create_new)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #38bdf8;
                color: #0f172a;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        left_layout.addWidget(create_btn)

        content.addWidget(left, 1)

        # Right: Recent files
        right = QFrame()
        right.setFrameStyle(QFrame.Box)
        right.setStyleSheet(
            "QFrame { border: 1px solid #334155; border-radius: 12px; }"
        )
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(16)

        recent_title = QLabel("📚 Recent Notes")
        recent_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #38bdf8;"
        )
        right_layout.addWidget(recent_title)

        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.on_file_selected)
        self.recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self.show_context_menu)
        right_layout.addWidget(self.recent_list)

        open_btn = QPushButton("📂 Open Selected")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #38bdf8;
                border: 2px solid #38bdf8;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.1);
            }
        """)
        open_btn.clicked.connect(self.on_open_selected)
        right_layout.addWidget(open_btn)

        content.addWidget(right, 1)
        layout.addLayout(content)

        # Bottom actions
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        browse_scratch = QPushButton("📁 Browse All Scratch")
        browse_scratch.clicked.connect(self.browse_scratch)
        bottom.addWidget(browse_scratch)

        browse_reports = QPushButton("📊 Browse Reports")
        browse_reports.clicked.connect(self.browse_reports)
        bottom.addWidget(browse_reports)

        bottom.addStretch()

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        bottom.addWidget(settings_btn)

        layout.addLayout(bottom)

        self.load_recent_files()

    def load_recent_files(self):
        """Load recent files into list."""
        self.recent_list.clear()
        files = self.manager.list_scratch_files()

        for file_info in files[:20]:  # Show last 20
            item = QListWidgetItem()
            item.setData(Qt.UserRole, file_info["path"])

            name = file_info["name"]
            modified = file_info["modified"].strftime("%Y-%m-%d %H:%M")
            size = format_file_size(file_info["size"])

            item.setText(f"{name}\n   📅 {modified}  •  📄 {size}")
            self.recent_list.addItem(item)

    def on_create_new(self):
        """Handle create new button click."""
        name = self.name_input.text().strip()
        date_str = self.date_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing Title", "Please enter a note title.")
            return

        try:
            dt.date.fromisoformat(date_str)
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Date", "Please enter a valid date (YYYY-MM-DD)."
            )
            return

        self.createNew.emit(name, date_str)
        self.accept()

    def on_file_selected(self, item: QListWidgetItem):
        """Handle file selection."""
        path = item.data(Qt.UserRole)
        self.fileSelected.emit(path)
        self.accept()

    def on_open_selected(self):
        """Handle open selected file."""
        selected = self.recent_list.selectedItems()
        if selected:
            self.on_file_selected(selected[0])
        else:
            QMessageBox.information(
                self, "No Selection", "Please select a file from the list."
            )

    def show_context_menu(self, position):
        """Show context menu for file list."""
        item = self.recent_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        open_action = menu.addAction("📂 Open")
        delete_action = menu.addAction("🗑️ Delete")

        action = menu.exec(self.recent_list.mapToGlobal(position))
        if action == open_action:
            self.on_file_selected(item)
        elif action == delete_action:
            path = item.data(Qt.UserRole)
            if confirm_delete(self, path.name):
                path.unlink()
                self.load_recent_files()

    def browse_scratch(self):
        """Browse all scratch files."""
        dialog = FileBrowserDialog(self.manager, "scratch", self)
        dialog.fileSelected.connect(self.fileSelected)
        dialog.exec()

    def browse_reports(self):
        """Browse generated reports."""
        dialog = FileBrowserDialog(self.manager, "reports", self)
        dialog.fileSelected.connect(self.fileSelected)
        dialog.exec()

    def open_settings(self):
        """Open settings dialog."""
        dialog = EnvSettingsDialog(self)
        dialog.exec()


class FileBrowserDialog(QDialog):
    """Dialog for browsing files with preview."""

    fileSelected = Signal(Path)

    def __init__(self, manager: NoteManager, mode: str = "scratch", parent=None):
        super().__init__(parent)
        self.manager = manager
        self.mode = mode
        self.setWindowTitle("Browse Files" if mode == "scratch" else "Browse Reports")
        self.resize(1200, 700)

        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left: File list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)

        # Controls
        controls = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search files...")
        self.search_input.textChanged.connect(self.filter_files)
        controls.addWidget(self.search_input)

        refresh = QPushButton("🔄 Refresh")
        refresh.clicked.connect(self.load_files)
        controls.addWidget(refresh)

        left_layout.addLayout(controls)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3 if self.mode == "scratch" else 6)
        headers = (
            ["Name", "Modified", "Size"]
            if self.mode == "scratch"
            else ["Name", "Title", "Tags", "Date", "Modified", "Size"]
        )
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.on_open)
        left_layout.addWidget(self.table)

        # Buttons
        buttons = QHBoxLayout()

        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.on_delete)
        buttons.addWidget(delete_btn)

        buttons.addStretch()

        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self.on_open)
        open_btn.setDefault(True)
        buttons.addWidget(open_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        left_layout.addLayout(buttons)

        layout.addWidget(left_panel, stretch=2)

        # Right: Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)

        preview_title = QLabel("👁️ Preview")
        preview_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #38bdf8;"
        )
        right_layout.addWidget(preview_title)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                color: #f8fafc;
                font-size: 13px;
            }
        """)
        right_layout.addWidget(self.preview)

        layout.addWidget(right_panel, stretch=1)

        self.load_files()

    def load_files(self):
        """Load files into table."""
        self.files = []

        if self.mode == "scratch":
            for f in self.manager.list_scratch_files():
                self.files.append(
                    {
                        "path": f["path"],
                        "name": f["name"],
                        "modified": f["modified"].strftime("%Y-%m-%d %H:%M"),
                        "size": format_file_size(f["size"]),
                    }
                )
        else:
            for r in self.manager.list_daily_reports():
                self.files.append(
                    {
                        "path": r["path"],
                        "name": r["name"],
                        "title": r.get("title", "N/A"),
                        "tags": ", ".join(r.get("tags", [])),
                        "date": r.get("date", ""),
                        "modified": r["modified"].strftime("%Y-%m-%d %H:%M"),
                        "size": format_file_size(r["size"]),
                    }
                )

        self.update_table()

    def update_table(self):
        """Update table contents."""
        self.table.setRowCount(len(self.files))

        for i, file in enumerate(self.files):
            self.table.setItem(i, 0, QTableWidgetItem(file["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(file["modified"]))
            self.table.setItem(i, 2, QTableWidgetItem(file["size"]))

            if self.mode == "reports":
                self.table.setItem(i, 3, QTableWidgetItem(file.get("title", "")))
                self.table.setItem(i, 4, QTableWidgetItem(file.get("tags", "")))
                self.table.setItem(i, 5, QTableWidgetItem(file.get("date", "")))

    def filter_files(self, text: str):
        """Filter files based on search text."""
        if not text:
            self.update_table()
            return

        filtered = [f for f in self.files if text.lower() in f["name"].lower()]

        self.table.setRowCount(len(filtered))
        for i, file in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(file["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(file["modified"]))
            self.table.setItem(i, 2, QTableWidgetItem(file["size"]))

    def on_open(self):
        """Handle open file."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(
                self, "No Selection", "Please select a file to open."
            )
            return

        row = selected[0].row()
        if row < len(self.files):
            path = self.files[row]["path"]
            self.fileSelected.emit(path)
            self.accept()

    def on_delete(self):
        """Handle delete file."""
        selected = self.table.selectedItems()
        if not selected:
            return

        rows = set(item.row() for item in selected)
        names = [self.files[r]["name"] for r in rows if r < len(self.files)]

        if not confirm_delete(
            self,
            ", ".join(names[:3])
            + ("" if len(names) <= 3 else f" and {len(names) - 3} more"),
            len(names),
        ):
            return

        for row in rows:
            if row < len(self.files):
                path = self.files[row]["path"]
                try:
                    path.unlink()
                    # Remove from list
                    self.files = [f for f in self.files if f["path"] != path]
                except Exception as e:
                    show_error(
                        self, "Delete Error", f"Failed to delete {path.name}: {e}"
                    )

        self.update_table()


class SyncDialog(QDialog):
    """Dialog for Git repository synchronization."""

    def __init__(self, manager: NoteManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("🔄 Sync Repository")
        self.resize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("🚀 Repository Sync")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4ade80;")
        layout.addWidget(title)

        self.progress = QTextEdit()
        self.progress.setReadOnly(True)
        self.progress.setMaximumHeight(300)
        layout.addWidget(self.progress)

        self.sync_btn = QPushButton("🔄 Start Sync")
        self.sync_btn.clicked.connect(self.start_sync)
        layout.addWidget(self.sync_btn)

    def start_sync(self):
        """Start synchronization."""
        self.sync_btn.setEnabled(False)
        self.progress.clear()
        self.log("Starting sync...", "info")

        self.thread = SyncThread(self.manager)
        self.thread.log.connect(self.log)
        self.thread.finished.connect(self.on_sync_complete)
        self.thread.start()

    def log(self, message: str, level: str = "info"):
        """Add log message."""
        import datetime as dt

        timestamp = dt.datetime.now().strftime("%H:%M:%S")

        if level == "info":
            icon = "💡"
        elif level == "success":
            icon = "✅"
        elif level == "error":
            icon = "❌"
        else:
            icon = "ℹ️"

        self.progress.append(f"[{timestamp}] {icon} {message}")

    def on_sync_complete(self, success: bool):
        """Handle sync completion."""
        self.sync_btn.setEnabled(True)
        if success:
            self.log("Sync completed successfully!", "success")
            QMessageBox.information(self, "Success", "Repository synced successfully!")
            self.accept()
        else:
            self.log("Sync failed!", "error")


class SyncThread(QThread):
    """Worker thread for Git synchronization."""

    log = Signal(str, str)
    finished = Signal(bool)

    def __init__(self, manager: NoteManager):
        super().__init__()
        self.manager = manager

    def run(self):
        """Run git synchronization."""
        try:
            self.log.emit("Adding changes to git...", "info")
            self.manager.run_git_command(["add", "."])

            self.log.emit("Committing changes...", "info")
            status = self.manager.run_git_command(["status", "--porcelain"])
            if status:
                self.manager.run_git_command(["commit", "-m", "chore: sync updates"])
                self.log.emit("Changes committed.", "success")

            self.log.emit("Pulling from remote...", "info")
            self.manager.run_git_command(["pull", "--rebase"])

            self.log.emit("Pushing to remote...", "info")
            self.manager.run_git_command(["push"])

            self.log.emit("Sync complete!", "success")
            self.finished.emit(True)
        except Exception as e:
            self.log.emit(f"Sync failed: {str(e)}", "error")
            self.finished.emit(False)


class GenerateReportDialog(QDialog):
    """Dialog for generating a daily report from a scratch note."""

    def __init__(
        self, manager: NoteManager, input_path: Optional[Path] = None, parent=None
    ):
        super().__init__(parent)
        self.manager = manager
        self.input_path = input_path
        self.setWindowTitle("📝 Generate Report")
        self.resize(500, 350)

        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("📝 Generate Daily Report")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4ade80;")
        layout.addWidget(title)

        if self.input_path:
            info = QLabel(f"Converting: <b>{self.input_path.name}</b>")
            info.setWordWrap(True)
            layout.addWidget(info)

        self.force_check = QCheckBox("Force regenerate (ignore hash check)")
        layout.addWidget(self.force_check)

        layout.addStretch()

        buttons = QHBoxLayout()

        self.generate_btn = QPushButton("🚀 Generate")
        self.generate_btn.clicked.connect(self.generate)
        buttons.addWidget(self.generate_btn)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        layout.addLayout(buttons)

        self.progress = QLabel("")
        self.progress.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress)

    def generate(self):
        """Generate report."""
        self.generate_btn.setEnabled(False)
        self.progress.setText("⏳ Generating report...")

        self.thread = GenerateThread(
            self.manager, self.input_path, self.force_check.isChecked()
        )
        self.thread.finished.connect(self.on_complete)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_complete(self, output: str):
        """Handle generation completion."""
        self.progress.setText("✅ Report generated successfully!")
        QMessageBox.information(
            self, "Success", "Report generated!\n\nOutput:\n" + output[:200]
        )
        self.accept()

    def on_error(self, error: str):
        """Handle generation error."""
        self.progress.setText("❌ Generation failed!")
        show_error(self, "Generation Error", error)


class GenerateThread(QThread):
    """Worker thread for report generation."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, manager: NoteManager, input_path: Optional[Path], force: bool):
        super().__init__()
        self.manager = manager
        self.input_path = input_path
        self.force = force

    def run(self):
        """Run report generation."""
        try:
            result = self.manager.generate_report(self.input_path, force=self.force)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class GenerateWeeklyDialog(QDialog):
    """Dialog for generating weekly summary."""

    def __init__(self, manager: NoteManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("📅 Generate Weekly Summary")
        self.resize(400, 300)

        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("📅 Generate Weekly Summary")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ade80;")
        layout.addWidget(title)

        # Year selection
        year_layout = QHBoxLayout()
        year_label = QLabel("Year:")
        year_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        year_layout.addWidget(year_label)

        self.year_combo = QComboBox()
        current_year = dt.date.today().year
        for year in range(current_year - 2, current_year + 1):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentText(str(current_year))
        year_layout.addWidget(self.year_combo)

        layout.addLayout(year_layout)

        # Week selection
        week_layout = QHBoxLayout()
        week_label = QLabel("Week:")
        week_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        week_layout.addWidget(week_label)

        self.week_combo = QComboBox()
        for week in range(1, 54):
            self.week_combo.addItem(f"Week {week:02d}", week)

        current_week = dt.date.today().isocalendar()[1]
        self.week_combo.setCurrentIndex(current_week - 1)
        week_layout.addWidget(self.week_combo)

        layout.addLayout(week_layout)

        layout.addStretch()

        self.generate_btn = QPushButton("🚀 Generate")
        self.generate_btn.clicked.connect(self.generate)
        layout.addWidget(self.generate_btn)

        self.progress = QLabel("")
        self.progress.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress)

    def generate(self):
        """Generate weekly summary."""
        self.generate_btn.setEnabled(False)
        self.progress.setText("⏳ Generating weekly summary...")

        year = self.year_combo.currentData()
        week = self.week_combo.currentData()

        try:
            result = self.manager.generate_weekly_summary(year, week)
            self.progress.setText("✅ Weekly summary generated!")
            QMessageBox.information(
                self, "Success", "Weekly summary generated!\n\n" + result
            )
            self.accept()
        except Exception as e:
            self.progress.setText("❌ Generation failed!")
            show_error(self, "Generation Error", str(e))
            self.generate_btn.setEnabled(True)


class EnvSettingsDialog(QDialog):
    """Dialog for environment variable settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Environment Settings")
        self.resize(700, 500)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️ Environment Variables")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Configure API keys and settings. Values are stored in ~/.env.secrets"
        )
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(subtitle)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 250)
        layout.addWidget(self.table)

        # Buttons
        buttons = QHBoxLayout()

        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_row)
        buttons.addWidget(add_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_row)
        buttons.addWidget(delete_btn)

        buttons.addStretch()

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

    def load_settings(self):
        """Load settings from .env.secrets."""
        envs = load_env()

        # Add defaults if missing
        defaults = {
            "REPORT_API_KEY": "",
            "REPORT_API_URL": "",
            "REPORT_API_MODEL": "",
            "REPORT_API_TIMEOUT": "120",
        }

        for key, val in defaults.items():
            if key not in envs:
                envs[key] = val

        self.table.setRowCount(len(envs))

        for i, (key, value) in enumerate(sorted(envs.items())):
            # Key item (read-only)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            key_item.setBackground(Qt.lightGray)
            self.table.setItem(i, 0, key_item)

            # Value item
            value_item = QTableWidgetItem(str(value))
            # Hide sensitive values
            if any(k in key.lower() for k in ["key", "token", "secret", "password"]):
                value_item.setToolTip("Double-click to edit sensitive value")
            self.table.setItem(i, 1, value_item)

    def add_row(self):
        """Add new row to settings."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        key_item = QTableWidgetItem("NEW_KEY")
        self.table.setItem(row, 0, key_item)

        value_item = QTableWidgetItem("")
        self.table.setItem(row, 1, value_item)

        self.table.editItem(key_item)

    def delete_row(self):
        """Delete selected row."""
        selected = self.table.selectedItems()
        if selected:
            self.table.removeRow(selected[0].row())

    def save_settings(self):
        """Save settings to .env.secrets."""
        settings = {}

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)

            if key_item and val_item:
                key = key_item.text().strip()
                val = val_item.text().strip()

                if key and key != "NEW_KEY":
                    settings[key] = val

        config_file = Path.home() / ".env.secrets"
        config_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")

        show_info(self, "Settings Saved", "Settings saved to ~/.env.secrets")
        self.accept()
